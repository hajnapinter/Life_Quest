import html
import os
import time
import threading
from datetime import datetime, timezone
from urllib.parse import urlencode
import streamlit as st
from ai_quests import generate_slot_quests, QuestGenerationError
from onboarding import PILLARS
from quest_plan import slot_plan, pillar_statistics, TRACKS, clean_title, EXPERIENCE_FOCUSES, progress_hint, weekly_recap, completed_csv
from design import greeting, hero, pillar_header, heatmap, pillar_bars
from pro import is_pro
from account import photo as account_photo, ring as account_ring


def ai_config():
    try:
        config=st.secrets.get('requesty',{})
    except FileNotFoundError:
        config={}
    return os.environ.get('REQUESTY_API_KEY') or config.get('api_key','')


@st.cache_resource
def generation_guard():
    return {}, threading.Lock()


def _tx(en, pt, fr, de):
    return {"en": en, "pt": pt, "fr": fr, "de": de}.get(st.session_state.get("language", "en"), en)


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


def quests_shown(category):
    """How many of the five ready quests to show for a pillar (onboarding/Settings); all five by default."""
    answers=st.session_state.user.get('user_metadata',{}).get('lifequest_onboarding',{})
    try:
        return max(1,min(5,int((answers.get('quests_shown') or {}).get(category,5))))
    except (TypeError,ValueError,AttributeError):
        return 5


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
        return _tx('We couldn’t save the quest update. Please retry. Your progress and previous quests have been kept.','Não foi possível guardar a atualização. Tenta novamente. O teu progresso e as missões anteriores foram mantidos.','Impossible d’enregistrer la mise à jour. Réessaie. Tes progrès et tes quêtes précédentes sont conservés.','Die Aktualisierung konnte nicht gespeichert werden. Bitte versuche es erneut. Dein Fortschritt und deine bisherigen Quests bleiben erhalten.')
    if type(points) is not int:
        return _tx('The quest update could not be verified. Please refresh before trying again.','Não foi possível confirmar a atualização. Atualiza a página antes de tentar outra vez.','La mise à jour n’a pas pu être vérifiée. Actualise la page avant de réessayer.','Die Aktualisierung konnte nicht bestätigt werden. Bitte lade die Seite neu und versuche es dann erneut.')
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
        return _tx('Your profile is saved. We couldn’t load quest storage yet.','O teu perfil foi guardado. Ainda não foi possível carregar as missões.','Ton profil est enregistré. Impossible de charger les quêtes pour le moment.','Dein Profil ist gespeichert. Die Quests konnten noch nicht geladen werden.')
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

    """Kept for older callers; styles now come from design.apply_styles()."""
    return None



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
        with st.spinner(_tx('Unlocking your next quest…','A desbloquear a tua próxima missão…','Déblocage de ta prochaine quête…','Deine nächste Quest wird freigeschaltet…')):
            error=replace_quest(api,quest,rows)
        if error:
            # Reset before this run renders the checkbox, so the user can retry.
            st.session_state['quest_check_'+quest_id]=False
            remove_request(quest_id)
            st.error(error)
            continue
        remove_request(quest_id)
        gained=max(0,st.session_state.profile.get('points',before)-before)
        st.session_state.quest_toast=(f'+{gained} XP · '+_tx('New quest unlocked!','Nova missão desbloqueada!','Nouvelle quête débloquée !','Neue Quest freigeschaltet!')) if gained else _tx('Quest saved · Your next one is ready!','Missão guardada · A próxima está pronta!','Quête enregistrée · La suivante est prête !','Quest gespeichert · Die nächste ist bereit!')
        refreshed,error=fetch_quests(api)
        if error:
            st.warning(_tx('Your completion was saved. Refresh to see the new quest.','A tua conclusão foi guardada. Atualiza para ver a nova missão.','Ta quête terminée est enregistrée. Actualise pour voir la nouvelle.','Dein Abschluss wurde gespeichert. Lade neu, um die neue Quest zu sehen.'))
            return None
        rows=refreshed
    return rows

def format_number(n):
    """4,000 / 4 000 / 4.000 depending on the language."""
    text=f'{int(n):,}'
    return {'pt':text.replace(',',' '),'fr':text.replace(',',' '),'de':text.replace(',','.')}.get(
        st.session_state.get('language','en'),text)


def trend_html(direction, previous):
    """Small line under a quest showing that its target adapted since last time."""
    n=format_number(previous)
    text=(_tx(f'↑ up from {n} last time',f'↑ mais do que os {n} da última vez',f'↑ plus que {n} la dernière fois',f'↑ mehr als {n} beim letzten Mal')
          if direction=='up' else
          _tx(f'↓ eased from {n} last time',f'↓ mais leve do que os {n} da última vez',f'↓ allégé par rapport à {n} la dernière fois',f'↓ leichter als {n} beim letzten Mal'))
    return f'<span class="lq-trend {direction}">{html.escape(text)}</span>'


def render_quest_cards(api, rows, category, limit=5):
    language = st.session_state.get("language", "en")
    # Five quests stay ready per pillar; only the first `limit` (by slot) are shown.
    active=sorted([q for q in rows if q['category']==category and q['status']=='active'],key=lambda q:q['slot'])[:limit]
    for quest in active:
        title=clean_title(quest['title'],quest.get('target'))
        if quest.get('source')=='curated' and quest.get('focus') in EXPERIENCE_FOCUSES:
            title=slot_plan(category,quest['slot'],starting_level(category),rows)['title']
        with st.container(key='quest_row_'+quest['id']):
            st.checkbox(title,key='quest_check_'+quest['id'],on_change=queue_completion,args=(quest['id'],))
            hint=progress_hint(quest,rows)
            if hint:
                st.markdown(trend_html(*hint),unsafe_allow_html=True)


def load_board(api, categories):
    rows,error=fetch_quests(api)
    if error:

        st.error(_tx('Your quests could not be loaded. Please refresh to reconnect.','Não foi possível carregar as tuas missões. Atualiza a página para voltar a ligar.','Impossible de charger tes quêtes. Actualise la page pour te reconnecter.','Deine Quests konnten nicht geladen werden. Lade die Seite neu, um dich erneut zu verbinden.'))

        return None
    rows=process_completions(api,rows)
    if rows is None:
        return None
    missing=any(sum(q['category']==c and q['status']=='active' for q in rows)<5 for c in categories)
    if missing:
        with st.spinner(_tx('Preparing five practical quests for each of your pillars…','A preparar cinco missões práticas para cada uma das tuas áreas…','Préparation de cinq quêtes concrètes pour chacun de tes domaines…','Fünf praktische Quests für jeden deiner Bereiche werden vorbereitet…')):
            rows,error=ensure_five_quests(api,rows,categories)
        if error:
            st.error(error)
            if st.button(_tx('Retry loading quests','Tentar carregar novamente','Réessayer de charger les quêtes','Quests erneut laden')):
                st.rerun()
            return None
    if st.session_state.get('quest_toast'):
        st.toast(st.session_state.pop('quest_toast'),icon='🌱')
    if st.session_state.pop('quest_library_used',False):
        st.caption(_tx('Some quests come from our practical habit library while AI is unavailable.','Algumas missões vêm da nossa biblioteca de hábitos enquanto a IA não está disponível.','Certaines quêtes viennent de notre bibliothèque d’habitudes tant que l’IA est indisponible.','Einige Quests stammen aus unserer Gewohnheitsbibliothek, solange die KI nicht verfügbar ist.'))
    st.session_state.ai_completed_count=sum(q['status']=='completed' for q in rows)
    return rows


CATEGORY_NAMES = {
    "Fitness": {"pt": "Exercício", "fr": "Sport", "de": "Fitness"},
    "Health": {"pt": "Saúde", "fr": "Santé", "de": "Gesundheit"},
    "Languages": {"pt": "Idiomas", "fr": "Langues", "de": "Sprachen"},
    "Personal Growth": {"pt": "Desenvolvimento Pessoal", "fr": "Développement personnel", "de": "Persönliche Entwicklung"},
    "Social": {"pt": "Vida Social", "fr": "Vie sociale", "de": "Soziales"},
    "Adventure": {"pt": "Aventura", "fr": "Aventure", "de": "Abenteuer"},
    "Finance": {"pt": "Finanças", "fr": "Finances", "de": "Finanzen"},
}


def category_name(category):
    return CATEGORY_NAMES.get(category, {}).get(st.session_state.get("language", "en"), category)


def completed_today(rows):
    today=datetime.now(timezone.utc).date().isoformat()
    return sum(1 for q in rows if q['status']=='completed' and (q.get('completed_at') or '').startswith(today))


def render_home(api):
    language = st.session_state.get("language", "en")
    name=st.session_state.profile.get('display_name','there')
    hello = {"en": "Hello,", "pt": "Olá,", "fr": "Salut,", "de": "Hallo,"}.get(language, "Hello,")
    greeting(hello, name, st.session_state.profile.get("points",0), pro=is_pro(), photo=account_photo(), ring=account_ring())
    categories=[c for c in st.session_state.profile.get('selected_categories',[]) if c in PILLARS]
    rows=load_board(api,categories)
    if rows is None:
        return
    done=completed_today(rows)
    if done:
        title={"en": f"{done} done today. Keep going!", "pt": f"{done} feitas hoje. Continua!",
               "fr": f"{done} faites aujourd'hui. Continue !", "de": f"Heute {done} geschafft. Weiter so!"}[language]
    else:
        title={"en": "One small step today", "pt": "Um pequeno passo hoje",
               "fr": "Un petit pas aujourd'hui", "de": "Heute ein kleiner Schritt"}[language]
    hero(
        {"en": "Today's focus", "pt": "Foco de hoje", "fr": "Objectif du jour", "de": "Fokus für heute"}[language],
        title,
        {"en": "Pick what fits today. A fresh quest appears whenever you finish one.",
         "pt": "Escolhe o que combina contigo hoje. Aparece uma nova missão sempre que concluis uma.",
         "fr": "Choisis ce qui te convient aujourd'hui. Une nouvelle quête apparaît à chaque quête terminée.",
         "de": "Wähle, was heute passt. Nach jedem Abschluss erscheint eine neue Quest."}[language],
    )
    def caption(n):
        return {"en": f"{n} quest{'s' if n != 1 else ''} · tick one when it's done",
                "pt": f"{n} miss{'ões' if n != 1 else 'ão'} · marca quando concluíres",
                "fr": f"{n} quête{'s' if n != 1 else ''} · coche quand c'est fait",
                "de": f"{n} Quest{'s' if n != 1 else ''} · abhaken, wenn erledigt"}[language]
    # Two pillars per row on desktop; Streamlit stacks the columns on phones.
    for start in range(0, len(categories), 2):
        for column, category in zip(st.columns(2, gap="large"), categories[start:start+2]):
            with column:
                shown=quests_shown(category)
                pillar_header(category, PILLARS[category][0], category_name(category), caption(shown))
                render_quest_cards(api,rows,category,limit=shown)


def render_pillar(api, category):
    language = st.session_state.get("language", "en")
    st.markdown('<div class="lq-eyebrow">'+{"en": "Your pillar", "pt": "A tua área", "fr": "Ton domaine", "de": "Dein Bereich"}.get(language, "Your pillar")+'</div>', unsafe_allow_html=True)
    st.title(f'{PILLARS[category][0]} {category_name(category)}')
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
    left, right = st.columns([3, 2], gap="large")
    with left:
            a,b,c=st.container(key='stat_row_pillar').columns(3)
            a.metric({"en": "Quests completed", "pt": "Missões concluídas", "fr": "Quêtes terminées", "de": "Abgeschlossene Quests"}.get(st.session_state.get("language", "en"), "Quests completed"), stats['completed'])
            b.metric({"en": "Pillar XP", "pt": "XP da área", "fr": "XP du domaine", "de": "Bereichs-XP"}.get(st.session_state.get("language", "en"), "Pillar XP"), stats['xp'])
            c.metric(
            {"en": "This week", "pt": "Esta semana", "fr": "Cette semaine", "de": "Diese Woche"}.get(st.session_state.get("language", "en"), "This week"),
            stats["week"],
            delta=f'{stats["week_delta"]:+d} ' + {
                "en": "vs last week",
                "pt": "vs semana passada",
                "fr": "vs semaine dernière",
                "de": "vs letzte Woche",
            }.get(st.session_state.get("language", "en"), "vs last week")
        )
            st.caption(f'🔥 {stats["streak"]} ' + {
            "en": "day streak in this pillar",
            "pt": "dias consecutivos nesta área",
            "fr": "jours consécutifs dans ce domaine",
            "de": "Tage in Folge in diesem Bereich",
        }.get(st.session_state.get("language", "en"), "day streak in this pillar"))
            heatmap(
                category, stats["activity"],
                {"en": "Last 14 days", "pt": "Últimos 14 dias", "fr": "14 derniers jours", "de": "Letzte 14 Tage"}.get(language, "Last 14 days"),
                less={"en": "Less", "pt": "Menos", "fr": "Moins", "de": "Weniger"}.get(language, "Less"),
                more={"en": "More", "pt": "Mais", "fr": "Plus", "de": "Mehr"}.get(language, "More"),
                weekdays={"en": ("M","T","W","T","F","S","S"), "pt": ("S","T","Q","Q","S","S","D"),
                          "fr": ("L","M","M","J","V","S","D"), "de": ("M","D","M","D","F","S","S")}.get(language, ("M","T","W","T","F","S","S")),
            )
    with right:
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
    "en": "Your current quests",
    "pt": "As tuas missões atuais",
    "fr": "Tes quêtes actuelles",
    "de": "Deine aktuellen Quests",
}.get(st.session_state.get("language", "en"), "Your current quests")):
        render_quest_cards(api,rows,category,limit=quests_shown(category))


WEEKDAYS={'en':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
          'pt':['segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado','domingo'],
          'fr':['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'],
          'de':['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']}


def recap_rows(rows):
    """Completed pillar quests plus completed shared challenges, in one list."""
    lookup={q['id']:q for q in st.session_state.get('challenges',[])}
    legacy=[]
    for q in st.session_state.get('legacy_completions',[]):
        challenge=lookup.get(q.get('challenge_id'),{})
        if challenge:
            legacy.append({'category':challenge.get('category'),'title':challenge.get('title',''),'status':'completed',
                           'completed_at':q.get('completed_at'),'points':challenge.get('points',0)})
    return rows+legacy


def render_recap(api):
    """Weekly recap with a per-pillar breakdown and a CSV export of every completed quest."""
    language=st.session_state.get('language','en')
    st.markdown('<div class="lq-eyebrow">'+_tx('Weekly recap','Resumo semanal','Bilan de la semaine','Wochenrückblick')+'</div>',unsafe_allow_html=True)
    st.title(_tx('Your week','A tua semana','Ta semaine','Deine Woche'))
    rows,error=fetch_quests(api)
    if error:
        st.error(_tx('Your quests could not be loaded. Please refresh to reconnect.','Não foi possível carregar as tuas missões. Atualiza a página para voltar a ligar.',
                     'Impossible de charger tes quêtes. Actualise la page pour te reconnecter.','Deine Quests konnten nicht geladen werden. Lade die Seite neu, um dich erneut zu verbinden.'))
        return
    everything=recap_rows(rows)
    recap=weekly_recap(everything)
    st.caption(_tx('Since Monday','Desde segunda-feira','Depuis lundi','Seit Montag')+f' · {recap["week_start"].isoformat()}')
    a,b,c=st.container(key='stat_row_recap').columns(3)
    a.metric(_tx('Quests completed','Missões concluídas','Quêtes terminées','Abgeschlossene Quests'),recap['completed'],
             delta=f'{recap["delta"]:+d} '+_tx('vs last week','vs semana passada','vs semaine dernière','vs letzte Woche'))
    b.metric(_tx('XP earned','XP ganho','XP gagnés','Verdiente XP'),recap['xp'])
    c.metric(_tx('Active days','Dias ativos','Jours actifs','Aktive Tage'),f'{recap["active_days"]}/7')
    if recap['completed']:
        st.subheader(_tx('By pillar','Por área','Par domaine','Nach Bereich'))
        pillar_bars([(cat,f'{PILLARS.get(cat,("•",))[0]} {category_name(cat)}',n) for cat,n in recap['per_pillar'].items()])
        day,count=recap['best_day']
        st.caption('🌟 '+_tx('Best day','Melhor dia','Meilleur jour','Bester Tag')+f': {WEEKDAYS.get(language,WEEKDAYS["en"])[day.weekday()]} · {count} '
                   +_tx('quests','missões','quêtes','Quests'))
    else:
        st.info(_tx('No quests completed this week yet. Your first one will show up here.',
                    'Ainda não concluíste missões esta semana. A primeira vai aparecer aqui.',
                    'Aucune quête terminée cette semaine pour l’instant. La première apparaîtra ici.',
                    'Diese Woche noch keine Quest abgeschlossen. Deine erste erscheint hier.'))
    with st.container(key='card_export'):
        st.subheader(_tx('Export your history','Exportar o teu histórico','Exporter ton historique','Verlauf exportieren'))
        total=sum(1 for q in everything if q.get('status')=='completed')
        st.caption(_tx(f'All {total} completed quests as a CSV file. Opens in Excel, Numbers or Google Sheets.',
                       f'As {total} missões concluídas num ficheiro CSV. Abre no Excel, Numbers ou Google Sheets.',
                       f'Tes {total} quêtes terminées dans un fichier CSV. S’ouvre avec Excel, Numbers ou Google Sheets.',
                       f'Alle {total} abgeschlossenen Quests als CSV-Datei. Öffnet sich in Excel, Numbers oder Google Sheets.'))
        st.download_button('⬇️ '+_tx('Download CSV','Descarregar CSV','Télécharger le CSV','CSV herunterladen'),
                           data=completed_csv(everything),file_name=f'life-quest-history-{recap["week_start"].isoformat()}.csv',
                           mime='text/csv',disabled=total==0,type='primary',key='export_csv')
