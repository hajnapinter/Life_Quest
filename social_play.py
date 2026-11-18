"""Shared squad missions and pair-specific daily competitions."""
import streamlit as st
from ai_quest_ui import render_quest_styles
def tx(en, pt, fr, de):
    language = st.session_state.get("language", "en")
    translations = {
        "en": en,
        "pt": pt,
        "fr": fr,
        "de": de,
    }
    return translations.get(language, en)



def rpc(api, name, payload=None):
    return api('POST','/rest/v1/rpc/'+name,payload or {},st.session_state.access_token)


def act(api, name, payload, message):
    _,error=rpc(api,name,payload)
    if error:
        st.error(error)
    else:
        st.session_state.social_notice=message
        st.rerun()


def queue_squad_confirmation(quest_id):
    if st.session_state.get('team_check_'+quest_id):
        st.session_state.team_confirmation_request=quest_id

def render_social(api):
    render_quest_styles()

    st.title(tx(
        "Better together",
        "Melhores juntos",
        "Ensemble, c'est mieux",
        "Gemeinsam besser"
    ))

    st.write(tx(
        "Share a real experience, or give a friend a friendly challenge.",
        "Partilha uma experiência real ou desafia um amigo de forma amigável.",
        "Partage une vraie expérience ou lance un défi amical à un ami.",
        "Teile ein echtes Erlebnis oder fordere einen Freund zu einer freundlichen Herausforderung heraus."
    ))

    state, error = rpc(api, 'get_social_state')

    if error or not isinstance(state, dict):
        st.error(tx(
            "Your squads and competitions could not be loaded. Please try again.",
            "Não foi possível carregar as tuas equipas e competições. Tenta novamente.",
            "Impossible de charger tes équipes et compétitions. Réessaie.",
            "Deine Teams und Wettbewerbe konnten nicht geladen werden. Bitte versuche es erneut."
        ))
        if st.button(tx("Try again", "Tentar novamente", "Réessayer", "Erneut versuchen")):
            st.rerun()
        return

    before = st.session_state.profile.get('points', 0)
    pending = st.session_state.get('team_confirmation_request')

    if pending:
        _, error = rpc(api, 'confirm_squad_quest', {'quest_id': pending})
        st.session_state.pop('team_confirmation_request', None)

        if error:
            st.session_state['team_check_' + pending] = False
            st.error(error)
        else:
            refreshed, refresh_error = rpc(api, 'get_social_state')
            if not refresh_error and isinstance(refreshed, dict):
                state = refreshed
            else:
                st.info(tx(
                    "Your participation was saved. Refresh to load the latest result.",
                    "A tua participação foi guardada. Atualiza para ver o resultado mais recente.",
                    "Ta participation a été enregistrée. Actualise pour voir le dernier résultat.",
                    "Deine Teilnahme wurde gespeichert. Aktualisiere, um das neueste Ergebnis zu laden."
                ))
            st.toast(tx(
                "Participation confirmed!",
                "Participação confirmada!",
                "Participation confirmée !",
                "Teilnahme bestätigt!"
            ), icon='🤝')

    if type(state.get('points')) is int:
        st.session_state.profile['points'] = state['points']
        gained = max(0, state['points'] - before)
        if gained:
            st.toast(f'+{gained} XP · ' + tx(
                "Nice work!",
                "Muito bem!",
                "Bravo !",
                "Gut gemacht!"
            ), icon='🌱')

    if st.session_state.get('social_notice'):
        st.success(st.session_state.pop('social_notice'))

    together, competition = st.tabs([
        tx("🤝 Squad quests", "🤝 Missões de equipa", "🤝 Quêtes d'équipe", "🤝 Team-Quests"),
        tx("⚔️ 1v1 competitions", "⚔️ Competições 1v1", "⚔️ Compétitions 1 contre 1", "⚔️ 1-gegen-1-Wettbewerbe")
    ])

    with together:
        render_squads(api, state)

    with competition:
        render_competitions(api, state)

def render_squads(api, state):
    squads = state['squads']

    if squads:
        options = {str(s['id']): s for s in squads}
        chosen = st.selectbox(
            tx("Your squad", "A tua equipa", "Ton équipe", "Dein Team"),
            list(options),
            format_func=lambda k: options[k]['name']
        )
        squad = options[chosen]

        st.subheader(squad['name'])
        st.caption(' · '.join(m['name'] for m in squad['members']))

        with st.expander(tx("Invite a friend", "Convidar um amigo", "Inviter un ami", "Freund einladen")):
            st.write(tx(
                "Ask your friend to open Squad quests and enter this code:",
                "Pede ao teu amigo para abrir as missões de equipa e introduzir este código:",
                "Demande à ton ami d'ouvrir les quêtes d'équipe et de saisir ce code :",
                "Bitte deinen Freund, die Team-Quests zu öffnen und diesen Code einzugeben:"
            ))
            st.code(squad['invite_code'], language=None)

        st.caption(tx(
            "Three shared quests each week. Do them together, then each participant confirms. At least two confirmations unlock 30 XP per participant.",
            "Três missões partilhadas por semana. Façam-nas juntos e cada participante confirma. Pelo menos duas confirmações desbloqueiam 30 XP por participante.",
            "Trois quêtes communes par semaine. Réalisez-les ensemble, puis chaque participant confirme. Au moins deux confirmations débloquent 30 XP par participant.",
            "Drei gemeinsame Quests pro Woche. Erledigt sie zusammen und bestätigt sie jeweils. Mindestens zwei Bestätigungen schalten 30 XP pro Teilnehmer frei."
        ))

        confirmed_total = sum(
            st.session_state.user['id'] in q['confirmed']
            for q in squad['quests']
        )

        st.caption(tx(
            f"Your participation: {confirmed_total}/{len(squad['quests'])} confirmed",
            f"A tua participação: {confirmed_total}/{len(squad['quests'])} confirmadas",
            f"Ta participation : {confirmed_total}/{len(squad['quests'])} confirmées",
            f"Deine Teilnahme: {confirmed_total}/{len(squad['quests'])} bestätigt"
        ))

        for quest in squad['quests']:
            mine = st.session_state.user['id'] in quest['confirmed']
            key = 'team_check_' + quest['id']
            st.session_state[key] = mine

            with st.container(key='quest_row_team_' + quest['id']):
                st.checkbox(
                    quest['title'],
                    key=key,
                    disabled=mine or len(squad['members']) < 2,
                    on_change=queue_squad_confirmation,
                    args=(quest['id'],)
                )

        if len(squad['members']) < 2:
            st.info(tx(
                "Invite a friend to start checking off shared quests together.",
                "Convida um amigo para começarem a completar missões juntos.",
                "Invite un ami pour commencer à réaliser des quêtes ensemble.",
                "Lade einen Freund ein, damit ihr gemeinsam Quests abschließen könnt."
            ))

    else:
        st.subheader(tx(
            "Turn a plan with friends into a shared quest",
            "Transforma um plano com amigos numa missão partilhada",
            "Transforme un projet entre amis en quête commune",
            "Mach aus einem Plan mit Freunden eine gemeinsame Quest"
        ))

        st.write(tx(
            "Start a squad, share its code and choose an experience to do together. Everyone needs their own Life Quest account.",
            "Cria uma equipa, partilha o código e escolhe uma experiência para fazerem juntos. Todos precisam da sua própria conta Life Quest.",
            "Crée une équipe, partage son code et choisissez une expérience à faire ensemble. Chaque personne doit avoir son propre compte Life Quest.",
            "Gründe ein Team, teile den Code und wähle ein gemeinsames Erlebnis. Jeder benötigt ein eigenes Life-Quest-Konto."
        ))

    with st.expander(
        tx("Start another squad", "Criar outra equipa", "Créer une autre équipe", "Weiteres Team erstellen")
        if squads else
        tx("Start your squad", "Criar a tua equipa", "Créer ton équipe", "Dein Team erstellen"),
        expanded=not squads
    ):
        with st.form('social_create_squad'):
            name = st.text_input(
                tx("Squad name", "Nome da equipa", "Nom de l'équipe", "Teamname"),
                max_chars=50
            )
            submit = st.form_submit_button(
                tx("Start a squad", "Criar uma equipa", "Créer une équipe", "Team erstellen"),
                type='primary'
            )

        if submit:
            if len(name.strip()) < 2:
                st.error(tx(
                    "Choose a name with at least two characters.",
                    "Escolhe um nome com pelo menos dois caracteres.",
                    "Choisis un nom d'au moins deux caractères.",
                    "Wähle einen Namen mit mindestens zwei Zeichen."
                ))
            else:
                act(api, 'create_squad', {'squad_name_input': name.strip()}, tx(
                    "Your squad is ready. Share its invite code with your friends.",
                    "A tua equipa está pronta. Partilha o código de convite com os teus amigos.",
                    "Ton équipe est prête. Partage le code d'invitation avec tes amis.",
                    "Dein Team ist bereit. Teile den Einladungscode mit deinen Freunden."
                ))

    with st.expander(tx(
        "I have a squad invite code",
        "Tenho um código de convite",
        "J'ai un code d'invitation",
        "Ich habe einen Einladungscode"
    )):
        with st.form('social_join_squad'):
            code = st.text_input(tx(
                "Squad invite code", "Código de convite da equipa",
                "Code d'invitation de l'équipe", "Team-Einladungscode"
            ))
            join = st.form_submit_button(tx(
                "Join my friends", "Juntar-me aos meus amigos",
                "Rejoindre mes amis", "Meinen Freunden beitreten"
            ))

        if join:
            if not code.strip():
                st.error(tx(
                    "Enter the invite code your friend shared.",
                    "Introduz o código de convite que o teu amigo partilhou.",
                    "Saisis le code d'invitation partagé par ton ami.",
                    "Gib den Einladungscode ein, den dein Freund geteilt hat."
                ))
            else:
                act(api, 'join_squad', {'invite_code_input': code.strip().upper()}, tx(
                    "You joined the squad.",
                    "Entraste na equipa.",
                    "Tu as rejoint l'équipe.",
                    "Du bist dem Team beigetreten."
                ))


def render_competitions(api,state):
    uid=st.session_state.user['id']
    st.subheader('A daily challenge. A weekly winner.')
    st.write('One shared daily quest per friend. Add your result by 23:59 UTC.')
    with st.expander('Scoring & deadlines'):
        st.caption('Results are self-reported and editable until the end of the day, UTC. Weeks run Monday–Sunday.')
        st.caption('Daily XP: winner 35, other submitting player 15, tied players 25 each. Weekly bonus: winner 50, participating players in a tied week 20 each. Missing entries earn no daily XP.')
        st.caption('Closed days and weeks settle when either player opens this page. Previous results stay in your history.')
    with st.expander('Challenge a friend',expanded=not state['duels']):
        friends={f['id']:f['name'] for f in state['friends']}
        if friends:
            with st.form('challenge_squadmates'):
                selected=st.multiselect('Choose friends from your squads',list(friends),format_func=lambda k:friends[k])
                invite=st.form_submit_button('Invite selected friends')
            if invite:
                errors=[]
                for friend in selected:
                    _,error=rpc(api,'create_friend_duel',{'friend_id':friend})
                    if error:errors.append(error)
                if errors:st.error('Some invitations could not be created: '+'; '.join(errors))
                elif selected:
                    st.session_state.social_notice='Invitations created. Each friend can accept in their 1v1 page.'
                    st.rerun()
                else:st.info('Select at least one friend.')
        st.write('For a friend outside your squad, create an invitation and share its code yourself.')
        if st.button('Create a 1v1 invite code'):
            act(api,'create_friend_duel',{'friend_id':None},'Invitation created. Share its code below.')
    with st.expander('Accept a 1v1 invite code'):
        with st.form('accept_duel'):
            code=st.text_input('Competition invite code')
            join=st.form_submit_button('Accept challenge',type='primary')
        if join:
            if not code.strip():st.error('Enter the invite code.')
            else:act(api,'join_friend_duel',{'invite':code.strip().upper()},'Your competition is live.')
    if st.button('Refresh results',key='social_refresh'):st.rerun()
    if not state['duels']:st.info('Your competitions will appear here once you invite a friend.')
    for pair in state['duels']:
        mine=pair['creator']==uid
        friend_id=pair['opponent'] if mine else pair['creator']
        friend_name=(pair.get('opponent_name') if mine else pair.get('creator_name')) or 'a friend'
        with st.container(border=True):
            st.subheader('You vs '+friend_name)
            if pair['status']=='pending':
                if mine:
                    st.write('Waiting for your friend to accept.')
                    st.code(pair['code'],language=None)
                else:
                    st.write(pair['creator_name']+' invited you to a daily competition.')
                    if st.button('Accept invitation',key='accept_'+pair['id']):
                        act(api,'join_friend_duel',{'invite':pair['code']},'Challenge accepted.')
                continue
            days=pair['days']
            current=next((d for d in days if d['day']==state['today']),None)
            week_days=[d for d in days if d['day']>=state['week_start'] and d['settled']]
            a,b=st.columns(2)
            a.metric('Your wins this week',sum(d['winner']==uid for d in week_days))
            b.metric(friend_name+'’s wins',sum(d['winner']==friend_id for d in week_days))
            if current:
                scores={s['user_id']:s['value'] for s in current['scores']}
                st.markdown('**'+current['title']+'**')
                st.caption('Today · '+state['today']+' · the exact same quest for both of you')
                st.write('Your result: **'+str(scores.get(uid,'not submitted'))+'** · '+friend_name+': **'+str(scores.get(friend_id,'not submitted'))+'**')
                with st.form('score_'+current['id']):
                    value=st.number_input('Your total ('+current['unit']+')',min_value=0,max_value=current['max'],value=scores.get(uid,0),step=1)
                    submitted=st.form_submit_button('Save my result',type='primary')
                if submitted:act(api,'record_duel_score',{'quest_id':current['id'],'result_value':int(value)},'Your result is saved. You can update it before the deadline.')
            if pair['weeks']:
                st.markdown('**Weekly results**')
                for week in pair['weeks']:
                    outcome='A shared win' if week['tied'] else 'You won' if week['winner']==uid else friend_name+' won'
                    st.write('🏆 Week of '+week['week']+' · '+outcome)
            with st.expander('Daily results and previous challenges'):
                table=[]
                for d in days:
                    scores={s['user_id']:s['value'] for s in d['scores']}
                    outcome='Open' if not d['settled'] else 'No entries' if not scores else 'Tie' if d['winner'] is None else 'You won' if d['winner']==uid else friend_name+' won'
                    table.append({'Day':d['day'],'Quest':d['title'],'Unit':d['unit'],'You':str(scores.get(uid,'—')),'Friend':str(scores.get(friend_id,'—')),'Result':outcome})
                st.dataframe(table,hide_index=True,width='stretch')
