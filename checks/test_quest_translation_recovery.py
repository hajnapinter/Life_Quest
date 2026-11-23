"""Regression checks for unnecessary translation and partial provider failures."""
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
import ai_quests
import quest_display
from quest_plan import slot_plan
from test_workflows import backend, ready_user, log_in


@pytest.fixture
def display(monkeypatch):
    warnings = []
    state = {'language': 'en'}
    monkeypatch.setattr(quest_display, 'st', SimpleNamespace(
        session_state=state, secrets={}, warning=warnings.append))
    monkeypatch.setattr(quest_display, 'known_translation', lambda text, language: None)
    return state, warnings


@pytest.mark.parametrize('language', ['en', 'pt', 'fr', 'de'])
def test_same_source_language_does_not_call_ai(display, monkeypatch, language):
    state, warnings = display
    state['language'] = language
    def unexpected(*args):
        pytest.fail('A quest already in this language must not call AI')
    monkeypatch.setattr(quest_display, '_translate', unexpected)
    assert quest_display.quest_texts(['Original title'], [language]) == ['Original title']
    assert warnings == []


@pytest.mark.parametrize('title', [
    'Explore a new place nearby', 'Try a beginner yoga class',
    'Learn 15 Japanese words', 'Read 10 nonfiction pages',
])
def test_legacy_english_titles_work_offline(display, monkeypatch, title):
    monkeypatch.setattr(quest_display, '_translate', lambda *args: pytest.fail('No translation needed'))
    assert quest_display.quest_text(title) == title
    assert display[1] == []


@pytest.mark.parametrize('original', [
    'Explore un nouveau parc', 'Explore a sua cidade', 'Prepare 3 refeições',
])
def test_legacy_foreign_title_is_not_assumed_to_be_english(display, monkeypatch, original):
    calls = []
    def translate(texts, language, key):
        calls.append((texts, language))
        return ['Explore a new park']
    monkeypatch.setattr(quest_display, '_translate', translate)
    assert quest_display.quest_text(original) == 'Explore a new park'
    assert len(calls) == 1


def test_language_switch_uses_translation_and_successful_cache(display, monkeypatch):
    state, warnings = display
    calls = []
    monkeypatch.setattr(quest_display, '_translate', lambda *args: calls.append(args) or ['Lis 10 pages'])
    state['language'] = 'fr'
    assert quest_display.quest_texts(['Read 10 pages'], ['en']) == ['Lis 10 pages']
    assert quest_display.quest_texts(['Read 10 pages'], ['en']) == ['Lis 10 pages']
    state['language'] = 'en'
    assert quest_display.quest_texts(['Read 10 pages'], ['en']) == ['Read 10 pages']
    assert len(calls) == 1 and not warnings


def test_partial_success_survives_failure_and_other_rows_respect_cooldown(display, monkeypatch):
    state, warnings = display
    state['language'] = 'de'
    calls = []
    now = [100.0]
    monkeypatch.setattr(quest_display.time, 'monotonic', lambda: now[0])
    def translate(texts, language, key):
        calls.append(texts)
        if len(calls) == 2:
            raise ai_quests.QuestGenerationError('offline')
        return ['DE ' + text for text in texts]
    monkeypatch.setattr(quest_display, '_translate', translate)
    texts = ['Task ' + str(n) for n in range(21)]
    assert quest_display.quest_texts(texts) == ['DE ' + text for text in texts[:20]] + [texts[20]]
    assert quest_display.quest_text('Other task') == 'Other task'
    assert len(calls) == 2 and warnings
    now[0] += 61
    assert quest_display.quest_text('Other task') == 'DE Other task'
    assert len(calls) == 3


@pytest.mark.parametrize('language', ['en', 'pt', 'fr', 'de'])
def test_generated_quests_store_server_owned_language(monkeypatch, language):
    responses = [
        {'data': [{'id': ai_quests.FREE_MODEL, 'input_price': 0, 'output_price': 0}]},
        {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps({'quests': [
            {'slot': 1, 'title': 'Walk 2,000 steps today', 'description': 'Walk comfortably.',
             'minutes': 20, 'context': {'text_language': 'wrong'}}]})}}]},
    ]
    monkeypatch.setattr(ai_quests, 'urlopen', lambda *args, **kwargs:
                        io.BytesIO(json.dumps(responses.pop(0)).encode()))
    plan = slot_plan('Fitness', 1, 1, [])
    plan['context'] = {'variant': 1, 'variety_version': 1}
    quest = ai_quests.generate_slot_quests('fixture', [plan], [], language)[0]
    assert quest['context'] == {'variant': 1, 'variety_version': 1, 'text_language': language}
    assert quest['target'] == plan['target'] and quest['difficulty'] == plan['difficulty']
    assert 'text_language' not in plan['context']


def test_english_home_displays_legacy_ai_quest_offline_without_warning(backend, monkeypatch):
    ready_user(backend, 'translation-check@example.com', categories=('Fitness',))
    app = log_in('translation-check@example.com')
    quest = backend.quests[0]
    quest.update(title='Try a beginner yoga class', source='ai', context={})
    monkeypatch.setattr(quest_display, '_translate', lambda *args: pytest.fail('English needs no translation'))
    app.run()
    assert not app.exception
    assert any('Try a beginner yoga class' in checkbox.label for checkbox in app.checkbox)
    assert not any('translations are temporarily unavailable' in warning.value for warning in app.warning)
