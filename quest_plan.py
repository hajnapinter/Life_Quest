"""Five independent habit tracks per pillar, with bounded, practical targets."""
from datetime import datetime, timezone
import re

EXPERIENCE_FOCUSES={'new_place','new_route','local_event','new_experience','nature','new_sport','new_hobby','financial_learning','yoga'}

# focus, five starting targets, two short title templates, short completion detail
TRACKS = {
 'Fitness': [
  ('steps', [2000,4000,6000,8000,10000], ['Walk {n:,} steps today', 'Reach {n:,} steps across your day'], 'Split the steps into short walks that fit your day.'),
  ('new_sport', [5,10,15,20,25], ['Try a sport you have never tried', 'Join a beginner session in a new sport'], 'Choose a beginner activity you have not tried. Move at a comfortable pace.'),
  ('mobility', [3,5,7,10,12], ['Stretch for {n} minutes', 'Take a {n}-minute mobility break'], 'Gently stretch after sitting; stay within a comfortable range.'),
  ('strength', [3,5,7,10,12], ['Do a {n}-minute beginner strength session', 'Make time for {n} minutes of gentle bodyweight exercise'], 'Choose an easy, equipment-free routine and take breaks as needed.'),
  ('yoga', [5,8,10,15,20], ['Try a beginner yoga class', 'Learn a new beginner yoga sequence'], 'Use a beginner video or a free community session. Adapt poses to your comfort.'),
 ],
 'Finance': [
  ('spending_log', [3,5,7,10,12], ['Track {n} expenses in a spreadsheet', 'Add your latest {n} purchases to a spending tracker'], 'Create or update a simple Excel or Sheets table: date, item, category and amount.'),
  ('financial_learning', [5,10,15,20,25], ['Listen to an episode about investing basics', 'Read an article about building a savings habit'], 'Pick an educational source. Write down one idea; this quest does not involve buying investments.'),
  ('budget', [1,2,3,4,5], ['Set a budget for {n} spending categories', 'Review {n} categories in your monthly budget'], 'Choose realistic limits using your own recent spending.'),
  ('money_review', [1,2,3,4,5], ['Review {n} recurring payments', 'Check {n} subscriptions or regular bills'], 'Note the price and whether each payment is still useful. You decide whether to change it.'),
  ('saving_goal', [1,2,3,4,5], ['Write down {n} saving goals', 'Add {n} small steps to your savings plan'], 'Give each goal an amount or next action. No transfer or purchase is required.'),
 ],
 'Languages': [
  ('vocabulary', [5,10,15,20,25], ['Learn {n} new words in your chosen language', 'Practise {n} new vocabulary words'], 'For example, choose Japanese. Review the words once, then recall them without looking.'),
  ('listening', [3,5,10,15,20], ['Listen to {n} minutes in your chosen language', 'Watch a {n}-minute beginner language video'], 'Use subtitles if helpful and note one phrase you understood.'),
  ('speaking', [1,2,3,4,5], ['Speak aloud in your chosen language for {n} minutes', 'Describe your day aloud for {n} minutes'], 'Use simple sentences. It is fine to look up words as you go.'),
  ('writing', [2,3,5,7,10], ['Write {n} sentences in your chosen language', 'Describe something you like in {n} sentences'], 'Use new vocabulary and check one sentence afterwards.'),
  ('reading', [3,5,8,10,15], ['Read in your chosen language for {n} minutes', 'Explore a short article for {n} minutes'], 'Choose something at your level and note one useful expression.'),
 ],
 'Personal Growth': [
  ('nonfiction', [3,5,10,15,20], ['Read {n} pages of a nonfiction book', 'Continue your nonfiction book for {n} pages'], 'Choose a book that teaches something you care about. Note one useful takeaway.'),
  ('new_hobby', [5,10,15,20,25], ['Try a hobby you have never tried', 'Make something using a new creative technique'], 'Try drawing, origami, writing or another hobby using materials you already have.'),
  ('public_speaking', [1,2,3,4,5], ['Give a {n}-minute speech to your mirror', 'Practise presenting an idea for {n} minutes'], 'Pick a topic you enjoy. Practise a clear opening, one idea and a short ending.'),
  ('planning', [1,2,3,4,5], ['Choose {n} priorities for tomorrow', 'Plan {n} concrete next steps for a personal goal'], 'Write each as a small action you can actually start.'),
  ('focused_learning', [5,10,15,20,25], ['Learn a useful skill for {n} minutes', 'Take {n} minutes of a free course'], 'Choose one short lesson and try one thing you learned.'),
 ],
 'Social': [
  ('reconnect', [1,1,2,2,3], ['Check in with {n} friend(s)', 'Send a thoughtful message to {n} person(s)'], 'Ask how they are doing and make time to read or hear the answer.'),
  ('kindness', [1,1,2,2,3], ['Give {n} sincere compliment(s)', 'Thank {n} person(s) for something specific'], 'Keep it respectful and natural; choose someone who seems open to conversation.'),
  ('new_conversation', [1,1,2,2,3], ['Start {n} friendly conversation(s)', 'Say hello to {n} new person(s)'], 'Try a classmate or someone at an event. Respect their space if they do not want to talk.'),
  ('make_plans', [1,1,1,2,2], ['Suggest {n} simple catch-up plan(s)', 'Invite a friend to {n} free shared activity/activities'], 'A walk, study session or home-cooked meal works. Sending the invitation completes the quest.'),
  ('listen', [3,5,7,10,15], ['Have a phone-free conversation for {n} minutes', 'Give someone your full attention for {n} minutes'], 'Ask an open question and listen without checking your phone.'),
 ],
 'Adventure': [
  ('new_place', [1,1,1,1,1], ['Explore a new place nearby', 'Visit a local spot you have never been to', 'Discover a free exhibition or a new neighbourhood'], 'Choose a public place that genuinely interests you.'),
  ('new_route', [1,1,1,1,1], ['Try a different walking route', 'Take an unfamiliar route to a familiar place', 'Discover a new park or trail nearby'], 'Choose a safe, accessible route you have not tried before.'),
  ('local_event', [1,1,1,1,1], ['Find a free local event you would like to attend', 'Try a free workshop or community activity', 'Visit a local market you have never explored'], 'Check the real date and availability, then pick an event that fits you.'),
  ('new_experience', [1,1,1,1,1], ['Try a recipe from a cuisine you have never cooked', 'Make a meal using three different coloured vegetables', 'Learn a new cooking technique with ingredients you have'], 'Choose a manageable recipe or technique and use ingredients within your budget.'),
  ('nature', [1,1,1,1,1], ['Get a new plant or swap a cutting with a friend', 'Visit a garden you have never been to', 'Learn how to propagate a plant you already have'], 'A free plant swap or a public garden counts. Pick the option that interests you.'),
 ],
 'Health': [
  ('sleep_routine', [5,10,15,20,25], ['Start winding down {n} minutes before bed', 'Make {n} minutes for a calm bedtime routine'], 'Choose a simple routine such as reading and dimming the lights.'),
  ('screen_break', [5,10,15,20,25], ['Take a {n}-minute screen-free break', 'Spend {n} minutes away from social media'], 'Choose a natural pause in your day and put the phone out of reach.'),
  ('meal_planning', [1,1,2,2,3], ['Plan {n} simple meal(s) for the week', 'Prepare {n} easy meal idea(s) for a busy day'], 'Use foods you enjoy and already have. Write a short plan or prepare ingredients.'),
  ('rest', [3,5,7,10,12], ['Take {n} minutes to relax', 'Make space for a {n}-minute quiet break'], 'Pause somewhere comfortable without trying to be productive.'),
  ('daily_routine', [1,2,3,4,5], ['Prepare {n} thing(s) for a calmer morning', 'Make {n} small improvements to your evening routine'], 'For example, pack a bag, set out clothes or tidy your desk.'),
 ],
}


def slot_plan(category, slot, start, history):
    focus, starts, titles, detail = TRACKS[category][slot - 1]
    level = max(1, min(5, int(start)))
    own = sorted([q for q in history if q.get('slot') == slot and q.get('category', category) == category], key=lambda q: q.get('completed_at') or q.get('created_at', ''))
    finished = [q for q in own if q.get('status') == 'completed']
    target = starts[level - 1]
    if finished or any(q.get('feedback')=='too_hard' for q in own):
        signals=[q for q in own if q.get('status')=='completed' or q.get('feedback')=='too_hard']
        last = signals[-1]
        previous = last.get('target') or target
        too_hard = last.get('feedback') == 'too_hard'
        if focus == 'steps':
            target = max(1000, min(12000, previous + (-1000 if too_hard else 2000)))
        elif too_hard:
            target = max(starts[0], previous - max(1, previous // 4))
        else:
            # Progress after each success, within a modest, practical ceiling.
            increment=max(1,starts[min(4,level)]-starts[level-1])
            target=min(starts[-1],previous+increment)
    if focus in EXPERIENCE_FOCUSES:
        target=1
    index = len([q for q in own if q.get('status') in ('completed', 'skipped')]) % len(titles)
    title = clean_title(titles[index].format(n=target), target)
    if focus == 'steps':
        minutes = min(120, max(10, target // 100))
    elif focus in ('saving_goal','budget','money_review','make_plans','kindness','reconnect','new_conversation','local_event','daily_routine','meal_planning','planning'):
        minutes = min(30, max(5, target * 3))
    else:
        minutes = min(45, max(5, target))
    metric=focus not in EXPERIENCE_FOCUSES
    return {'slot': slot, 'metric':metric, 'focus': focus, 'target': target, 'title': title,
            'description': detail, 'minutes': minutes, 'category': category,
            'difficulty': max(1,min(5,level + len(finished))), 'source': 'curated'}


def pillar_statistics(rows, today=None):
    from datetime import timedelta
    today = today or datetime.now(timezone.utc).date()
    finished = [q for q in rows if q.get('status') == 'completed']
    dates = [datetime.fromisoformat(q['completed_at'].replace('Z','+00:00')).date() for q in finished if q.get('completed_at')]
    this_week = sum(today - timedelta(days=6) <= d <= today for d in dates)
    previous = sum(today-timedelta(days=13) <= d < today-timedelta(days=6) for d in dates)
    streak, current = 0, today if today in dates else today-timedelta(days=1)
    while current in dates:
        streak += 1
        current -= timedelta(days=1)
    return {'completed':len(finished), 'xp':sum(10+5*q['difficulty'] for q in finished),
            'week':this_week,'week_delta':this_week-previous,'streak':streak,
            'activity':[{'Date':today-timedelta(days=i),'Quests':dates.count(today-timedelta(days=i))} for i in range(13,-1,-1)]}


def clean_title(title, target=None):
    if target is None:
        return title
    title=title.replace('activity/activities','activity' if target==1 else 'activities')
    title=title.replace('person(s)','person' if target==1 else 'people')
    title=title.replace('(s)','' if target==1 else 's')
    if target==1:
        for plural,singular in [('categories','category'),('payments','payment'),('goals','goal'),
                                ('steps','step'),('priorities','priority'),('improvements','improvement')]:
            title=re.sub(r'\b'+plural+r'\b',singular,title)
    return title


# ---------- Adaptivity hint shown under a quest ----------

def progress_hint(quest, rows):
    """('up' | 'down', previous_target) when this quest's target changed since the last completion in its slot."""
    target = quest.get('target')
    if quest.get('focus') in EXPERIENCE_FOCUSES or not isinstance(target, int):
        return None
    previous = [q for q in rows
                if q.get('status') == 'completed' and q.get('id') != quest.get('id')
                and q.get('category') == quest.get('category') and q.get('slot') == quest.get('slot')
                and isinstance(q.get('target'), int)]
    if not previous:
        return None
    last = max(previous, key=lambda q: q.get('completed_at') or '')['target']
    if target > last:
        return ('up', last)
    if target < last:
        return ('down', last)
    return None


# ---------- Weekly recap and CSV export ----------

def quest_xp(quest):
    """XP a completed quest earned: shared challenges carry points, pillar quests 10 + 5 x difficulty."""
    if quest.get('points') is not None:
        return int(quest['points'])
    return 10 + 5 * int(quest.get('difficulty') or 1)


def _completed_day(quest):
    value = quest.get('completed_at')
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()


def weekly_recap(rows, today=None):
    """Summary of the current week (Monday to today) compared with the previous one."""
    from datetime import timedelta
    today = today or datetime.now(timezone.utc).date()
    start = today - timedelta(days=today.weekday())
    previous_start = start - timedelta(days=7)
    done = [(q, _completed_day(q)) for q in rows if q.get('status') == 'completed']
    week = [(q, d) for q, d in done if d and start <= d <= today]
    last_week = [q for q, d in done if d and previous_start <= d < start]
    per_pillar, per_day = {}, {}
    for q, d in week:
        per_pillar[q.get('category', '')] = per_pillar.get(q.get('category', ''), 0) + 1
        per_day[d] = per_day.get(d, 0) + 1
    best_day = max(per_day.items(), key=lambda item: (item[1], item[0])) if per_day else None
    return {
        'week_start': start,
        'completed': len(week),
        'xp': sum(quest_xp(q) for q, _ in week),
        'previous_completed': len(last_week),
        'delta': len(week) - len(last_week),
        'active_days': len(per_day),
        'per_pillar': dict(sorted(per_pillar.items(), key=lambda item: (-item[1], item[0]))),
        'best_day': best_day,
    }


CSV_COLUMNS = ['completed_on', 'pillar', 'quest', 'xp', 'feedback']


def _safe_cell(value):
    """Stop spreadsheet apps from running a cell as a formula (CSV injection)."""
    text = '' if value is None else str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


def completed_csv(rows):
    """All completed quests, newest first, as CSV text."""
    import csv
    import io
    finished = sorted([q for q in rows if q.get('status') == 'completed'],
                      key=lambda q: q.get('completed_at') or '', reverse=True)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for q in finished:
        day = _completed_day(q)
        writer.writerow([_safe_cell(day.isoformat() if day else ''), _safe_cell(q.get('category')),
                         _safe_cell(clean_title(q.get('title', ''), q.get('target'))), quest_xp(q),
                         _safe_cell(q.get('feedback') or '')])
    return buffer.getvalue()
