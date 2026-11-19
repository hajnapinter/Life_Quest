# Continue development with the team

## Get this version

Open the `hajnapinter/Life_Quest` repository in GitHub Desktop and select the branch containing this handoff. Fetch/pull its latest commit before editing. Keep unrelated work in another branch or local checkout.

## Start locally

Install `uv`, open this project folder and run:

```sh
uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Open `http://127.0.0.1:8502/`. This matches the callback configured in `auth_config.json` and the shared project's Supabase redirect allow list. Using a different port requires matching authentication configuration. The localhost address works only on your own computer.

Create your own `.streamlit/secrets.toml` using Supabase project values shared privately by the team. The required table is `[supabase]` with `url` and `anon_key`. Do not use a service-role key. The app uses Supabase Auth and user-scoped RPCs.

For AI, configure `REQUESTY_API_KEY` in the server environment or a private `[requesty]` table with `api_key` in Streamlit Secrets. The approved model is checked against live zero-cost prices. Without that key, the personalised habit library still supplies five practical quests per pillar, so teammates can work on the app without AI credentials. No paid fallback is enabled.

Never commit secrets, paste them in issues or include them in screenshots. `.streamlit/secrets.toml`, the virtual environment and test caches are ignored. Each teammate should use their own account rather than someone else's Supabase or Google login.

## Database

The current shared Life Quest Supabase project already has the migrations below. Do not rerun the initial schema on that project.

For an empty project, run these in order in the Supabase SQL Editor:

1. `supabase/schema.sql`
2. `supabase/ai-quests.sql`
3. `supabase/five-quest-slots.sql`
4. `supabase/social-play.sql`
5. `supabase/protect-profile-points.sql` (stops users editing their own XP; **also run this once on the existing shared project**, it is new and safe to repeat)
6. `supabase/security-hardening.sql` (closes the findings in `docs/security-audit.md`; **also run this once on the existing shared project**, after step 5)

The separate squad, complete-challenge and weekly-leaderboard SQL files contain the original incremental functions; the latest social migration updates the leaderboard to include all reward sources.

For a deployed app, add its secrets to the deployment settings, configure its URL and add that exact URL in Supabase Auth redirect configuration. Google OAuth credentials are configured in the Supabase dashboard and must not be copied into application source code. SMTP remains a separate deployment task.

## Main files

- `app.py`: authentication screens, dashboard and bottom navigation.
- `auth_component/` and `auth_helpers.py`: Google PKCE and authentication validation.
- `onboarding.py`: first-run questionnaire.
- `quest_plan.py`: five independent habit tracks per pillar, progression and statistics.
- `ai_quests.py`: free-only Requesty generation and model-output validation.
- `ai_quest_ui.py`: checkbox completion, atomic replacement and XP feedback.
- `social_play.py`: squad missions and daily friend competitions.
- `supabase/`: database schema and migrations.

## Verification

```sh
uv run pytest
```

Current suite: 11 tests passed. Additional UI checks covered checkbox completion, failed-save recovery, rapid checks and preserved statistics. Transactional database checks covered replacements, duplicate-XP protection, squad confirmation, pair-specific scores, deadline enforcement and weekly rewards. All database verification fixtures were rolled back.

Scores and real-life completion are self-reported. Daily and weekly competitions use UTC. Closed results settle the next time either participant opens the social page; no paid scheduler is required. See `docs/social-play.md` and `docs/ai-quests-setup.md` for behaviour and limits.
