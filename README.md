# Life Quest

Life Quest turns personal development into a social game. Users choose life
areas, complete challenges, earn points, compete on a weekly leaderboard, and
work together in squads.

## Team members

Replace the placeholders below before submitting the project:

Catarina Pedro | 71361

## Deployed application

Add the public deployed URL here before submission:

`TODO: deployed URL`

## Main features

- Email account creation and login through Supabase Auth.
- Step-by-step onboarding with nickname, selected pillars and starting levels.
- Five renewable, one-line checkbox quests per selected pillar, with persistent XP.
- Free-only Requesty AI variations with a practical habit-library fallback.
- Per-pillar activity charts, completion history and growth targets.
- Secure challenge completion with persistent points.
- Weekly leaderboard based on points earned during the current week.
- Squad creation and invite-code based joining.
- Shared weekly squad quests with two-participant confirmation.
- Accepted friend invitations, shared daily 1v1 challenges and weekly results.

## Tech stack

- Streamlit for the user interface.
- Supabase Auth and PostgreSQL for accounts and persistent data.
- Supabase Row Level Security and database functions for access control.

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
app.py                         Streamlit application
supabase/schema.sql            Database tables, policies, and functions
supabase/*-function.sql        Incremental database functions
docs/product-rules.md          Product rules and acceptance examples
docs/supabase-setup.md          Supabase setup and security notes
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
