# Life Quest

Life Quest turns personal development into a friendly game. You choose the life
areas ("pillars") you want to grow in, get small practical quests that adapt to
your pace, earn XP, and progress together with friends in squads and 1v1
competitions.

[![Tests](https://github.com/hajnapinter/Life_Quest/actions/workflows/tests.yml/badge.svg)](https://github.com/hajnapinter/Life_Quest/actions/workflows/tests.yml)

**Live app: [life-quest-team.streamlit.app](https://life-quest-team.streamlit.app/)**
(Streamlit Community Cloud, deployed from the `main` branch; see [docs/deploy.md](docs/deploy.md)).

## Team

| Name | Student number |
|---|---|
| Catarina Pedro | 71361 |
| Ana Luiza Costa | 81023 |
| Hajna Pintér | 81324 |
| Janka Stolk | 83499 |

## Main features

**Account and onboarding**
- Sign-up and login with a validated email address or Google (PKCE), through Supabase Auth. Confirmation emails can be resent (60-second cooldown) and errors are explained clearly.
- You stay signed in after reloading or reopening the app for up to 30 days. Only a rotating refresh credential is kept in the browser, and Supabase verifies it on every restore. Logging out clears it on every tab.
- Onboarding: nickname, any of the seven pillars, a starting level per pillar, how many quests to show, city/country and target-language preferences.

**Quests and progress**
- Five adaptive quests are kept ready per pillar, shown 1–5 at a time. A target rises after a success and drops after "too hard", within fixed limits; each quest shows when its target changed ("↑ up from 4,000 last time").
- Variety: 84 locally translated practical activity variants across 35 habit tracks. Wording is personalised to your country, city and languages, but targets, difficulty and XP are never changed by personalisation.
- Optional free AI wording of quests, strictly validated and rejecting recently repeated titles, with a fallback to the built-in habit library when no AI key is set or the service is down.
- Pillar pages with XP, weekly change, streak, a 14-day activity grid and habit journeys (starting and latest target, next task, purpose, long-term direction).
- Progress insights based only on recorded completions (most consistent habit, this week versus the same weekday last week, life areas explored), plus a short AI reflection with a labelled local fallback.
- Weekly recap with a per-pillar breakdown and a CSV export of all completed quests, including multiplayer rewards.

**Playing with friends**
- Squads with invite codes or copyable invite links, shared weekly quests that need two confirmations, member-by-quest participation and a weekly squad ranking.
- Daily 1v1 competitions with a live two-player ranking and weekly winners. Invitations must be explicitly accepted or dismissed after login, and survive the Google sign-in handoff without putting tokens in links.
- A leaderboard of every account, refreshed every 30 seconds. At the end of each UTC week the top three players with positive XP get 100/50/25 bonus XP once.

**Settings, reminders and privacy**
- Settings: pillars, quests per pillar, profile photo, avatar ring, language and notification preferences.
- Opt-in daily reminder emails, sent hourly by a GitHub Actions worker through Brevo. Browser push supports a device test only.
- A public privacy notice in four languages (linked on the login screen and in Settings) and an email-based path for rights and deletion requests.
- English, Portuguese, French and German everywhere after login; works on phone and desktop.

## Run it locally

Requirements: [`uv`](https://docs.astral.sh/uv/) (Python 3.11+) and, for the JavaScript tests, Node.js.

1. Create `.streamlit/secrets.toml` with the Supabase project URL and anon key (shared privately by the team):

   ```toml
   [supabase]
   url = "YOUR_SUPABASE_PROJECT_URL"
   anon_key = "YOUR_SUPABASE_ANON_KEY"
   ```

   Without an AI key the app still works: quests come from the built-in habit library. AI setup: [docs/ai-quests-setup.md](docs/ai-quests-setup.md).

2. Start the app. It opens at http://127.0.0.1:8502 on your own computer only (the public version is the live app above):

   ```bash
   uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8502
   ```

3. Run the tests:

   ```bash
   uv run pytest                                      # all Python tests (tests/ and checks/)
   node --test tests/*.test.cjs checks/*.test.cjs     # Google sign-in and session tests (JavaScript)
   ```

Without `uv`, create a virtual environment, run `pip install -r requirements.txt`, then use `python -m streamlit run …` and `python -m pytest` instead.

Never commit `.streamlit/secrets.toml` or any other file containing credentials.

### Database

The shared Supabase project already has every migration applied, so do **not** rerun `schema.sql`. To set up a new Supabase project, follow the ordered steps in [docs/team-setup.md](docs/team-setup.md). Email (SMTP) and Google sign-in setup: [docs/supabase-setup.md](docs/supabase-setup.md). Set the public app URL in `auth_config.json` for each deployment.

### Access for teammates

- **Using the app** needs only the live link and a Life Quest account.
- **Programming** needs access to this repository and your own `.streamlit/secrets.toml` with the same URL and anon key.
- **Changing tables or policies** needs a Supabase membership: add each teammate in **Project Settings → Team** with their own email. Never share a Supabase password.

If the live app shows "Supabase is not configured", add the same two values to the Streamlit app's **Secrets** setting and restart it. The deployed app does not read the `secrets.toml` file on your computer.

## How it is built

- **Interface:** Streamlit (Python). All styling lives in `design.py` and `.streamlit/config.toml`; rules in [docs/design.md](docs/design.md).
- **Accounts and data:** Supabase Auth and PostgreSQL. Every database call sends the user's own login token, so Row Level Security and database functions decide what each user may read or change. XP can only be awarded by database functions, never written by the browser.
- **External services:** Requesty (optional, free AI models only), Photon / OpenStreetMap (city search), Brevo (reminder emails).
- **Quality:** dependencies are pinned in `pyproject.toml` / `uv.lock` / `requirements.txt`; GitHub Actions runs the Python tests, the JavaScript tests and a dependency audit on every push.

More detail:
- [docs/architecture.md](docs/architecture.md): data storage, security, test coverage, what happens when a service is down, known limits.
- [docs/security-audit.md](docs/security-audit.md): security review.
- [docs/product-rules.md](docs/product-rules.md) and [docs/social-play.md](docs/social-play.md): quest, XP and multiplayer rules.
- [docs/reminders.md](docs/reminders.md): the scheduled reminder worker.
- [docs/walkthrough.md](docs/walkthrough.md): the repository walkthrough script.

## Project structure

```text
app.py                  Entry point: login, dashboard, navigation, Settings, api_request()
auth_helpers.py         Login rules (email, password, redirects), independent of Streamlit
browser_session.py      Restores a verified session after reload (up to 30 days)
onboarding.py           First-run questions (onboarding_text.py: pt/fr/de wording)
i18n.py                 Interface translations (en/pt/fr/de)

quest_plan.py           Habit tracks, progression and statistics (pure logic, the core)
quest_variety.py        Practical activity variants; never changes targets or XP
quest_languages.py      Translations of quest titles and targets
quest_display.py        Shows stored quests in the user's language
personalization.py      Country/city/language wording; never changes targets or XP
ai_quests.py            Optional free AI wording with strict validation
ai_quest_ui.py          Home and pillar pages (quests, statistics)
habit_journey.py        Habit journeys shown on pillar pages
progress_insights.py    Feedback based only on recorded completions

social_play.py          Squads, squad ranking and 1v1 competitions
duel_progress.py        Live standings for 1v1 competitions
invitations.py          Invite codes and links; joining needs an explicit action
weekly_leaderboard.py   All-player weekly ranking and prizes

profile_data.py         Shared profile settings helpers
account.py              Profile photo, avatar ring, device notification test
places.py               City search (Photon / OpenStreetMap)
reminder_settings.py    Opt-in reminder email settings
privacy.py              Public privacy notice and rights requests
design.py               All styling and reusable UI pieces

auth_component/         Google sign-in in the browser (PKCE)
session_component/      Browser side of the remembered sign-in
scripts/send_reminders.py  Reminder email worker run by GitHub Actions
supabase/*.sql          Tables, security rules, database functions and live checks
tests/                  Original automated test suite
checks/                 Regression tests added for later features
docs/                   Architecture, design rules, setup and privacy guides
.github/workflows/      Tests on every push; hourly reminder worker
```

### Why there are two test folders

`tests/` is the original suite: unit tests, security checks and end-to-end workflows that drive the real app against an in-memory Supabase (`tests/fake_supabase.py`). Our team rule (see `AGENTS.md`) is that existing tests are not edited as a side effect of a feature change, so the tests that prove an old behaviour still work as written.

`checks/` holds the regression tests added with later features: remembered sign-in, invitation links through Google sign-in, quest variety and insights, the second round of social features, and privacy. Both folders run together: `uv run pytest` collects every Python test in both, and CI runs the JavaScript tests in both.

## Privacy and account requests

Read the public [Privacy Policy](https://life-quest-team.streamlit.app/?privacy=1) (also linked on the login screen and in Settings), or its [English source](docs/privacy-en.md); Portuguese, French and German versions are in the app. Controller: Hajna Pintér, 81324@novasbe.pt.

Rights and deletion requests are emails the user sends; accounts are not deleted automatically. Administrators follow [the privacy runbook](docs/privacy-operations.md). Provider agreements and international transfers still need controller review before the app could claim GDPR compliance.
