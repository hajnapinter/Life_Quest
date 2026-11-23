"""Evidence-based feedback from recorded completions, never inferred life outcomes."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from personalization import LANGUAGE_NAMES, tr

HABITS={
 'steps':('Walking','Caminhadas','Marche','Spazierengehen'),
 'new_sport':('Trying sports','Novos desportos','Découverte de sports','Neue Sportarten'),
 'mobility':('Mobility','Mobilidade','Mobilité','Beweglichkeit'),
 'strength':('Strength practice','Exercícios de força','Renforcement','Kraftübungen'),
 'yoga':('Yoga','Yoga','Yoga','Yoga'),
 'spending_log':('Expense tracking','Registo de despesas','Suivi des dépenses','Ausgabenübersicht'),
 'financial_learning':('Financial learning','Aprendizagem financeira','Éducation financière','Finanzwissen'),
 'budget':('Budgeting','Orçamento','Budget','Budgetplanung'),
 'money_review':('Reviewing payments','Revisão de pagamentos','Suivi des paiements','Zahlungen prüfen'),
 'saving_goal':('Savings planning','Planear poupanças','Épargne','Sparplanung'),
 'vocabulary':('Vocabulary','Vocabulário','Vocabulaire','Wortschatz'),
 'listening':('Language listening','Compreensão oral','Écoute d’une langue','Hörverständnis'),
 'speaking':('Language speaking','Expressão oral','Expression orale','Sprechen üben'),
 'writing':('Language writing','Escrita numa língua','Expression écrite','Schreiben üben'),
 'reading':('Language reading','Leitura numa língua','Lecture d’une langue','Lesen üben'),
 'nonfiction':('Nonfiction reading','Leitura de não ficção','Lecture documentaire','Sachbücher lesen'),
 'new_hobby':('Creative hobbies','Passatempos criativos','Loisirs créatifs','Kreative Hobbys'),
 'public_speaking':('Speaking practice','Prática de apresentações','Prise de parole','Vorträge üben'),
 'planning':('Personal planning','Planeamento pessoal','Organisation personnelle','Persönliche Planung'),
 'focused_learning':('Learning skills','Aprender competências','Apprentissage','Fähigkeiten lernen'),
 'reconnect':('Keeping in touch','Manter contacto','Prendre des nouvelles','Kontakt halten'),
 'kindness':('Kindness','Gentileza','Bienveillance','Freundlichkeit'),
 'new_conversation':('New conversations','Novas conversas','Nouvelles conversations','Neue Gespräche'),
 'make_plans':('Making plans with friends','Planos com amigos','Projets entre amis','Treffen planen'),
 'listen':('Attentive conversations','Conversas com atenção','Écoute attentive','Aufmerksam zuhören'),
 'new_place':('Exploring places','Explorar lugares','Exploration','Orte entdecken'),
 'new_route':('Discovering routes','Descobrir percursos','Nouveaux itinéraires','Neue Wege'),
 'local_event':('Community activities','Atividades comunitárias','Activités locales','Lokale Aktivitäten'),
 'new_experience':('Cooking discoveries','Descobertas na cozinha','Découvertes culinaires','Neues kochen'),
 'nature':('Connecting with nature','Contacto com a natureza','Lien avec la nature','Natur erleben'),
 'sleep_routine':('Bedtime routine','Rotina de sono','Routine du soir','Abendroutine'),
 'screen_break':('Screen-free time','Tempo sem ecrãs','Temps sans écran','Bildschirmfreie Zeit'),
 'meal_planning':('Meal planning','Planear refeições','Planification des repas','Mahlzeiten planen'),
 'rest':('Making time to rest','Tempo para descansar','Temps de repos','Zeit für Ruhe'),
 'daily_routine':('Everyday routines','Rotinas diárias','Routines quotidiennes','Alltagsroutinen'),
}


def completion_day(row):
    if row.get('status')!='completed' or not row.get('counts_as_quest',True):
        return None
    try:
        value=datetime.fromisoformat(row['completed_at'].replace('Z','+00:00'))
        return value.astimezone(timezone.utc).date() if value.tzinfo else value.date()
    except (ValueError,TypeError,KeyError,AttributeError):
        return None


def insight_facts(rows,today=None):
    today=today or datetime.now(timezone.utc).date()
    monday=today-timedelta(days=today.weekday())
    done=[(q,completion_day(q)) for q in rows]
    week=[(q,d) for q,d in done if d and monday<=d<=today]
    previous=[q for q,d in done if d and monday-timedelta(days=7)<=d<=today-timedelta(days=7)]
    groups={}
    for q,d in week:
        if q.get('focus') not in HABITS:
            continue
        context=q.get('context') if isinstance(q.get('context'),dict) else {}
        goal=context.get('target_language') if q.get('category')=='Languages' else None
        key=(q.get('category'),q['focus'],goal)
        group=groups.setdefault(key,{'focus':q['focus'],'goal':goal,'count':0,'days':set()})
        group['count']+=1;group['days'].add(d)
    best=max(groups.values(),key=lambda g:(len(g['days']),g['count'],g['focus'])) if groups else None
    return {'count':len(week),'days':len({d for _,d in week}),'previous':len(previous),
            'best':best,'pillars':len({q.get('category') for q,_ in week if q.get('category')})}


def insight_messages(rows,language='en',today=None):
    f=insight_facts(rows,today)
    if not f['count']:
        return [tr(('Your first completed quest this week will give us something real to reflect on.',
                    'A primeira missão concluída esta semana vai dar-nos algo concreto para analisar.',
                    'Ta première quête terminée cette semaine nous donnera un progrès concret à commenter.',
                    'Deine erste abgeschlossene Quest diese Woche liefert eine echte Grundlage für Feedback.'),language)]
    messages=[];best=f['best']
    if best:
        label=tr(HABITS[best['focus']],language)
        if best['goal'] in LANGUAGE_NAMES:
            label+=' · '+tr(LANGUAGE_NAMES[best['goal']],language)
        count=best['count'];days=len(best['days'])
        quest_word=tr(('completed quest','missão concluída','quête terminée','abgeschlossene Quest') if count==1 else
                      ('completed quests','missões concluídas','quêtes terminées','abgeschlossene Quests'),language)
        day_word=tr(('day','dia','jour','Tag') if days==1 else ('days','dias','jours','Tagen'),language)
        messages.append(tr(('{label}: {count} {quests} across {days} {day_word} this week.',
                            '{label}: {count} {quests} em {days} {day_word} esta semana.',
                            '{label} : {count} {quests} sur {days} {day_word} cette semaine.',
                            '{label}: {count} {quests} an {days} {day_word} diese Woche.'),language).format(label=label,count=count,quests=quest_word,days=days,day_word=day_word))
        if days>=2:
            messages[-1]+=' '+tr(('You came back on multiple days — keep this rhythm.',
                                   'Voltaste em vários dias — mantém este ritmo.',
                                   'Tu es revenu plusieurs jours — garde ce rythme.',
                                   'Du bist an mehreren Tagen zurückgekommen — bleib bei diesem Rhythmus.'),language)
    if f['previous'] and f['count']>f['previous']:
        messages.append(tr(('You completed {count} quests, compared with {previous} by the same point last week.',
                            'Concluíste {count} missões, face a {previous} até ao mesmo dia da semana passada.',
                            'Tu as terminé {count} quêtes, contre {previous} au même stade la semaine dernière.',
                            'Du hast {count} Quests abgeschlossen, gegenüber {previous} bis zum gleichen Wochentag letzte Woche.'),language).format(**f))
    if f['pillars']>=2:
        messages.append(tr(('You made time for {pillars} different life areas this week.',
                            'Dedicaste tempo a {pillars} áreas diferentes esta semana.',
                            'Tu as consacré du temps à {pillars} domaines différents cette semaine.',
                            'Du hast diese Woche {pillars} verschiedenen Lebensbereichen Zeit gewidmet.'),language).format(**f))
    if not messages:
        messages.append(tr(('You recorded {count} completed quests across {days} days this week.',
                            'Registaste {count} missões concluídas em {days} dias esta semana.',
                            'Tu as enregistré {count} quêtes terminées sur {days} jours cette semaine.',
                            'Du hast diese Woche {count} abgeschlossene Quests an {days} Tagen erfasst.'),language).format(**f))
    return messages[:3]


def render_insights(rows,language):
    import streamlit as st
    with st.container(key='card_personal_insights'):
        st.subheader(tr(('Your progress, in words','O teu progresso em palavras','Tes progrès en mots','Dein Fortschritt in Worten'),language))
        for message in insight_messages(rows,language):
            st.text(message)
        st.caption(tr(('Based on quests you marked complete this week (UTC).',
                       'Com base nas missões que marcaste como concluídas esta semana (UTC).',
                       'D’après les quêtes que tu as cochées cette semaine (UTC).',
                       'Basierend auf deinen als erledigt markierten Quests dieser Woche (UTC).'),language))
