# Repository walkthrough: preparation

In the walkthrough, the teaching staff open this repository and ask high-level questions. **Any member can be asked about any part**, and the grade rewards explaining *how* it is built, *why*, its *limits*, and *how it could change*. This page is a guided tour of the repository and answers to common questions about how it is built. The details behind every answer are in [architecture.md](architecture.md) and [security-audit.md](security-audit.md).

## 1. The 5-minute tour (open the files in this order)

| # | Open | What it shows |
|---|---|---|
| 1 | `README.md` | What Life Quest is, the deployed URL, how to run the app and the tests. |
| 2 | `app.py` → `api_request` | "Every database call goes through this one function. It sends the **user's own login token**, so Supabase's Row Level Security decides what each user may see or change, not our Python code." |
| 3 | `quest_plan.py` → `slot_plan` | "This is the heart of the app: five habit tracks per pillar. After a success the next target goes up; after 'too hard' it goes down, within fixed limits. It's pure Python, so it's easy to test." |
| 4 | `supabase/five-quest-slots.sql` → `save_quest_slots` | "Completing a quest is **one database transaction**: mark it done, add XP, save the next quest. If anything fails, nothing is half-saved, and completing twice does nothing." |
| 5 | `ai_quests.py` → `validate_batch` | "AI only rewords quests. We never trust its answer: wrong count, changed target, too long, timers on experience quests… all rejected, and then the habit library is used instead." |
| 6 | `tests/` + `.github/workflows/tests.yml` | "238 automated tests run on every push, including 19 full user workflows against a fake Supabase." |
| 7 | `docs/` | Architecture, security audit, design rules, deployment. |

## 2. Common questions

### Architecture and data
**Where is the data stored?**
In Supabase (hosted PostgreSQL). Tables include profiles, quests (`ai_quests`), squads, squad quests and confirmations, 1v1 competitions, rewards. Small per-user settings (onboarding answers, quests shown, preferences, photo) are in the login's *user metadata*. The access token lives in server memory; only the rotating refresh token is saved in project-scoped localStorage for up to 30 days since renewal (sessionStorage fallback); restore is server-verified and logout clears both. Secrets are in Streamlit Secrets, never in Git.

**Why Streamlit and Supabase?**
Streamlit lets us build the whole UI in Python, the language of the course. Supabase gives us accounts, a real Postgres database and Row Level Security without writing our own backend.

**Why are some settings in user metadata instead of tables?**
The shared database was already set up; metadata needed no migration for the whole team. The limit: users can edit their own metadata, so nothing security-relevant may depend on it. That's why XP is in a protected table and metadata contains preferences only.

**What happens when I tick a quest?**
The checkbox queues the completion → the app calls `save_quest_slots` → the database marks it done, adds 10 + 5 × difficulty XP and inserts the next quest for that slot → the app reloads and shows the new quest with "↑ up from … last time".

**How does the design stay consistent?**
All styling is in `design.py` and `.streamlit/config.toml`; rules for people and AI tools are in `docs/design.md`, and `AGENTS.md` points every assistant there.

### Tests
**What do the tests cover?**
- Unit tests for the pure logic: quest progression, statistics, recap, CSV, AI validation, city search, all-pillar availability, photos.
- Screen tests on the real app: invalid login and sign-up input, Supabase unreachable.
- **19 workflow tests** that drive the real app like a user against a fake Supabase: sign-up and onboarding, completing quests, recap, squads (create, join, wrong code, two confirmations), Settings, logout.
- Security checks: no secrets in the repo, XP not writable.
- The Google sign-in script (PKCE) in JavaScript.

**What do they *not* cover?**
The automated suite does not run against the real database: the fake follows the SQL rules but isn't Postgres. We cover that gap separately with the `supabase/check-*.sql` scripts, which test Row Level Security, permissions and the XP functions on the live database and roll everything back (48 checks, all passing; see [verification.md](verification.md)); they are run by hand, not in CI. Also not automated: the visual design, the real AI's wording, browser notifications and real email delivery, which were checked by hand.

**Why a fake Supabase instead of the real one?**
Tests must be fast, repeatable and must not write into our shared database. The fake answers the same HTTP requests as Supabase, and enforces the same key rules.

### External services
**What if an external API is unavailable?**
- **Supabase:** a clear message, no crash (tested).
- **AI:** quests come from the built-in habit library; only free models are ever used.
- **City search:** "unavailable, you can skip", and the failure isn't cached.
- **Fonts:** the browser's normal font.

**Which external APIs do you use and what do you send them?**
- **Photon (OpenStreetMap):** only the text typed into the city box.
- **Requesty (AI):** pillars, starting levels, quest feedback, city/country and preferences. Never your name or email.
- **Brevo (email):** the email address and the text of confirmation and opted-in reminder emails.
- **Google (sign-in):** handled by Supabase; we only receive the verified identity.

What happens when each service fails is in section 7 of [architecture.md](architecture.md).

### Security
**Did you do a security review?**
Yes, two. See `docs/security-audit.md`. The first audit found 3 high, 3 medium and 8 low findings: the app-side ones are fixed and tested, the database ones are fixed in `security-hardening.sql`. A follow-up review of the newer code found one medium issue (the sign-in components trusted the page that embedded them; they now only talk to the app's own address) and one low issue (AI-written quest titles are now shown as plain text), both fixed. It also confirmed that an anonymous visitor cannot read any table on the live database. A good example to explain: anyone could join any squad through the API because of an old insert policy; now only the invite-code function can add members.

**How do you stop a user from cheating XP or reading other people's data?**
- **Reading data:** Row Level Security on every table, so users only see their own rows.
- **XP:** it only changes inside database functions that check who is calling (`auth.uid()`).
- **Direct edits:** `protect-profile-points.sql` removes the right to edit the `points` column directly.

**How is input validated?**
- Email format; password of at least 8 characters that matches its confirmation.
- Nickname ≤ 30 characters; squad name 2–50; city search ≤ 80.
- Photos: type and size checked, then re-encoded.
- Every AI answer is checked.
- User text is HTML-escaped; CSV exports block spreadsheet formulas.

**Dependencies?**
Three direct ones (`streamlit`, `pillow`, `pytest`), pinned to exact versions, audited with `pip-audit` on every push.

### Limits and how it could change
**What are the main limits?**
- The photo travels inside the login token.
- The squad ranking uses stable user IDs and requires squad membership.
- Quests are self-reported.
- There's no push server, so notifications are only browser permission plus a test notification.

**How would you scale or improve it?**
- Photos in Supabase Storage.
- Automated database integration tests in CI.
- Database tests with a local Supabase in CI.

### Team process
**How did you work as a team?**
- Each member owns features (see the commit history).
- Changes go through branches and pull requests, with GitHub Desktop.
- Tests run automatically on every push.
- One design guide is shared by everyone's AI tools.

## 3. Practise like this

1. Everyone reads `architecture.md` once.
2. Split the questions above: each person rehearses one section out loud, then **swap**, because anyone can be asked anything.
3. Do the 5-minute tour once each, with someone else asking "why?" after every answer.
4. Run `uv run pytest` together once, so everyone has seen the tests pass.

Scheduled email uses a restricted worker credential, a daily outbox and explicit opt-in. Explain why SMTP acceptance cannot guarantee inbox delivery and why ambiguous failures are not automatically retried. See `docs/reminders.md`.

## Final rehearsal additions — 23 November

Before presenting, each member should practise sign-up/onboarding with a disposable account, complete one quest and explain atomic XP/progression, compare the habit journey and Recap, show shared squad participation and a 1v1 score, and explain the weekly podium/reset. Show Settings → Your data, your choice and the anonymous Privacy Policy. Do not delete a real account or change real competition scores during rehearsal. Have the controller explain the email-based rights process and why SMTP acceptance is not inbox delivery. Finish by pointing to the passing CI and the owner-only, rolled-back database privacy test.

Prepare screenshots as a network-failure fallback, and practise answering out loud: any of us can be asked about any part. What we verified and the known limits are in [verification.md](verification.md).
