"""Shared squad missions and pair-specific daily competitions."""
import streamlit as st
from ai_quest_ui import render_quest_styles


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
    st.title('Better together')
    st.write('Share a real experience, or give a friend a friendly challenge.')
    state,error=rpc(api,'get_social_state')
    if error or not isinstance(state,dict):
        st.error('Your squads and competitions could not be loaded. Please try again.')
        if st.button('Try again'):st.rerun()
        return
    before=st.session_state.profile.get('points',0)
    pending=st.session_state.get('team_confirmation_request')
    if pending:
        _,error=rpc(api,'confirm_squad_quest',{'quest_id':pending})
        st.session_state.pop('team_confirmation_request',None)
        if error:
            st.session_state['team_check_'+pending]=False
            st.error(error)
        else:
            refreshed,refresh_error=rpc(api,'get_social_state')
            if not refresh_error and isinstance(refreshed,dict):
                state=refreshed
            else:
                st.info('Your participation was saved. Refresh to load the latest result.')
            st.toast('Participation confirmed!',icon='🤝')
    if type(state.get('points')) is int:
        st.session_state.profile['points']=state['points']
        gained=max(0,state['points']-before)
        if gained:
            st.toast(f'+{gained} XP · Nice work!',icon='🌱')
    if st.session_state.get('social_notice'):
        st.success(st.session_state.pop('social_notice'))
    together,competition=st.tabs(['🤝 Squad quests','⚔️ 1v1 competitions'])
    with together:
        render_squads(api,state)
    with competition:
        render_competitions(api,state)


def render_squads(api,state):
    squads=state['squads']
    if squads:
        options={str(s['id']):s for s in squads}
        chosen=st.selectbox('Your squad',list(options),format_func=lambda k:options[k]['name'])
        squad=options[chosen]
        st.subheader(squad['name'])
        st.caption(' · '.join(m['name'] for m in squad['members']))
        with st.expander('Invite a friend'):
            st.write('Ask your friend to open Squad quests and enter this code:')
            st.code(squad['invite_code'],language=None)
        st.caption('Three shared quests each week. Do them together, then each participant confirms. At least two confirmations unlock 30 XP per participant.')
        confirmed_total=sum(st.session_state.user['id'] in q['confirmed'] for q in squad['quests'])
        st.caption(f'Your participation: {confirmed_total}/{len(squad["quests"])} confirmed')
        for quest in squad['quests']:
            mine=st.session_state.user['id'] in quest['confirmed']
            key='team_check_'+quest['id']
            st.session_state[key]=mine
            with st.container(key='quest_row_team_'+quest['id']):
                st.checkbox(quest['title'],key=key,disabled=mine or len(squad['members'])<2,
                            on_change=queue_squad_confirmation,args=(quest['id'],))
        if len(squad['members'])<2:
            st.info('Invite a friend to start checking off shared quests together.')

    else:
        st.subheader('Turn a plan with friends into a shared quest')
        st.write('Start a squad, share its code and choose an experience to do together. Everyone needs their own Life Quest account.')
    with st.expander('Start another squad' if squads else 'Start your squad',expanded=not squads):
        with st.form('social_create_squad'):
            name=st.text_input('Squad name',placeholder='e.g. Weekend explorers',max_chars=50)
            submit=st.form_submit_button('Start a squad',type='primary')
        if submit:
            if len(name.strip())<2:st.error('Choose a name with at least two characters.')
            else:act(api,'create_squad',{'squad_name_input':name.strip()},'Your squad is ready. Share its invite code with your friends.')
    with st.expander('I have a squad invite code'):
        with st.form('social_join_squad'):
            code=st.text_input('Squad invite code')
            join=st.form_submit_button('Join my friends')
        if join:
            if not code.strip():st.error('Enter the invite code your friend shared.')
            else:act(api,'join_squad',{'invite_code_input':code.strip().upper()},'You joined the squad.')


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
