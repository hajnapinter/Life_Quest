"""First-run questionnaire; account metadata stores answers across devices."""
import streamlit as st
from design import hero
from places import city_picker
from pro import pillar_limit

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
    st.markdown('<div class="lq-eyebrow">Life Quest · Your fresh start</div>', unsafe_allow_html=True)
    st.progress(min((step + 1) / total, 1))
    st.caption(f'Step {step + 1} of {total}' if step >= 3 else 'A few small questions. A journey that feels like you.')
    if step == 0:
        st.title('First, what should we call you?')
        st.write('Your name, your nickname — whatever feels like you.')
        with st.form('nickname'):
            nickname = st.text_input('Your nickname', value=st.session_state.get('ob_name',''), max_chars=30, placeholder='e.g. Hajna')
            submitted = st.form_submit_button('Let’s begin →', type='primary', use_container_width=True)
        if submitted:
            if not nickname.strip():
                st.error('Add a nickname so we know what to call you.')
            else:
                st.session_state.ob_name = nickname.strip()
                advance(1)
    elif step == 1:
        hero('A small step. A new chapter.', f'Hi, {st.session_state.ob_name}!',
             'You don’t need to change everything today. Let’s start with one small quest that feels right for you.')
        if st.button('Make it mine →', type='primary', use_container_width=True):
            advance(2)
    elif step == 2:
        st.title('Where would you like to grow?')
        limit = pillar_limit()
        st.write(f'Choose up to {limit} pillars. This is your journey.' if limit < len(PILLARS)
                 else 'Choose as many pillars as you like. This is your journey.')
        items = list(PILLARS.items())
        full = len(chosen) >= limit
        for start in range(0, len(items), 2):
            for column, (pillar, (icon, title, description, _)) in zip(st.columns(2), items[start:start + 2]):
                with column, st.container(key='pickcard_' + pillar.replace(' ', '_').lower()):
                    picked = st.session_state.get('ob_pick_' + pillar, False)
                    st.checkbox(f'{icon}  **{pillar}**', key='ob_pick_' + pillar, disabled=full and not picked)
                    st.caption(title)
        chosen = [p for p in PILLARS if st.session_state.get('ob_pick_' + p)][:limit]
        if full and limit < len(PILLARS):
            st.caption('✨ Want more? Life Quest Pro unlocks all 7 pillars. You can upgrade later in Settings.')
        if st.button('Find my starting point →', type='primary', disabled=not chosen, use_container_width=True):
            st.session_state.ob_categories = chosen
            advance(3)
    elif step < 3 + len(st.session_state.ob_categories):
        pillar = st.session_state.ob_categories[step - 3]
        icon, title, _, levels = PILLARS[pillar]
        st.caption(f'{icon}  {pillar.upper()}')
        st.title('What feels most like you today?')
        st.write('No right answers. We’ll start at your pace, not somebody else’s.')
        answer = st.radio('Your starting point', levels, index=None, key='ob_level_' + pillar, label_visibility='collapsed')
        if st.button('Continue →', type='primary', disabled=answer is None, use_container_width=True):
            advance(step + 1)
    elif step == 3 + len(st.session_state.ob_categories):
        st.title('How many quests should we show?')
        st.write('We always keep five quests ready for each pillar. Pick how many you want to see at once; a new one appears whenever you finish one. You can change this for each pillar in Settings.')
        st.session_state.setdefault('ob_shown', DEFAULT_QUESTS_SHOWN)
        st.radio('Quests shown per pillar', list(QUESTS_SHOWN), key='ob_shown',
                 format_func=lambda n: QUESTS_SHOWN[n], label_visibility='collapsed')
        if st.button('Continue →', type='primary', use_container_width=True):
            advance(step + 1)
    else:
        st.title('Your next chapter is ready to begin ✨')
        st.write('Small steps, chosen around your interests and your starting point.')
        categories = st.session_state.ob_categories
        for p in categories:
            level = PILLARS[p][3].index(st.session_state['ob_level_' + p]) + 1
            st.write(f'{PILLARS[p][0]} **{p}** · Starting point {level}/5')
        shown = st.session_state.get('ob_shown', DEFAULT_QUESTS_SHOWN)
        st.write(f'👀 **Quests shown** · {shown} per pillar')
        place = city_picker('ob_city', st.session_state.get('ob_location_label', ''))
        if place:
            st.session_state.ob_location_label = place['label']
        location = st.session_state.get('ob_location_label', '')
        if location:
            st.write(f'📍 **{location}**')
        st.caption('City search uses OpenStreetMap (Photon): only what you type is sent. Your city is shown on your profile; it does not change your quests.')
        st.caption('When AI quests are enabled, your chosen pillars, starting levels and quest feedback are shared with Requesty and its free model provider to personalise your quests. Your name and email are not sent.')
        if st.button('Prepare my quests →', type='primary', use_container_width=True):
            with st.status('Preparing your personalised quests…', expanded=True) as status:
                st.write('Saving your interests and starting points…')
                levels = {p: PILLARS[p][3].index(st.session_state['ob_level_' + p]) + 1 for p in categories}
                if save(st.session_state.ob_name, location, categories, levels, {p: shown for p in categories}):
                    status.update(label='Your journey is ready!', state='complete')
                    st.rerun()
                else:
                    status.update(label='We couldn’t finish preparing your journey. Please try again.', state='error')
    if step > 0 and st.button('← Back', key='ob_back'):
        advance(step - 1)


def advance(step):
    st.session_state.ob_step = step
    st.rerun()
