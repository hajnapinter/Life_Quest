"""Personalised wording only: never changes a quest's target, difficulty or XP."""
from profile_data import country_of, save_user_data

LANGUAGE_NAMES={
 'en':('English','Inglês','Anglais','Englisch'), 'pt':('Portuguese','Português','Portugais','Portugiesisch'),
 'fr':('French','Francês','Français','Französisch'), 'de':('German','Alemão','Allemand','Deutsch'),
 'es':('Spanish','Espanhol','Espagnol','Spanisch'), 'ja':('Japanese','Japonês','Japonais','Japanisch'),
 'it':('Italian','Italiano','Italien','Italienisch'), 'ko':('Korean','Coreano','Coréen','Koreanisch'),
 'zh':('Chinese','Chinês','Chinois','Chinesisch'), 'ar':('Arabic','Árabe','Arabe','Arabisch')}
CURRENCIES={'Portugal':'EUR','France':'EUR','Germany':'EUR','Spain':'EUR','Italy':'EUR','Netherlands':'EUR',
 'Hungary':'HUF','United Kingdom':'GBP','United States':'USD','Brazil':'BRL','Canada':'CAD','Australia':'AUD','Japan':'JPY'}
CUISINES={'Portugal':('Portuguese','portuguesa','portugaise','portugiesischen'),
 'France':('French','francesa','française','französischen'),'Germany':('German','alemã','allemande','deutschen'),
 'Spain':('Spanish','espanhola','espagnole','spanischen'),'Italy':('Italian','italiana','italienne','italienischen'),
 'Hungary':('Hungarian','húngara','hongroise','ungarischen'),'Japan':('Japanese','japonesa','japonaise','japanischen'),
 'Brazil':('Brazilian','brasileira','brésilienne','brasilianischen')}


def tr(values,language):
    return values[('en','pt','fr','de').index(language) if language in ('en','pt','fr','de') else 0]


def clean_preferences(value):
    value=value if isinstance(value,dict) else {}
    return {'target_language':value.get('target_language') if value.get('target_language') in LANGUAGE_NAMES else '',
            'minutes':value.get('minutes') if type(value.get('minutes')) is int and value['minutes'] in (10,20,30,60) else 20}


def personalize_title(title,quest,preferences,location,language='en',level=1):
    """Local templates remain available when AI or translation providers are down."""
    prefs=clean_preferences(preferences); focus=quest.get('focus'); n=quest.get('target') or 1
    goal=prefs['target_language']
    if quest.get('category')=='Languages' and goal:
        name=tr(LANGUAGE_NAMES[goal],language)
        templates={
         'vocabulary':('Learn {n} new words in {name}','Aprende {n} palavras novas em {name}','Apprends {n} nouveaux mots en {name}','Lerne {n} neue Wörter auf {name}'),
         'listening':('Listen to {name} for {n} minutes','Ouve {name} durante {n} minutos','Écoute du {name} pendant {n} minutes','Höre {n} Minuten etwas auf {name}'),
         'speaking':('Speak {name} aloud for {n} minutes','Fala {name} em voz alta durante {n} minutos','Parle {name} à voix haute pendant {n} minutes','Sprich {n} Minuten laut auf {name}'),
         'writing':('Write {n} sentences in {name}','Escreve {n} frases em {name}','Écris {n} phrases en {name}','Schreibe {n} Sätze auf {name}'),
         'reading':('Read in {name} for {n} minutes','Lê em {name} durante {n} minutos','Lis en {name} pendant {n} minutes','Lies {n} Minuten auf {name}')}
        if focus in templates:
            return tr(templates[focus],language).format(n=n,name=name)
    country=country_of(location); city=(location or '').split(',')[0].strip()
    if country and city and ',' in (location or ''):
        if focus=='new_place':
            return tr(('Explore a new public place in {city}','Explora um lugar público novo em {city}',
                       'Explore un nouveau lieu public à {city}','Entdecke einen neuen öffentlichen Ort in {city}'),language).format(city=city)
        if focus=='local_event':
            return tr(('Find a free community event in {city}','Encontra um evento comunitário gratuito em {city}',
                       'Trouve un événement associatif gratuit à {city}','Finde eine kostenlose Gemeinschaftsveranstaltung in {city}'),language).format(city=city)
        if focus=='new_experience' and country in CUISINES:
            cuisine=tr(CUISINES[country],language)
            return tr(('Try a new {cuisine} recipe','Experimenta uma receita {cuisine} nova',
                       'Essaie une nouvelle recette {cuisine}','Probiere ein neues Rezept aus der {cuisine} Küche'),language).format(cuisine=cuisine)
        if focus=='spending_log' and country in CURRENCIES:
            return tr(('Track {n} expenses in {currency}','Regista {n} despesas em {currency}',
                       'Note {n} dépenses en {currency}','Erfasse {n} Ausgaben in {currency}'),language).format(n=n,currency=CURRENCIES[country])
    if focus=='strength' and level>=4:
        return tr(('Do a {n}-minute strength session at your level','Faz uma sessão de força de {n} minutos adequada ao teu nível',
                   'Fais une séance de renforcement de {n} minutes à ton niveau','Mache {n} Minuten Krafttraining auf deinem Niveau'),language).format(n=n)
    return title


def render_preference_fields(preferences,key,language,has_languages=False):
    import streamlit as st
    prefs=clean_preferences(preferences)
    options=['',*LANGUAGE_NAMES]
    goal=st.selectbox(tr(('Language you want to learn','Língua que queres aprender','Langue que tu veux apprendre','Sprache, die du lernen möchtest'),language),
                      options,index=options.index(prefs['target_language']),key=key+'_target_language',
                      format_func=lambda code:tr(LANGUAGE_NAMES[code],language) if code else tr(('Choose a language','Escolhe uma língua','Choisis une langue','Wähle eine Sprache'),language)) if has_languages else prefs['target_language']
    # Session length is no longer asked: it never changed a quest. The stored value (default 20) is kept.
    return {'target_language':goal,'minutes':prefs['minutes']}


def render_preferences(api,language):
    import streamlit as st
    user=st.session_state.user
    current=clean_preferences(user.get('user_metadata',{}).get('lifequest_preferences'))
    st.subheader(tr(('Make quests yours','Missões à tua medida','Des quêtes pour toi','Quests für dich'),language))
    with st.form('quest_preferences'):
        chosen=render_preference_fields(current,'preferences',language,'Languages' in st.session_state.profile.get('selected_categories',[]))
        save=st.form_submit_button(tr(('Save preferences','Guardar preferências','Enregistrer mes préférences','Vorlieben speichern'),language))
    if save:
        error=save_user_data(api,{'lifequest_preferences':chosen})
        if error:
            st.error(tr(('Could not save preferences. Please retry.','Não foi possível guardar. Tenta novamente.','Impossible d’enregistrer. Réessaie.','Speichern fehlgeschlagen. Bitte versuche es erneut.'),language))
        else:
            st.success(tr(('Preferences saved.','Preferências guardadas.','Préférences enregistrées.','Vorlieben gespeichert.'),language))
