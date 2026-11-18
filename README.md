# Life Quest

Life Quest turns personal development into a friendly game. You choose the life
areas ("pillars") you want to grow in, get small practical quests that adapt to
your pace, earn XP, and progress together with friends in squads.

[![Tests](https://github.com/hajnapinter/Life_Quest/actions/workflows/tests.yml/badge.svg)](https://github.com/hajnapinter/Life_Quest/actions/workflows/tests.yml)

## Deployed application

**TODO: paste the Streamlit Community Cloud URL here** (how to deploy: [docs/deploy.md](docs/deploy.md))

## Team

| Name | Student number |
|---|---|
| Catarina Pedro | 71361 |
| TODO | TODO |
| TODO | TODO |
| TODO | TODO |

## Run it locally

```bash
uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8502   # app at http://127.0.0.1:8502
uv run pytest                                                                # Python tests
node --test tests/oauth.test.cjs                                             # Google sign-in tests
```

The app needs `.streamlit/secrets.toml` with the Supabase URL and anon key (see *Local setup* below).
Without an AI key it still works: quests then come from the built-in habit library.

## Main features

- Sign-up and login with email (validated) or Google (PKCE), through Supabase Auth.
- Onboarding: nickname, pillars (up to 3, all 7 with Pro), starting level per pillar, how many quests to show, city search.
- Five adaptive quests kept ready per pillar; harder after a success, easier after "too hard"; shown 1–5 at a time.
- Optional free AI wording of quests, strictly validated, with a habit-library fallback.
- Pillar pages with XP, weekly change, streak, a 14-day activity grid and next steps; each quest shows when its target adapted ("↑ up from 4,000 last time").
- Weekly recap with a per-pillar breakdown and a CSV export of all completed quests.
- Squads with invite codes, shared weekly quests needing two confirmations, and a weekly squad ranking.
- Daily 1v1 competitions with friends and weekly winners.
- Settings: pillars, quests per pillar, city (OpenStreetMap search), profile photo, phone/laptop notifications, email reminders.
- Life Quest Pro (demo subscription): all pillars, avatar styles, country-personalised quests (placeholder), and a list of features that would need paid APIs.
- English, Portuguese, French and German everywhere after login (onboarding included); works on phone and desktop.

## How it is built

See **[docs/architecture.md](docs/architecture.md)**: where the data is stored, security, what the tests
cover, what happens when an external service is down, known limits, and a demo checklist.
The visual design rules are in [docs/design.md](docs/design.md).

## Tech stack

- Streamlit (Python) for the interface; Supabase Auth and PostgreSQL for accounts and data.
- Row Level Security and database functions for access control.
- External APIs: Requesty (optional, free models only) and Photon / OpenStreetMap (city search).
- Dependencies pinned in `pyproject.toml` / `uv.lock` / `requirements.txt`; tests and a dependency audit run on every push.

## Local setup

1. Install `uv`.
2. Create `.streamlit/secrets.toml` with the local Supabase values:

   ```toml
   [supabase]
   url = "YOUR_SUPABASE_PROJECT_URL"
   anon_key = "YOUR_SUPABASE_ANON_KEY"
   ```

3. For the existing shared Supabase project, the migrations are already applied. Do not rerun `schema.sql`. For a new project, follow the ordered steps in [the team setup guide](docs/team-setup.md).
4. Start the app:

   ```bash
   uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8502
   ```

5. Run the tests:

   ```bash
   uv run pytest
   ```

Never commit `.streamlit/secrets.toml` or any other file containing credentials.

## Sharing the project with teammates

The repository contains the application code, database SQL, documentation, and
project configuration. It does not contain `.streamlit/secrets.toml` because
that file contains credentials.

Each teammate should:

1. Clone or download the repository from GitHub.
2. Create `.streamlit/secrets.toml` using the template above.
3. Use the same Supabase project URL and anon key shared privately by the team.
4. Run `uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8502`.
5. Create an account and join the squad with the invite code.

The SQL files only need to be run when setting up a new Supabase project. If
the team is using the existing Life Quest Supabase project, the database is
already configured.

### Important: app access versus Supabase dashboard access

The public Streamlit link and the Supabase dashboard are separate services:

- To open and use the app, teammates only need the working public link and a
  Life Quest account. They do not need your Supabase login.
- To program the app, teammates need access to this repository and their own
  local `.streamlit/secrets.toml` containing the same project URL and anon key.
- To inspect or change tables, policies, or SQL in the Supabase dashboard, add
  each teammate as a member in Supabase **Project Settings → Team** using her
  own email address. Never share your Supabase password or an account login.

If the published link shows “Supabase is not configured”, open the deployment
settings for the Streamlit app and add these two secrets to its Secrets field:

```toml
[supabase]
url = "THE_EXISTING_SUPABASE_PROJECT_URL"
anon_key = "THE_EXISTING_SUPABASE_ANON_KEY"
```

The deployed app does not read the `.streamlit/secrets.toml` file on your
computer. After saving the deployment secrets, redeploy or restart the app.

## Project structure

```text
app.py                  Entry point: login, dashboard, navigation, Settings
onboarding.py           First-run questions
ai_quest_ui.py          Home and pillar pages (quests, statistics)
quest_plan.py           Quest tracks, progression and statistics (pure logic)
ai_quests.py            Optional AI wording with strict validation
social_play.py          Squads, squad ranking, 1v1 competitions
pro.py / account.py     Pro demo, profile photo, avatar, notifications
places.py               City search (Photon / OpenStreetMap)
design.py               All styling and reusable UI pieces
supabase/*.sql          Tables, security rules and database functions
tests/                  Automated tests
docs/                   Architecture, design rules, setup guides
```

## Confirmation email and Google sign-in

The login screen supports confirmation-email resend with a 60-second cooldown,
clear authentication errors and Google OAuth with PKCE. Google activates only
after its provider is configured in Supabase. Custom SMTP is configured in
Supabase, not in the Streamlit code. See [the setup guide](docs/supabase-setup.md)
for SMTP/domain setup, Google Cloud credentials, redirects and verification.
Set the public app URL in `auth_config.json` for each deployment.

## Current team handoff

See [docs/team-setup.md](docs/team-setup.md) for the exact local start command,
private configuration, database migration order and validation checks. No server
credentials are included in the repository. The local app URL is
`http://127.0.0.1:8502/`; it is not a publicly hosted deployment.
