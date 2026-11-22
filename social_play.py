"""Shared squad missions and pair-specific daily competitions."""
from quest_display import quest_text, quest_texts
import streamlit as st
from ai_quest_ui import render_quest_styles
from design import hero, member_chips, squad_ranking
from auth_helpers import friendly_error, plain_markdown
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
        st.error(friendly_error(error))
    else:
        st.session_state.social_notice=message
        st.rerun()


def queue_squad_confirmation(quest_id):
    if st.session_state.get('team_check_'+quest_id):
        st.session_state.team_confirmation_request=quest_id

def render_social(api, competition=False):
    render_quest_styles()

    if competition:
        st.markdown('<div class="lq-eyebrow">' + tx("Competition", "Competição", "Compétition", "Wettbewerb") + '</div>', unsafe_allow_html=True)
        st.title(tx("A friendly challenge", "Um desafio entre amigos", "Un défi entre amis", "Ein freundschaftlicher Wettstreit"))
        hero(
            tx("Daily 1v1 quests", "Missões diárias 1v1", "Quêtes quotidiennes en duel", "Tägliche 1-gegen-1-Quests"),
            tx("Challenge a friend", "Desafia um amigo", "Défie un ami", "Fordere einen Freund heraus"),
            tx("Same quest. Your own pace. A new winner every week.",
               "A mesma missão. Ao teu ritmo. Um novo vencedor a cada semana.",
               "La même quête. À ton rythme. Un nouveau gagnant chaque semaine.",
               "Dieselbe Quest. Dein eigenes Tempo. Jede Woche ein neuer Sieger."),
            variant="peach",
        )
    else:
        st.markdown('<div class="lq-eyebrow">' + tx("Squad", "Equipa", "Équipe", "Team") + '</div>', unsafe_allow_html=True)
        st.title(tx("Better together", "Melhores juntos", "Ensemble, c'est mieux", "Gemeinsam besser"))
        hero(
            tx("Shared quests", "Missões partilhadas", "Quêtes communes", "Gemeinsame Quests"),
            tx("Grow with your friends", "Cresce com os teus amigos", "Progresse avec tes amis", "Wachse mit deinen Freunden"),
            tx("Share real experiences and complete quests together.",
               "Partilha experiências reais e completa missões em conjunto.",
               "Partage de vraies expériences et réalise des quêtes en équipe.",
               "Teilt echte Erlebnisse und erledigt gemeinsam Quests."),
            variant="lilac",
        )

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
            st.error(friendly_error(error))
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

    if competition:
        render_competitions(api, state)
    else:
        render_squads(api, state)

def render_squad_ranking(api, squad):
    """This week's XP for the members of one squad (from the weekly leaderboard, matched by name)."""
    board, error = rpc(api, 'get_weekly_leaderboard')
    if error or not isinstance(board, list):
        st.caption(tx("This week's ranking could not be loaded.", "Não foi possível carregar a classificação desta semana.",
                      "Impossible de charger le classement de la semaine.", "Die Rangliste dieser Woche konnte nicht geladen werden."))
        return
    scores = {r.get('display_name'): r for r in board}
    rows = [{'name': m['name'] or '?',
             'points': (scores.get(m['name']) or {}).get('weekly_points') or 0,
             'quests': (scores.get(m['name']) or {}).get('quests_completed') or 0}
            for m in squad['members']]
    squad_ranking(
        rows, st.session_state.profile.get('display_name', ''),
        tx("This week in your squad", "Esta semana na tua equipa", "Cette semaine dans ton équipe", "Diese Woche in deinem Team"),
        quests_label=tx("quests", "missões", "quêtes", "Quests"),
    )


def render_squads(api, state):
    squads = state['squads']

    left, right = st.columns([3, 2], gap="large")
    with left:
            if squads:
                options = {str(s['id']): s for s in squads}
                chosen = st.selectbox(
                    tx("Your squad", "A tua equipa", "Ton équipe", "Dein Team"),
                    list(options),
                    format_func=lambda k: options[k]['name']
                )
                squad = options[chosen]

                st.subheader(plain_markdown(squad['name']))
                member_chips([m['name'] for m in squad['members']])
                render_squad_ranking(api, squad)

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

                titles = quest_texts([q['title'] for q in squad['quests']])
                for quest, translated_title in zip(squad['quests'], titles):
                    mine = st.session_state.user['id'] in quest['confirmed']
                    key = 'team_check_' + quest['id']
                    st.session_state[key] = mine

                    with st.container(key='quest_row_team_' + quest['id']):
                        st.checkbox(
                            translated_title,
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

    with right:
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

    st.subheader(tx('A daily challenge. A weekly winner.','Um desafio diário. Um vencedor semanal.',
                    'Un défi quotidien. Un gagnant chaque semaine.','Eine tägliche Challenge. Ein Wochensieger.'))
    st.write(tx('One shared daily quest per friend. Add your result by 23:59 UTC.',
                'Uma missão diária partilhada por amigo. Regista o teu resultado até às 23:59 UTC.',
                'Une quête quotidienne commune par ami. Ajoute ton résultat avant 23 h 59 UTC.',
                'Eine gemeinsame Tagesquest pro Freund. Trage dein Ergebnis bis 23:59 UTC ein.'))
    with st.expander(tx('Scoring & deadlines','Pontuação e prazos','Points et délais','Punkte und Fristen')):
        st.caption(tx('Results are self-reported and editable until the end of the day, UTC. Weeks run Monday–Sunday.',
                      'Os resultados são declarados por cada um e podem ser editados até ao fim do dia, UTC. As semanas vão de segunda a domingo.',
                      'Les résultats sont déclarés par chacun et modifiables jusqu\'à la fin de la journée, UTC. Les semaines vont du lundi au dimanche.',
                      'Ergebnisse werden selbst eingetragen und können bis Tagesende (UTC) geändert werden. Wochen laufen von Montag bis Sonntag.'))
        st.caption(tx('Daily XP: winner 35, other submitting player 15, tied players 25 each. Weekly bonus: winner 50, participating players in a tied week 20 each. Missing entries earn no daily XP.',
                      'XP diário: vencedor 35, outro jogador que submeteu 15, empate 25 cada. Bónus semanal: vencedor 50, em semana empatada 20 para cada participante. Sem registo não há XP diário.',
                      'XP quotidiens : gagnant 35, autre joueur ayant participé 15, égalité 25 chacun. Bonus hebdomadaire : gagnant 50, semaine à égalité 20 par participant. Sans résultat, pas d\'XP quotidiens.',
                      'Tages-XP: Sieger 35, anderer Teilnehmer 15, Gleichstand je 25. Wochenbonus: Sieger 50, bei Gleichstand je 20 pro Teilnehmer. Ohne Eintrag gibt es keine Tages-XP.'))
        st.caption(tx('Closed days and weeks settle when either player opens this page. Previous results stay in your history.',
                      'Os dias e semanas fechados são calculados quando um dos jogadores abre esta página. Os resultados anteriores ficam no teu histórico.',
                      'Les jours et semaines terminés sont calculés dès qu\'un des joueurs ouvre cette page. Les résultats précédents restent dans ton historique.',
                      'Abgeschlossene Tage und Wochen werden ausgewertet, sobald einer der Spieler diese Seite öffnet. Frühere Ergebnisse bleiben in deinem Verlauf.'))
    with st.expander(tx('Challenge a friend','Desafiar um amigo','Défier un ami','Freund herausfordern'),expanded=not state['duels']):

        friends={f['id']:f['name'] for f in state['friends']}
        if friends:
            with st.form('challenge_squadmates'):
                selected=st.multiselect(tx('Choose friends from your squads','Escolhe amigos das tuas equipas',
                                           'Choisis des amis de tes équipes','Wähle Freunde aus deinen Teams'),
                                        list(friends),format_func=lambda k:friends[k])
                invite=st.form_submit_button(tx('Invite selected friends','Convidar amigos selecionados',
                                                'Inviter les amis choisis','Ausgewählte Freunde einladen'))
            if invite:
                errors=[]
                for friend in selected:
                    _,error=rpc(api,'create_friend_duel',{'friend_id':friend})
                    if error:errors.append(error)
                errors=[friendly_error(e) for e in errors]
                if errors:st.error(tx('Some invitations could not be created: ','Não foi possível criar alguns convites: ',
                                      'Certaines invitations n\'ont pas pu être créées : ','Einige Einladungen konnten nicht erstellt werden: ')+'; '.join(errors))
                elif selected:
                    st.session_state.social_notice=tx('Invitations created. Each friend can accept in their 1v1 page.',
                                                      'Convites criados. Cada amigo pode aceitar na sua página 1v1.',
                                                      'Invitations créées. Chaque ami peut accepter sur sa page 1 contre 1.',
                                                      'Einladungen erstellt. Jeder Freund kann sie auf seiner 1-gegen-1-Seite annehmen.')
                    st.rerun()

                else:st.info(tx('Select at least one friend.','Seleciona pelo menos um amigo.','Sélectionne au moins un ami.','Wähle mindestens einen Freund aus.'))
        st.write(tx('For a friend outside your squad, create an invitation and share its code yourself.',
                    'Para um amigo fora da tua equipa, cria um convite e partilha o código.',
                    'Pour un ami hors de ton équipe, crée une invitation et partage son code.',
                    'Für Freunde außerhalb deines Teams: Erstelle eine Einladung und teile den Code selbst.'))
        if st.button(tx('Create a 1v1 invite code','Criar código de convite 1v1','Créer un code d\'invitation 1 contre 1','1-gegen-1-Einladungscode erstellen')):
            act(api,'create_friend_duel',{'friend_id':None},tx('Invitation created. Share its code below.','Convite criado. Partilha o código abaixo.',
                                                                'Invitation créée. Partage son code ci-dessous.','Einladung erstellt. Teile den Code unten.'))
    with st.expander(tx('Accept a 1v1 invite code','Aceitar um código de convite 1v1','Accepter un code d\'invitation 1 contre 1','1-gegen-1-Einladungscode annehmen')):
        with st.form('accept_duel'):
            code=st.text_input(tx('Competition invite code','Código de convite da competição','Code d\'invitation du défi','Einladungscode des Wettbewerbs'),max_chars=20)
            join=st.form_submit_button(tx('Accept challenge','Aceitar desafio','Accepter le défi','Herausforderung annehmen'),type='primary')
        if join:
            if not code.strip():st.error(tx('Enter the invite code.','Introduz o código de convite.','Saisis le code d\'invitation.','Gib den Einladungscode ein.'))
            else:act(api,'join_friend_duel',{'invite':code.strip().upper()},tx('Your competition is live.','A tua competição começou.','Ton défi a commencé.','Dein Wettbewerb läuft.'))
    if st.button(tx('Refresh results','Atualizar resultados','Actualiser les résultats','Ergebnisse aktualisieren'),key='social_refresh'):st.rerun()
    if not state['duels']:st.info(tx('Your competitions will appear here once you invite a friend.',
                                     'As tuas competições aparecem aqui quando convidares um amigo.',
                                     'Tes défis apparaîtront ici dès que tu auras invité un ami.',
                                     'Deine Wettbewerbe erscheinen hier, sobald du einen Freund einlädst.'))
    not_submitted=tx('not submitted','não submetido','non envoyé','nicht eingetragen')
    you_won=tx('You won','Ganhaste','Tu as gagné','Du hast gewonnen')
    for pair in state['duels']:
        mine=pair['creator']==uid
        friend_id=pair['opponent'] if mine else pair['creator']
        friend_raw=(pair.get('opponent_name') if mine else pair.get('creator_name')) or tx('a friend','um amigo','un ami','ein Freund')
        friend_name=plain_markdown(friend_raw)   # shown as Markdown below; the table uses the raw name
        won=lambda name: tx(f'{name} won',f'{name} ganhou',f'{name} a gagné',f'{name} hat gewonnen')
        friend_won=won(friend_name)
        with st.container(key='card_duel_'+str(pair['id'])):
            st.subheader(tx('You vs ','Tu vs ','Toi contre ','Du gegen ')+friend_name)
            if pair['status']=='pending':
                if mine:
                    st.write(tx('Waiting for your friend to accept.','À espera que o teu amigo aceite.',
                                'En attente de l\'acceptation de ton ami.','Warte darauf, dass dein Freund annimmt.'))
                    st.code(pair['code'],language=None)
                else:
                    st.write(tx(f"{friend_name} invited you to a daily competition.",
                                f"{friend_name} convidou-te para uma competição diária.",
                                f"{friend_name} t'a invité à un défi quotidien.",
                                f"{friend_name} hat dich zu einem täglichen Wettbewerb eingeladen."))
                    if st.button(tx('Accept invitation','Aceitar convite','Accepter l\'invitation','Einladung annehmen'),key='accept_'+pair['id']):
                        act(api,'join_friend_duel',{'invite':pair['code']},tx('Challenge accepted.','Desafio aceite.','Défi accepté.','Herausforderung angenommen.'))

                continue
            days=pair['days']
            current=next((d for d in days if d['day']==state['today']),None)
            week_days=[d for d in days if d['day']>=state['week_start'] and d['settled']]

            a,b=st.container(key='stat_row_duel_'+str(pair['id'])).columns(2)
            a.metric(tx('Your wins this week','As tuas vitórias esta semana','Tes victoires cette semaine','Deine Siege diese Woche'),
                     sum(d['winner']==uid for d in week_days))
            b.metric(tx(f'{friend_name}’s wins',f'Vitórias de {friend_name}',f'Victoires de {friend_name}',f'Siege von {friend_name}'),
                     sum(d['winner']==friend_id for d in week_days))

            if current:
                scores={s['user_id']:s['value'] for s in current['scores']}
                st.markdown('**'+quest_text(current['title'])+'**')
                st.caption(tx('Today · ','Hoje · ','Aujourd\'hui · ','Heute · ')+state['today']+tx(' · the exact same quest for both of you',
                           ' · exatamente a mesma missão para os dois',' · exactement la même quête pour vous deux',' · genau dieselbe Quest für euch beide'))
                st.write(tx('Your result: ','O teu resultado: ','Ton résultat : ','Dein Ergebnis: ')+'**'+str(scores.get(uid,not_submitted))+'** · '
                         +friend_name+': **'+str(scores.get(friend_id,not_submitted))+'**')
                with st.form('score_'+current['id']):

                    value=st.number_input(tx('Your total','O teu total','Ton total','Deine Summe')+' ('+quest_text(current['unit'])+')',
                                          min_value=0,max_value=current['max'],value=scores.get(uid,0),step=1)
                    submitted=st.form_submit_button(tx('Save my result','Guardar o meu resultado','Enregistrer mon résultat','Mein Ergebnis speichern'),type='primary')
                if submitted:act(api,'record_duel_score',{'quest_id':current['id'],'result_value':int(value)},
                                 tx('Your result is saved. You can update it before the deadline.',
                                    'O teu resultado foi guardado. Podes atualizá-lo até ao prazo.',
                                    'Ton résultat est enregistré. Tu peux le modifier avant la fin du délai.',
                                    'Dein Ergebnis ist gespeichert. Du kannst es bis zur Frist ändern.'))

            if pair['weeks']:
                st.markdown('**'+tx('Weekly results','Resultados semanais','Résultats de la semaine','Wochenergebnisse')+'**')
                for week in pair['weeks']:
                    outcome=tx('A shared win','Vitória partilhada','Victoire partagée','Geteilter Sieg') if week['tied'] else you_won if week['winner']==uid else friend_won
                    st.write('🏆 '+tx('Week of ','Semana de ','Semaine du ','Woche vom ')+week['week']+' · '+outcome)
            with st.expander(tx('Daily results and previous challenges','Resultados diários e desafios anteriores',
                                'Résultats quotidiens et défis précédents','Tagesergebnisse und frühere Herausforderungen')):
                columns=[tx('Day','Dia','Jour','Tag'),tx('Quest','Missão','Quête','Quest'),tx('Unit','Unidade','Unité','Einheit'),
                         tx('You','Tu','Toi','Du'),tx('Friend','Amigo','Ami','Freund'),tx('Result','Resultado','Résultat','Ergebnis')]
                table=[]
                for d in days:
                    scores={s['user_id']:s['value'] for s in d['scores']}
                    outcome=(tx('Open','Em aberto','En cours','Offen') if not d['settled']
                             else tx('No entries','Sem registos','Aucun résultat','Keine Einträge') if not scores
                             else tx('Tie','Empate','Égalité','Unentschieden') if d['winner'] is None
                             else you_won if d['winner']==uid else won(friend_raw))
                    table.append(dict(zip(columns,[d['day'],quest_text(d['title']),quest_text(d['unit']),str(scores.get(uid,'—')),str(scores.get(friend_id,'—')),outcome])))
                st.dataframe(table,hide_index=True,width='stretch')
