import os
import time
import threading
from datetime import datetime, timezone
from urllib.parse import urlencode
import streamlit as st
from ai_quests import generate_slot_quests, QuestGenerationError
from onboarding import PILLARS
from quest_plan import slot_plan, pillar_statistics, TRACKS, clean_title, EXPERIENCE_FOCUSES


def ai_config():
    try:
        config=st.secrets.get('requesty',{})
    except FileNotFoundError:
        config={}
    return os.environ.get('REQUESTY_API_KEY') or config.get('api_key','')


@st.cache_resource
def generation_guard():
    return {}, threading.Lock()


def fetch_quests(api):
    rows, offset = [], 0
    while True:
        query=urlencode({'select':'*','order':'created_at.asc,id.asc','limit':'500','offset':str(offset)})
        batch,error=api('GET','/rest/v1/ai_quests?'+query,access_token=st.session_state.access_token)
        if error:
            return [],error
        rows.extend(batch or [])
        if len(batch or [])<500:
            return rows,None
        offset+=500


def starting_level(category):
    answers=st.session_state.user.get('user_metadata',{}).get('lifequest_onboarding',{})
    value=answers.get('levels',{}).get(category,1)
    return max(1,min(5,int(value)))


def build_batch(category, slots, rows, pending_id=None, allow_ai=True):
    user_id=st.session_state.user['id']
    pending_key=f'quest_batch_{user_id}_{category}_{slots}_{pending_id}'
    if pending_key in st.session_state:
        return st.session_state[pending_key],pending_key
    history=[q for q in rows if q['category']==category]
    plans=[slot_plan(category,slot,starting_level(category),history) for slot in slots]
    key=ai_config()
    attempts,lock=generation_guard()
    identity=(user_id,category,pending_id or tuple(slots))
    with lock:
        now=time.monotonic()
        can_call=now-attempts.get(identity,-1000)>=3
        attempts[identity]=now
    if key and can_call and allow_ai:
        try:
            language = st.session_state.get("language", "en")
            plans = generate_slot_quests(key, plans, history, language)
        except QuestGenerationError:
            st.session_state.quest_library_used=True
    elif allow_ai:
        st.session_state.quest_library_used=True
    st.session_state[pending_key]=plans
    return plans,pending_key


def save_batch(api, batch, pending_key, finished_id=None, rating='just_right', skip=False):
    stored=[{k:v for k,v in q.items() if k!='metric'} for q in batch]
    points,error=api('POST','/rest/v1/rpc/save_quest_slots',
        {'quest_rows':stored,'finished_id':finished_id,'rating':rating,'skip':skip},st.session_state.access_token)
    if error:
        return 'We couldn’t save the quest update. Please retry. Your progress and previous quests have been kept.'
    if type(points) is not int:
        return 'The quest update could not be verified. Please refresh before trying again.'
    st.session_state.profile['points']=points
    st.session_state.pop(pending_key,None)
    return None


def ensure_five_quests(api, rows, categories):
    for category in categories:
        used={q.get('slot') for q in rows if q['category']==category and q['status']=='active'}
        missing=[n for n in range(1,6) if n not in used]
        if missing:
            batch,key=build_batch(category,missing,rows,allow_ai=False)
            error=save_batch(api,batch,key)
            if error:
                return rows,error
            rows,error=fetch_quests(api)
            if error:
                return [],'Your quests were saved, but could not be reloaded. Please refresh.'
    return rows,None


def prepare_initial_quests(api):
    rows,error=fetch_quests(api)
    if error:
        return 'Your profile is saved. We couldn’t load quest storage yet.'
    _,error=ensure_five_quests(api,rows,[c for c in st.session_state.profile.get('selected_categories',[]) if c in PILLARS])
    return error


def replace_quest(api, quest, rows, rating='just_right', skip=False):
    # Plan against the proposed completion; save completion + replacement in one transaction.
    now=datetime.now(timezone.utc).isoformat()
    proposed=[{**q,'status':'skipped' if skip else 'completed','feedback':rating,'completed_at':now}
              if q['id']==quest['id'] else q for q in rows]
    batch,key=build_batch(quest['category'],[quest['slot']],proposed,quest['id'])
    return save_batch(api,batch,key,quest['id'],rating,skip)


def render_quest_styles():
    st.markdown("""<style>
    @keyframes quest-enter {from {opacity:0;transform:translateY(9px);} to {opacity:1;transform:translateY(0);}}
    div[class*="st-key-quest_row_"] {border:1px solid #dbe8df;border-radius:15px;
      padding:12px 16px;background:#fff;animation:quest-enter .38s ease-out both;
      transition:opacity .22s ease,transform .22s ease,background .22s ease;}
    div[class*="st-key-quest_row_"]:hover {border-color:#83af95;background:#f6fbf7;}
    div[class*="st-key-quest_row_"]:has(input:checked:not(:disabled)) {opacity:.35;transform:translateY(-5px);background:#e5f5e9;pointer-events:none;}
    div[class*="st-key-quest_row_"] [data-testid="stCheckbox"] {margin:0;min-width:0;}
    div[class*="st-key-quest_row_"] label {width:100%;min-width:0;cursor:pointer;}
    div[class*="st-key-quest_row_"] label>div {min-width:0;}
    div[class*="st-key-quest_row_"] [data-testid="stMarkdownContainer"] {min-width:0;}
    div[class*="st-key-quest_row_"] [data-testid="stMarkdownContainer"] p {white-space:nowrap;
      overflow:hidden;text-overflow:ellipsis;font-weight:550;line-height:1.6;}
    @media(prefers-reduced-motion:reduce) {
      div[class*="st-key-quest_row_"] {animation:none;transition:none;transform:none!important;}
    }
    </style>""",unsafe_allow_html=True)


def queue_completion(quest_id):
    queue=list(st.session_state.get('quest_completion_queue',[]))
    if st.session_state.get('quest_check_'+quest_id):
        if quest_id not in queue:
            queue.append(quest_id)
    else:
        queue=[q for q in queue if q!=quest_id]
    st.session_state.quest_completion_queue=queue


def process_completions(api, rows):
    queue=list(st.session_state.get('quest_completion_queue',[]))
    def remove_request(quest_id):
        st.session_state.quest_completion_queue=[q for q in st.session_state.get('quest_completion_queue',[]) if q!=quest_id]
    for quest_id in queue:
        quest=next((q for q in rows if q['id']==quest_id and q['status']=='active'),None)
        if quest is None:
            remove_request(quest_id)
            continue
        before=st.session_state.profile.get('points',0)
        with st.spinner('Unlocking your next quest…'):
            error=replace_quest(api,quest,rows)
        if error:
            # Reset before this run renders the checkbox, so the user can retry.
            st.session_state['quest_check_'+quest_id]=False
            remove_request(quest_id)
            st.error(error)
            continue
        remove_request(quest_id)
        gained=max(0,st.session_state.profile.get('points',before)-before)
        st.session_state.quest_toast=f'+{gained} XP · New quest unlocked!' if gained else 'Quest saved · Your next one is ready!'
        refreshed,error=fetch_quests(api)
        if error:
            st.warning('Your completion was saved. Refresh to see the new quest.')
            return None
        rows=refreshed
    return rows

def render_quest_cards(api, rows, category):
    language = st.session_state.get("language", "en")
    active=sorted([q for q in rows if q['category']==category and q['status']=='active'],key=lambda q:q['slot'])
    for quest in active:
        title=clean_title(quest['title'],quest.get('target'))
        if quest.get('source')=='curated' and quest.get('focus') in EXPERIENCE_FOCUSES:
            title=slot_plan(category,quest['slot'],starting_level(category),rows)['title']
        with st.container(key='quest_row_'+quest['id']):
            st.checkbox(title,key='quest_check_'+quest['id'],on_change=queue_completion,args=(quest['id'],))


def load_board(api, categories):
    rows,error=fetch_quests(api)
    if error:
        st.error('Your quests could not be loaded. Please refresh to reconnect.')
        st.error(f"Debug: {error}")
        return None
    rows=process_completions(api,rows)
    if rows is None:
        return None
    missing=any(sum(q['category']==c and q['status']=='active' for q in rows)<5 for c in categories)
    if missing:
        with st.spinner('Preparing five practical quests for each of your pillars…'):
            rows,error=ensure_five_quests(api,rows,categories)
        if error:
            st.error(error)
            if st.button('Retry loading quests'):
                st.rerun()
            return None
    if st.session_state.get('quest_toast'):
        st.toast(st.session_state.pop('quest_toast'),icon='🌱')
    if st.session_state.pop('quest_library_used',False):
        st.caption('Some quests come from our practical habit library while AI is unavailable.')
    st.session_state.ai_completed_count=sum(q['status']=='completed' for q in rows)
    return rows


def render_home(api):
    render_quest_styles()
    name=st.session_state.profile.get('display_name','there')
    st.caption({
        "en": "LIFE QUEST · A LITTLE BETTER, EVERY DAY",
        "pt": "LIFE QUEST · UM POUCO MELHOR A CADA DIA",
        "fr": "LIFE QUEST · UN PEU MIEUX CHAQUE JOUR",
        "de": "LIFE QUEST · JEDEN TAG EIN BISSCHEN BESSER",
    }.get(st.session_state.get("language", "en")))
    language = st.session_state.get("language", "en")
    greeting = {
        "en": "Hi",
        "pt": "Olá",
        "fr": "Salut",
        "de": "Hallo",
    }.get(language, "Hi")
    st.title(f'{greeting}, {name} 👋')
    st.write({
        "en": "Five small opportunities in each of your pillars. Pick what fits today — good luck!",
        "pt": "Cinco pequenas oportunidades em cada uma das tuas áreas. Escolhe o que combina contigo hoje — boa sorte!",
        "fr": "Cinq petites opportunités dans chacun de tes domaines. Choisis ce qui te convient aujourd'hui — bonne chance !",
        "de": "Fünf kleine Möglichkeiten in jedem deiner Lebensbereiche. Wähle, was heute zu dir passt — viel Erfolg!",
    }.get(language, "Five small opportunities in each of your pillars. Pick what fits today — good luck!"))
    categories=[c for c in st.session_state.profile.get('selected_categories',[]) if c in PILLARS]
    rows=load_board(api,categories)
    if rows is None:
        return
    st.caption(f'🌱 {st.session_state.profile.get("points",0)} XP')
    for category in categories:
            
        category_names = {
            "Fitness": {"pt": "Exercício", "fr": "Sport", "de": "Fitness"},
            "Health": {"pt": "Saúde", "fr": "Santé", "de": "Gesundheit"},
            "Languages": {"pt": "Idiomas", "fr": "Langues", "de": "Sprachen"},
            "Personal Growth": {"pt": "Desenvolvimento Pessoal", "fr": "Développement personnel", "de": "Persönliche Entwicklung"},
            "Social": {"pt": "Vida Social", "fr": "Vie sociale", "de": "Soziales"},
            "Adventure": {"pt": "Aventura", "fr": "Aventure", "de": "Abenteuer"},
            "Finance": {"pt": "Finanças", "fr": "Finances", "de": "Finanzen"},
        }
        translated_category = category_names.get(category, {}).get(language, category)
        st.subheader(f'{PILLARS[category][0]} {translated_category}')
        st.caption({
            "en": "5 independent quests · a fresh one appears whenever you finish",
            "pt": "5 missões independentes · aparece uma nova sempre que concluis uma",
            "fr": "5 quêtes indépendantes · une nouvelle apparaît à chaque quête terminée",
            "de": "5 unabhängige Quests · nach jedem Abschluss erscheint eine neue",
        }.get(language, "5 independent quests · a fresh one appears whenever you finish"))
        render_quest_cards(api,rows,category)


def render_pillar(api, category):
    render_quest_styles()
    st.caption({
    "en": "YOUR PILLAR · YOUR PROGRESS",
    "pt": "A TUA ÁREA · O TEU PROGRESSO",
    "fr": "TON DOMAINE · TES PROGRÈS",
    "de": "DEIN BEREICH · DEIN FORTSCHRITT",
}.get(st.session_state.get("language", "en"), "YOUR PILLAR · YOUR PROGRESS"))
    st.title(f'{PILLARS[category][0]} ' + {
    "en": category,
    "pt": {"Finance": "Finanças", "Fitness": "Exercício", "Health": "Saúde", "Languages": "Idiomas", "Personal Growth": "Desenvolvimento Pessoal", "Social": "Vida Social", "Adventure": "Aventura"}.get(category, category),
    "fr": {"Finance": "Finances", "Fitness": "Sport", "Health": "Santé", "Languages": "Langues", "Personal Growth": "Développement personnel", "Social": "Vie sociale", "Adventure": "Aventure"}.get(category, category),
    "de": {"Finance": "Finanzen", "Fitness": "Fitness", "Health": "Gesundheit", "Languages": "Sprachen", "Personal Growth": "Persönliche Entwicklung", "Social": "Soziales", "Adventure": "Abenteuer"}.get(category, category),
}.get(st.session_state.get("language", "en"), category))
    rows=load_board(api,[category])
    if rows is None:
        return
    own=[q for q in rows if q['category']==category]
    # Include existing shared-quest completions in the same pillar's history and trends.
    lookup={q['id']:q for q in st.session_state.get('challenges',[])}
    legacy=[]
    for q in st.session_state.get('legacy_completions',[]):
        challenge=lookup.get(q['challenge_id'],{})
        if challenge.get('category')==category:
            legacy.append({**challenge,'status':'completed','completed_at':q.get('completed_at'),'difficulty':1,'legacy':True})
    stats=pillar_statistics(own+legacy)
    stats['xp']=sum(10+5*q['difficulty'] for q in own if q['status']=='completed')+sum(q.get('points',0) for q in legacy)
    a,b,c=st.columns(3)
    a.metric({"en": "Quests completed", "pt": "Missões concluídas", "fr": "Quêtes terminées", "de": "Abgeschlossene Quests"}.get(st.session_state.get("language", "en"), "Quests completed"), stats['completed'])
    b.metric({"en": "Pillar XP", "pt": "XP da área", "fr": "XP du domaine", "de": "Bereichs-XP"}.get(st.session_state.get("language", "en"), "Pillar XP"), stats['xp'])
    c.metric(
    {"en": "This week", "pt": "Esta semana", "fr": "Cette semaine", "de": "Diese Woche"}.get(st.session_state.get("language", "en"), "This week"),
    stats["week"],
    delta=f'{stats["week_delta"]:+d} ' + {
        "en": "vs previous 7 days",
        "pt": "em relação aos 7 dias anteriores",
        "fr": "par rapport aux 7 jours précédents",
        "de": "im Vergleich zu den letzten 7 Tagen",
    }.get(st.session_state.get("language", "en"), "vs previous 7 days")
)
    st.caption(f'🔥 {stats["streak"]} ' + {
    "en": "day streak in this pillar",
    "pt": "dias consecutivos nesta área",
    "fr": "jours consécutifs dans ce domaine",
    "de": "Tage in Folge in diesem Bereich",
}.get(st.session_state.get("language", "en"), "day streak in this pillar"))
    st.subheader({
    "en": "Your activity",
    "pt": "A tua atividade",
    "fr": "Ton activité",
    "de": "Deine Aktivität",
}.get(st.session_state.get("language", "en"), "Your activity"))
    chart_labels = {
        "en": ("Date", "Quests"),
        "pt": ("Data", "Missões"),
        "fr": ("Date", "Quêtes"),
        "de": ("Datum", "Quests"),
    }
    date_label, quests_label = chart_labels.get(
    st.session_state.get("language", "en"),
    chart_labels["en"]
    )

    chart_data = stats["activity"].rename(
    columns={"Date": date_label, "Quests": quests_label}
    )

    st.bar_chart(chart_data, x=date_label, y=quests_label, color="#245C43")
    st.subheader({
    "en": "Where you can grow next",
    "pt": "Onde podes evoluir a seguir",
    "fr": "Tes prochaines pistes de progression",
    "de": "Wo du dich als Nächstes weiterentwickeln kannst",
}.get(st.session_state.get("language", "en"), "Where you can grow next"))
    for slot in range(1,6):
        plan=slot_plan(category,slot,starting_level(category),own)
        completed=[q for q in own if q.get('slot')==slot and q['status']=='completed']
        with st.expander(TRACKS[category][slot-1][0].replace('_',' ').title()):
            step_label = {
                "en": "Your current step",
                "pt": "O teu passo atual",
                "fr": "Ton étape actuelle",
                "de": "Dein aktueller Schritt",
                    }.get(st.session_state.get("language", "en"), "Your current step")

            st.write(f'**{step_label}:** {plan["title"]}')
            habit_message = {
    "en": f"{len(completed)} completed in this habit track. Each completion unlocks the next step.",
    "pt": f"{len(completed)} missões concluídas neste hábito. Cada conclusão desbloqueia o próximo passo.",
    "fr": f"{len(completed)} quêtes terminées dans cette habitude. Chaque réussite débloque l'étape suivante.",
    "de": f"{len(completed)} Quests in diesem Gewohnheitsbereich abgeschlossen. Jeder Abschluss schaltet den nächsten Schritt frei.",
}.get(st.session_state.get("language", "en"))

            st.caption(habit_message)
            if plan['metric'] and completed and completed[-1].get('target'):
                target_labels = {
    "en": ("Latest completed target", "current target"),
    "pt": ("Último objetivo concluído", "objetivo atual"),
    "fr": ("Dernier objectif atteint", "objectif actuel"),
    "de": ("Letztes erreichtes Ziel", "aktuelles Ziel"),
}

                previous_label, current_label = target_labels.get(
    st.session_state.get("language", "en"),
    target_labels["en"]
)

                st.write(f'{previous_label}: **{completed[-1]["target"]:,}** → {current_label}: **{plan["target"]:,}**')
    st.subheader({
    "en": "Completed quests",
    "pt": "Missões concluídas",
    "fr": "Quêtes terminées",
    "de": "Abgeschlossene Quests",
}.get(st.session_state.get("language", "en"), "Completed quests"))
    finished=sorted([q for q in own+legacy if q['status']=='completed'],key=lambda q:q.get('completed_at') or '',reverse=True)
    if finished:
        table_labels = {
    "en": ("Quest", "Completed"),
    "pt": ("Missão", "Concluída"),
    "fr": ("Quête", "Terminée"),
    "de": ("Quest", "Abgeschlossen"),
}

        quest_label, completed_label = table_labels.get(
    st.session_state.get("language", "en"),
    table_labels["en"]
)

        st.dataframe([
    {
        quest_label: q["title"],
        completed_label: q["completed_at"][:10] if q.get("completed_at") else "",
        "XP": q.get("points", 0) if q.get("legacy") else 10 + 5 * q["difficulty"]
    }
    for q in finished
        ], hide_index=True, width="stretch")
    else:
        st.info({
    "en": "Your first completed quest will appear here. Small starts count.",
    "pt": "A tua primeira missão concluída aparecerá aqui. Cada pequeno passo conta.",
    "fr": "Ta première quête terminée apparaîtra ici. Chaque petit pas compte.",
    "de": "Deine erste abgeschlossene Quest erscheint hier. Jeder kleine Schritt zählt.",
}.get(st.session_state.get("language", "en"), "Your first completed quest will appear here. Small starts count."))
    with st.expander({
    "en": "Your five current quests",
    "pt": "As tuas cinco missões atuais",
    "fr": "Tes cinq quêtes actuelles",
    "de": "Deine fünf aktuellen Quests",
}.get(st.session_state.get("language", "en"), "Your five current quests")):
        render_quest_cards(api,rows,category)
