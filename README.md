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
- Personal profiles with location and selected life areas.
- Challenges loaded from the Supabase database.
- Secure challenge completion with persistent points.
- Weekly leaderboard based on points earned during the current week.
- Squad creation and invite-code based joining.
- Shared squad member progress.

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

3. Run the SQL files in `supabase/` in the Supabase SQL Editor.
4. Start the app:

   ```bash
   uv run streamlit run app.py
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
4. Run `uv run streamlit run app.py`.
5. Create an account and join the squad with the invite code.

The SQL files only need to be run when setting up a new Supabase project. If
the team is using the existing Life Quest Supabase project, the database is
already configured.

## Project structure

```text
app.py                         Streamlit application
supabase/schema.sql            Database tables, policies, and functions
supabase/*-function.sql        Incremental database functions
docs/product-rules.md          Product rules and acceptance examples
docs/supabase-setup.md          Supabase setup and security notes
```
