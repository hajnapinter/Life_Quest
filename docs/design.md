# Life Quest design system

> **For everyone working on the UI, people and AI assistants alike** (Claude Code, ChatGPT / Codex, Copilot, …).
> Read this before you add or change any screen, widget, colour, font, card, chart or CSS.
> Using ChatGPT in the browser? Paste this file into the chat (or add it to your ChatGPT Project) first.

Life Quest turns everyday self-improvement into small quests. The look is **Warm glow**: friendly and encouraging like a wellbeing app, with soft peach gradients, white rounded cards on a warm off-white page, a little sprout character, and **Inter Tight** type (big *light* headings, semi-bold section titles).

Precedence: what the team asks for in the current task wins, then this file, then your own taste.

## Where styling lives (do not scatter it)

| What | File |
|---|---|
| Colours, fonts, corner rounding, chart palettes | `.streamlit/config.toml` (`[theme]`) |
| All custom CSS + HTML helpers + pillar colours | `design.py` |
| Google sign-in button (runs in its own iframe) | `auth_component/index.html` |

- `app.py` calls `apply_styles()` once, right after `st.set_page_config`. Never add another `<style>` block in a screen file. If something needs new CSS, add it to `_CSS` in `design.py`.
- If you change a colour, change it in **both** `config.toml` and the constants at the top of `design.py`.
- Theme changes in `config.toml` need an app restart; changes to `.py` files hot-reload.

## Tokens

| Token | Value | Use |
|---|---|---|
| Page | `#FFF9F4` | app background |
| Surface | `#FFFFFF` | cards, quest rows, tiles, inputs, nav bar |
| Ink | `#2B2330` | all body text and headings |
| Muted | `#7A6E7E` | captions, eyebrows, secondary labels |
| Action | `#BF4A1A` | `primaryColor`: primary buttons, checkboxes, toggles, keyboard focus outlines. White text on it is 4.99:1 (passes WCAG AA for normal text). It replaced `#D4551F` (only 4.10:1). Don't lighten it below 4.5:1 with white. |
| Glow | `#FF8A4C` | bright orange for fills, highlights, shadows. **Never** as a text colour or as a button background with white text (fails contrast). |
| Growth | `#7CC394` | the sprout, success moments |
| Line | `#F1E4DA` | hairline borders on inputs and tables |

Hero gradients (`design.HERO_GRADIENTS`): `peach` (default), `lilac`, `mint`. Text on gradients is always Ink, never white.

### Pillar colours (`design.PILLAR_COLORS`)

Each pillar has a soft background (icon tiles) and a strong colour (heatmap fill):
Adventure blue `#DDEEFB/#5B9FD6` · Finance yellow `#FFF1C9/#D9A521` · Fitness peach `#FFE3D1/#FF8A4C` · Health mint `#DDF2E3/#4FAA72` · Languages lilac `#E7E3FA/#8A78E0` · Personal Growth pink `#F9E1EC/#D9739F` · Social rose `#FFE0E0/#E86A6A`.
A new pillar must get an entry here; otherwise it falls back to peach.

## Type

- Font: Inter Tight everywhere (set in `config.toml`; also loaded in the Google button iframe).
- `st.title` (h1): weight **300**, 2.6rem, tight letter-spacing. Exactly one main heading per screen; on Home it is the name in `greeting()` (marked `role="heading" aria-level="1"`), so Home has no `st.title`.
- `st.subheader` / h2–h3: weight 600.
- Eyebrow labels above titles: `<div class="lq-eyebrow">…</div>` (small caps-spaced uppercase, muted). Use these, not `st.caption("ALL CAPS · TEXT")`.
- Running text: sentence case, short, encouraging, second person ("Pick what fits today").

## Shape and depth

- Corners: base `1rem`; cards 18–22px; hero 28px; buttons and pills fully round (`buttonRadius = "full"`).
- Depth comes from soft plum shadows (`0 8px 22px -16px rgba(43,35,48,.45)`), not borders. White cards sit on the off-white page with no outline.
- Do not give every block a card. Cards are for: quest rows, stat tiles (`st.metric`), expanders, forms, the heatmap, the hero.

## Components (use the helpers in `design.py`)

| Need | Use |
|---|---|
| Screen greeting with avatar, name and XP | `greeting(hello, name, xp, photo, ring)` |
| One focus card per screen (gradient + sprout) | `hero(tag, title, body, variant="peach", sprout=True)`; **max one per screen** |
| Pillar section header | `pillar_header(category, icon, label, caption)` |
| Activity over time for a pillar | `heatmap(category, activity, title, less, more, weekdays)`; replaces bar charts |
| Stats | `st.metric` in `st.container(key="stat_row_<name>").columns(2–3)`; white tiles that stay side by side on phones (the change vs last week is hidden there) |
| A quest the user can tick | `st.checkbox` inside `st.container(key="quest_row_<id>")`; the key prefix gives the card style and the "completed" animation |
| Main navigation | Squad and ⚔️ Competition are separate pages; Squad contains shared quests and its ranking, Competition contains daily 1v1 challenges. Use the `st.radio` inside `st.container(key="bottom_navigation")`; a white pill floating at the bottom on phones, sticky at the top on desktop; the selected item is a light peach pill. On phones the pill sits 56px above the bottom edge so the hosting platform's bottom-right controls (Streamlit Community Cloud) never cover it; the page has matching bottom padding |
| Onboarding choice cards | widgets inside the `onboarding` keyed container get card styling automatically; multi-select options go in a 2-column grid of `st.container(key="pickcard_<name>")` cards (checkbox + caption, no dashes in labels) |
| A white card around a group of widgets | `st.container(key="card_<name>")`; any key starting with `card_` gets the card style |
| Weekly ranking | `squad_ranking(rows, me, title)` on the Squad page, for the selected squad only (compact rows, medals for the top 3, the user highlighted). The separate weekly Leaderboard page uses `leaderboard()` with profile avatars and a three-height podium. |
| Profile header | `profile_card(name, line, photo, ring)`: avatar (photo or initials), name, one muted line |
| People in a squad | `member_chips(names)` |
| Logo + "Life Quest" label at the top of a screen | `brand()` (sprout logo `LOGO_SVG`; tilts on hover) |
| Loading screen | `splash()`: the sprout grows, then fades after ~1.5s; `app.py` shows it once per session |
| Quest target changed since last time | `trend_html(direction, previous)` under the checkbox (`.lq-trend.up` green / `.down` orange) |
| Counts per pillar | `pillar_bars(items)`: horizontal bars in each pillar's strong colour (used on the Recap page) |
| Language selector | `i18n.language_picker(key)` (dashboard header and onboarding) |
| Primary call to action | `st.button(..., type="primary")`; at most one primary button per view; `width="stretch"` on narrow forms |

## Motion

The app should feel alive but calm. All motion lives in `design.py`:
- **Entrance:** cards, tiles, podium and hero rise in (`lq-up`, ~0.45s), staggered by a few tens of ms.
- **Hover:** anything clickable or card-like lifts 2–3px with a warm orange shadow; buttons press down (`scale(.97)`) on click; nav items get a peach background; pillar icons tilt.
- **Idle:** only the sprout moves (gentle bob and leaf sway). Nothing else loops.
- Keep durations under 1s (except the splash) and use the existing easing. Every new animation must be switched off by the `prefers-reduced-motion` block (it already disables all animations and transitions globally).

## Quests shown per pillar

Five quests are always kept ready per pillar. Users choose how many to **see** (1–5) per pillar: once in onboarding (`onboarding.QUESTS_SHOWN`, applied to every chosen pillar) and per pillar in Settings. It is a lighter view, not a goal: when one is finished the next ready quest appears. Stored as `quests_shown: {pillar: n}` inside the `lifequest_onboarding` user metadata; read it with `ai_quest_ui.quests_shown(category)` (default 5) and pass it to `render_quest_cards(..., limit=n)`.

## Personalisation and navigation

- All seven pillars and avatar rings are available to everyone. No subscription modes.
- Six main navigation items: Home, Recap, Squad, Competition, Settings, Leaderboard. Labels have no emoji, use dark text and are centered. On narrow phones use two rows of three items. Pillar pages open from Home and its pillar picker. Keep navigation within phone width, without horizontal scrolling.
- `places.py` searches cities via Photon. City, country, target language and preferred session length personalise quests through `personalization.py`; numeric progression stays in `quest_plan.py`.
- Clearly disclose that location and preferences are sent to Requesty for generation; never send names or email addresses.
- Daily opt-in email reminders use the hourly worker. Device notifications remain a test only.

## Profile photo, avatar and device notifications (`account.py`)

- Everyone can upload a profile photo; it is cropped to 80×80 JPEG and stored in auth metadata `lifequest_profile.photo` (no Storage bucket exists). Show avatars with `avatar_html()` / `profile_card(..., photo, ring)` / `greeting(..., photo, ring)`.
- Everyone can choose an avatar ring (`AVATAR_RINGS`: peach, lilac, mint, ocean, gold, sunset).
- "Phone and laptop notifications" saves a preference and asks the browser for permission on this device (test notification). Scheduled delivery while the app is closed would need a push server (not built).

## No loading fade

Streamlit normally dims the page while it reruns after a click. `design.py` turns that off (`[data-stale="true"]`) so choosing an option never flashes. Don't reintroduce full-page loading effects; use `st.spinner` only for real waits (quest generation).

## Rules for new screens

1. Start with an eyebrow + `st.title`, or `greeting()` on Home-like screens.
2. Every user-visible string goes through the existing translation pattern (en / pt / fr / de). Never ship an English-only label.
3. Pillar emoji (`PILLARS[c][0]`) sit inside a coloured icon tile or before a title, never as decoration on random lines.
4. Prefer white rows and tiles over `st.dataframe` for anything the user reads for fun (leaderboards, histories). Tables are fine for long records.
5. Must work at phone width (~390px) **and** on desktop: no fixed widths, no horizontal scrolling including the nav.
   - Desktop (≥960px) widens the page to 1080px and moves the nav to a sticky pill at the top.
   - Use `st.columns` for desktop layouts (Streamlit stacks them on phones): Home shows 2 pillars per row; pillar, Squad and Settings pages use a main column + side column (`[3, 2]` or `2`).
6. Respect `prefers-reduced-motion` for any new animation (see the existing media query).
7. Escape user text (`html.escape`) before putting it into any HTML string.

## Checking your work

Run `uv run streamlit run app.py`, look at the screen at desktop and phone width, then run `uv run pytest` (see AGENTS.md).

## Quest variety, progress feedback and invitations

- `quest_variety.py` provides 84 practical activity variants across the 35 tracks, each in en/pt/fr/de. It changes activity wording only; `slot_plan` owns the unchanged targets, difficulty and progression. Completed history keeps its context snapshot. Append variants instead of reordering them; their recorded indices are part of saved history.
- `progress_insights.py` adds a short factual card to Recap and pillar pages. Use recorded completed quests, exclude XP-only bonuses, and compare only equivalent weekdays. Do not claim a habit is established or infer health/financial outcomes.
- `invitations.py` shows a copyable invitation link using Streamlit's native code-block copy button, plus the original code in an expander. Links contain only invite type and code. Signing in never accepts an invitation automatically; the user must press Accept invitation. Failed, closed or wrong-recipient invitations get a neutral message.

## Multiplayer and progress review

- Competition shows active pair standings and today's score form before rules and invitation controls. Confirmed XP and provisional same-day scores are explicitly distinguished; refresh every 30 seconds.
- Squad uses a member-by-quest participation matrix on the left; the member ranking sits in the right desktop column and stacks on phones. Names and status cells must have accessible labels; never rely only on color.
- Habit expanders use broad names from `habit_journey.habit_name`; inside, show recorded first/latest completed targets separately from the next target, a long-term direction and the purpose. Do not change progression.
- Progress reflections use the verified free Requesty model with bounded activity evidence and no identity/location. Failures use a clearly labeled local encouragement, never pretend AI succeeded.
- Settings omits city editing and the personalization form; stored onboarding preferences remain in effect.

Navigation labels use regular weight (400) and soft dark plum (#55444F). Keep the existing bar shadow; tabs themselves have no inset/click shadow, underline or hover lift. Selection is a light peach pill (#FFF1E6), with a quieter hover tint. Keyboard focus shows a 2px Action (`#BF4A1A`) outline, about 5:1 against the white bar, so keyboard users can always see where they are. Never use a pale outline (the old `#E8CFC0` was 1.49:1).

During verified session restoration, hide only the auth form with `.st-key-auth_restoring` and show a translated restoration status. Do not flash a signed-out screen or hide the session component. Connection failures offer retry without discarding credentials.
