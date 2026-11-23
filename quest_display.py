"""Localize stored quest text without modifying tasks, progress or shared data."""
import os
import re
import time
import streamlit as st
from ai_quests import translate_quest_texts, QuestGenerationError
from quest_languages import known_translation


@st.cache_data(ttl=3600, max_entries=512, show_spinner=False)
def _translate(texts, language, _api_key):
    # Cache only successful translations; failures can be retried after a short cooldown.
    return translate_quest_texts(_api_key, list(texts), language)


def _legacy_english(text):
    """Recognise common English quest openings in old rows without language metadata.

    Do not assume that every unknown title is English: older AI rows can be in
    any of the four languages. Ambiguous verbs require an English determiner.
    """
    return bool(re.match(
        r'^(?:(?:walk|try|learn|read|listen|watch|write|speak|practise|practice|'
        r'track|cook|call|meet|join|stretch|drink|declutter|volunteer)\b|'
        r'(?:explore|take|make|start|invite|visit|save|plan|organise|organize|'
        r'create|review|find|spend|do|give|ask|prepare|discover)\s+'
        r'(?:an|the|your|some|one|new|nearby|a\s+'
        r'(?:new|nearby|different|beginner|local|free|friend|hobby|book|meal))\b)', text, re.I))


def quest_texts(texts, source_languages=None):
    language = st.session_state.get('language', 'en')
    source_languages = source_languages if source_languages is not None else [None] * len(texts)
    if len(source_languages) != len(texts):
        raise ValueError('Each quest text needs a source language entry.')
    output = [known_translation(text, language) for text in texts]
    output = [text if value is None and (source == language or
              (source is None and language == 'en' and _legacy_english(text))) else value
              for text, value, source in zip(texts, output, source_languages)]
    saved = st.session_state.setdefault('quest_text_translations', {})
    output = [value if value is not None else saved.get((language, text))
              for text, value in zip(texts, output)]
    missing = list(dict.fromkeys(text for text, translated in zip(texts, output) if translated is None and text))
    if missing:
        try:
            config = st.secrets.get('requesty', {})
        except FileNotFoundError:
            config = {}
        key = os.environ.get('REQUESTY_API_KEY') or config.get('api_key', '')
        # A provider outage should not trigger a separate failed call per pillar/row.
        retry_key = ('quest_translation_retry', language)
        retries = st.session_state.setdefault('quest_translation_retries', {})
        lookup = {}
        try:
            if time.monotonic() < retries.get(retry_key, 0):
                raise QuestGenerationError('cooldown')
            for offset in range(0, len(missing), 20):
                batch = missing[offset:offset + 20]
                translated = _translate(tuple(batch), language, key)
                lookup.update(zip(batch, translated))
                saved.update({(language, text): value for text, value in zip(batch, translated)})
        except QuestGenerationError:
            if time.monotonic() >= retries.get(retry_key, 0):
                retries[retry_key] = time.monotonic() + 60
            st.warning({
                'en':'Some AI quest translations are temporarily unavailable. Their original text is shown; your tasks and progress are unchanged.',
                'pt':'Algumas traduções das missões de IA estão temporariamente indisponíveis. Vês o texto original; as tarefas e o progresso mantêm-se.',
                'fr':'Certaines traductions des quêtes IA sont temporairement indisponibles. Le texte original reste affiché ; tes tâches et tes progrès sont conservés.',
                'de':'Einige Übersetzungen der KI-Quests sind vorübergehend nicht verfügbar. Der Originaltext bleibt sichtbar; Aufgaben und Fortschritt bleiben erhalten.',
            }.get(language, 'Quest translation is temporarily unavailable.'))
        # Keep earlier successful batches even when a later batch fails.
        output = [translated if translated is not None else lookup.get(text, text)
                  for text, translated in zip(texts, output)]
    return [translated if translated is not None else text for text, translated in zip(texts, output)]


def quest_text(text):
    return quest_texts([text])[0]
