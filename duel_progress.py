"""Live standings from confirmed pair results; current-day scores stay provisional."""
def standings(pair,state,own_id,own_name):
    people=[(pair['creator'],own_name if pair['creator']==own_id else pair.get('creator_name') or '—'),
            (pair['opponent'],own_name if pair['opponent']==own_id else pair.get('opponent_name') or '—')]
    current=next((d for d in pair['days'] if d['day']==state['today']),None)
    scores={s['user_id']:s['value'] for s in current['scores']} if current else {}
    rows=[]
    for uid,name in people:
        xp=0
        for day in pair['days']:
            if day['day']<state['week_start'] or not day['settled']:
                continue
            if any(s['user_id']==uid for s in day['scores']):
                xp+=15+(20 if day['winner']==uid else 10 if day['winner'] is None else 0)
        rows.append({'user_id':uid,'name':name,'points':xp,'result':scores.get(uid,'—'),'live_score':scores.get(uid,-1)})
    rows.sort(key=lambda r:(-r['points'],-r['live_score'],r['user_id'] or ''))
    for i,row in enumerate(rows):
        row['place']=1 if i==0 or (row['points'],row['live_score'])==(rows[0]['points'],rows[0]['live_score']) else 2
    return rows
