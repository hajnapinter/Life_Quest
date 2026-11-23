"""All-user weekly XP ranking, settled and protected by database RPCs."""
import streamlit as st
from design import leaderboard
from personalization import tr


@st.fragment(run_every='30s')
def render_weekly_leaderboard(api):
    language=st.session_state.get('language','en')
    st.title(tr(('Weekly leaderboard','Classificação semanal','Classement hebdomadaire','Wochenrangliste'),language))
    st.caption(tr(('Monday–Sunday, UTC · refreshes every 30 seconds.','Segunda–domingo, UTC · atualiza a cada 30 segundos.',
                   'Lundi–dimanche, UTC · actualisation toutes les 30 secondes.','Montag–Sonntag, UTC · aktualisiert alle 30 Sekunden.'),language))
    data,error=api('POST','/rest/v1/rpc/get_global_weekly_ranking',{},st.session_state.access_token)
    if error or not isinstance(data,dict):
        st.error(tr(('The weekly ranking could not be loaded. Please retry.','Não foi possível carregar a classificação. Tenta novamente.',
                     'Impossible de charger le classement. Réessaie.','Die Wochenrangliste konnte nicht geladen werden. Bitte versuche es erneut.'),language))
        return
    if type(data.get('your_total')) is int:
        st.session_state.profile['points']=data['your_total']
    rows=[{**row,'is_me':row['user_id']==st.session_state.user['id']} for row in data.get('rows',[])]
    st.caption(tr(('Week starting ','Semana de ','Semaine du ','Woche ab '),language)+data['week_start'])
    leaderboard(rows,'',quests_label=tr(('quests','missões','quêtes','Quests'),language))
    st.caption(tr(('Weekly prizes: 1st +100 XP · 2nd +50 XP · 3rd +25 XP. Only users who earn XP that week qualify. Prize XP does not count towards another weekly ranking.',
                   'Prémios semanais: 1.º +100 XP · 2.º +50 XP · 3.º +25 XP. Só participa quem ganha XP nessa semana. O prémio não conta para outra classificação.',
                   'Prix hebdomadaires : 1er +100 XP · 2e +50 XP · 3e +25 XP. Il faut gagner des XP dans la semaine. Les prix ne comptent pas pour un autre classement.',
                   'Wochenpreise: 1. +100 XP · 2. +50 XP · 3. +25 XP. Nur mit verdienten Wochen-XP. Preis-XP zählen nicht für eine weitere Wochenrangliste.'),language))
    with st.expander(tr(('How ties are resolved','Como se resolvem empates','Départage des égalités','So werden Gleichstände entschieden'),language)):
        st.write(tr(('Equal XP: more completed quests, then the earlier last XP activity, then a stable account ID. Scores reset every Monday; your lifetime XP stays.',
                     'XP igual: mais missões concluídas, depois a última atividade com XP mais cedo e por fim o ID da conta. Reinicia à segunda; o XP total mantém-se.',
                     'XP égaux : plus de quêtes terminées, puis dernière activité XP la plus ancienne, puis identifiant stable. Remise à zéro le lundi ; XP totaux conservés.',
                     'Gleiche XP: mehr abgeschlossene Quests, dann frühere letzte XP-Aktivität, dann stabile Konto-ID. Neustart montags; Gesamt-XP bleiben erhalten.'),language))
    for prize in data.get('prizes',[]):
        st.success(tr(('Your weekly prize','O teu prémio semanal','Ton prix hebdomadaire','Dein Wochenpreis'),language)+f": #{prize['place']} · +{prize['points']} XP · {prize['week']}")
