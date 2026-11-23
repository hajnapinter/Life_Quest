"""First-run questionnaire; account metadata stores answers across devices."""
import streamlit as st
from design import hero
from places import city_picker
from profile_data import pillar_limit
from i18n import language_picker
from onboarding_text import ob, pillar_text
from personalization import render_preference_fields

PILLARS = {
    'Adventure': ('🌍', 'Explore more', 'New places, fresh experiences, little adventures.', ['I usually stick to familiar places', 'I try something new a few times a year', 'I explore somewhere new every month', 'I seek new experiences most weeks', 'Exploring is already part of my everyday life']),
    'Finance': ('💰', 'Build money confidence', 'Small saving habits and financial understanding.', ['I am just starting to understand my spending', 'I track some of my expenses', 'I have a budget but find consistency difficult', 'I budget and save regularly', 'I have clear goals and review my finances regularly']),
    'Fitness': ('💪', 'Move with confidence', 'Enjoy movement and build a sustainable routine.', ['I do very little intentional movement', 'I move occasionally and want a gentle start', 'I am active one or two days a week', 'I exercise regularly most weeks', 'I have a consistent routine and want variety']),
    'Health': ('🌿', 'Feel better every day', 'Rest, everyday wellbeing and mindful habits.', ['My daily routines feel irregular', 'I have one healthy habit I want to build on', 'I manage some routines but often lose consistency', 'My sleep and wellbeing routines are mostly steady', 'I have steady routines and want to refine them']),
    'Languages': ('💬', 'Find new words', 'Learn, practise and connect through language.', ['I am starting from my first words', 'I know basic words and simple phrases', 'I can handle short everyday conversations', 'I can discuss familiar topics comfortably', 'I communicate confidently and want more nuance']),
    'Personal Growth': ('🧠', 'Grow your curiosity', 'Learning, reflection and meaningful personal goals.', ['I am not sure where to start', 'I occasionally read, learn or reflect', 'I make time for learning about once a week', 'I regularly learn and act on personal goals', 'I have a steady learning routine and seek deeper challenges']),
    'Social': ('❤️', 'Feel more connected', 'Strengthen friendships and meet people at your pace.', ['I prefer very small, familiar interactions', 'I want to reconnect with people I already know', 'I am comfortable one-to-one but rarely initiate', 'I often make plans and meet new people', 'I confidently bring people together']),
}


# How many of the five ready quests to show per pillar (a lighter view, not a target).
QUESTS_SHOWN = {
    1: 'Just one · keep it simple',
    2: 'Two at a time',
    3: 'Three · a light list',
    5: 'All five · show me everything',
}
DEFAULT_QUESTS_SHOWN = 5


def render_onboarding(save):
    with st.container(key='onboarding'):
        _render_onboarding(save)


def _render_onboarding(save):
    user_id = st.session_state.user['id']
    if st.session_state.get('onboarding_owner') != user_id:
        for key in list(st.session_state):
            if key.startswith('ob_') and key != 'ob_back':
                del st.session_state[key]
        st.session_state.onboarding_owner = user_id
    # Keep answers when their widgets are absent on the next step.
    for key in list(st.session_state):
        if key.startswith('ob_') and key != 'ob_back':
            st.session_state[key] = st.session_state[key]
    st.session_state.setdefault('ob_step', 0)
    step = st.session_state.ob_step
    chosen = [p for p in PILLARS if st.session_state.get('ob_pick_' + p, False)]
    total = 5 + len(chosen)
    top_left, top_right = st.columns([3, 1], vertical_alignment="center")
    top_left.markdown(f'<div class="lq-eyebrow">{ob("eyebrow")}</div>', unsafe_allow_html=True)
    with top_right:
        language_picker('onboarding_language')
    st.progress(min((step + 1) / total, 1))
    st.caption(ob('step', a=step + 1, b=total) if step >= 3 else ob('intro'))
    if step == 0:
        st.title(ob('name_title'))
        st.write(ob('name_text'))
        with st.form('nickname'):
            nickname = st.text_input(ob('name_label'), value=st.session_state.get('ob_name',''), max_chars=30,
                                     placeholder=ob('name_placeholder'))
            submitted = st.form_submit_button(ob('name_button'), type='primary', use_container_width=True)
        if submitted:
            if not nickname.strip():
                st.error(ob('name_error'))
            else:
                st.session_state.ob_name = nickname.strip()
                advance(1)
    elif step == 1:
        hero(ob('hi_tag'), ob('hi_title', name=st.session_state.ob_name), ob('hi_body'))
        if st.button(ob('hi_button'), type='primary', use_container_width=True):
            advance(2)
    elif step == 2:
        st.title(ob('pillars_title'))
        limit = pillar_limit()
        st.write(ob('pillars_limit', n=limit) if limit < len(PILLARS) else ob('pillars_any'))
        items = list(PILLARS.items())
        full = len(chosen) >= limit
        for start in range(0, len(items), 2):
            for column, (pillar, english) in zip(st.columns(2), items[start:start + 2]):
                name, tagline, _, _ = pillar_text(pillar, english)
                with column, st.container(key='pickcard_' + pillar.replace(' ', '_').lower()):
                    picked = st.session_state.get('ob_pick_' + pillar, False)
                    st.checkbox(f'{english[0]}  **{name}**', key='ob_pick_' + pillar, disabled=full and not picked)
                    st.caption(tagline)
        chosen = [p for p in PILLARS if st.session_state.get('ob_pick_' + p)][:limit]
        if st.button(ob('pillars_button'), type='primary', disabled=not chosen, use_container_width=True):
            st.session_state.ob_categories = chosen
            advance(3)
    elif step < 3 + len(st.session_state.ob_categories):
        pillar = st.session_state.ob_categories[step - 3]
        icon, _, _, levels = PILLARS[pillar]
        name, _, _, shown_levels = pillar_text(pillar, PILLARS[pillar])
        st.caption(f'{icon}  {name.upper()}')
        st.title(ob('level_title'))
        st.write(ob('level_text'))
        # Options stay in English (they are stored and mapped to a level by position); only the labels change.
        answer = st.radio(ob('level_label'), levels, index=None, key='ob_level_' + pillar, label_visibility='collapsed',
                          format_func=lambda option: shown_levels[levels.index(option)])
        if st.button(ob('continue'), type='primary', disabled=answer is None, use_container_width=True):
            advance(step + 1)
    elif step == 3 + len(st.session_state.ob_categories):
        st.title(ob('shown_title'))
        st.write(ob('shown_text'))
        st.session_state.setdefault('ob_shown', DEFAULT_QUESTS_SHOWN)
        st.radio(ob('shown_label'), list(QUESTS_SHOWN), key='ob_shown',
                 format_func=lambda n: ob(f'shown_{n}'), label_visibility='collapsed')
        if st.button(ob('continue'), type='primary', use_container_width=True):
            advance(step + 1)
    else:
        st.title(ob('final_title'))
        st.write(ob('final_text'))
        categories = st.session_state.ob_categories
        for p in categories:
            level = PILLARS[p][3].index(st.session_state['ob_level_' + p]) + 1
            st.write(f'{PILLARS[p][0]} **{pillar_text(p, PILLARS[p])[0]}** · {ob("final_level", level=level)}')
        shown = st.session_state.get('ob_shown', DEFAULT_QUESTS_SHOWN)
        st.write(f'👀 **{ob("final_shown")}** · {ob("final_per", n=shown)}')
        place = city_picker('ob_city', st.session_state.get('ob_location_label', ''), label=ob('city_label'),
                            placeholder=ob('city_placeholder'), none_found=ob('city_none'), unavailable=ob('city_down'))
        if place:
            st.session_state.ob_location_label = place['label']
        location = st.session_state.get('ob_location_label', '')
        if location:
            st.write(f'📍 **{location}**')
        st.caption(ob('city_note'))
        st.caption(ob('ai_note'))
        preferences=render_preference_fields(st.session_state.get('ob_preferences',{}),'ob_preferences',st.session_state.get('language','en'),'Languages' in categories)
        st.session_state.ob_preferences=preferences
        if st.button(ob('prepare'), type='primary', use_container_width=True,
                     disabled='Languages' in categories and not preferences['target_language']):
            with st.status(ob('preparing'), expanded=True) as status:
                st.write(ob('saving'))
                levels = {p: PILLARS[p][3].index(st.session_state['ob_level_' + p]) + 1 for p in categories}
                if save(st.session_state.ob_name, location, categories, levels, {p: shown for p in categories}):
                    status.update(label=ob('ready'), state='complete')
                    st.rerun()
                else:
                    status.update(label=ob('failed'), state='error')
    if step > 0 and st.button(ob('back'), key='ob_back'):
        advance(step - 1)


def advance(step):
    st.session_state.ob_step = step
    st.rerun()
