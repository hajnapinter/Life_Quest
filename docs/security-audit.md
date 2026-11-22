# Security audit

**Date:** 19 Nov 2026 · **Scope:** the Streamlit app, the Google sign-in component, the Supabase SQL (tables, Row Level Security, database functions), dependencies and the repository.
**Method:** line-by-line review of every SQL file in the order they are applied (`docs/team-setup.md`), every place user input enters or user text is shown, and every call to an external service. Each fix has an automated test.

## Status of the findings

| Status | Meaning |
|---|---|
| **Fixed** | Changed in the app code and covered by tests. |
| **Fixed – run SQL** | Fix written in `supabase/security-hardening.sql` or `supabase/protect-profile-points.sql`. It takes effect once someone runs the file in the Supabase SQL Editor (see `docs/deploy.md`, step 4). |
| **Accepted** | A known limit of a student project, explained below. |

| # | Finding | Severity | Status |
|---|---|---|---|
| H1 | Anyone could add themselves to **any squad** through the REST API without the invite code (a leftover insert policy from `schema.sql`), then see its members, earn its XP and challenge its members. | High | Fixed – run SQL |
| H2 | **Unlimited XP** by calling `save_quest_slots` in a loop (complete + replace); quest difficulty comes from the client. | High | Fixed – run SQL (max 20 XP-earning completions per day, target upper bound, old `finish_ai_quest` closed) |
| H3 | Users could **edit their own `points`** column directly. | High | Fixed – run SQL (`protect-profile-points.sql`) |
| M1 | Squad XP could be farmed by creating many squads. | Medium | Fixed – run SQL (max 5 squads per creator) |
| M2 | **Markdown injection**: a squad name or another user's display name such as `![](https://evil/p.png)` was rendered as an image or link (tracking pixel, phishing link). | Medium | Fixed (escaped with `plain_markdown`; tested end to end) |
| M3 | Squad invite codes are 8 hex characters from a non-cryptographic generator, with no attempt limit. | Medium | Accepted: with H1 fixed, the only way in is guessing 1 of 4.3 billion codes through the API. A real product would use `gen_random_bytes` and rate-limit joins. |
| L1 | Users could insert back- or future-dated completed challenges to inflate the leaderboard. | Low | Fixed – run SQL (only the `complete_challenge` function may write) |
| L2 | No database-side length or value limits on names, city, pillars. | Low | Fixed – run SQL (constraints; existing rows are kept) |
| L3 | Raw database errors (table, constraint and function names) were shown to users. | Low | Fixed (`friendly_error`; tested) |
| L4 | Some older functions were executable by anonymous users (they still required a login inside). | Low | Fixed – run SQL |
| L5 | Uploads up to Streamlit's default 200 MB were accepted before our 8 MB check. | Low | Fixed (`maxUploadSize = 8`; tested) |
| L6 | Logging out did not end the session on Supabase. | Low | Fixed (calls `/auth/v1/logout`; tested) |
| L7 | The squad ranking matches people by display name (names aren't unique). | Low | Accepted: the leaderboard function returns no user ids; documented in `architecture.md`. |
| L8 | The 8-character password minimum and email cooldown are enforced in the app; Supabase's own minimum may be lower. | Low | Action: set *Minimum password length = 8* in Supabase → Authentication → Policies (dashboard setting). |
| I1 | The Pro flag and profile photo live in user-editable metadata. | Info | Accepted: Pro is a demo. A real version would store Pro in a server-only table written by the payment provider. |
| I2 | The weekly leaderboard shows the top 50 display names and XP to every signed-in user (no emails or ids). | Info | Accepted, by design. |

## What was already good (verified)

- **No secrets in the repository**, including the full Git history; `.streamlit/secrets.toml` is ignored; a test scans for keys.
- **Row Level Security on every table.** Users can only read their own profile, quests and completions, and only the squads they belong to. The seven social tables can't be touched directly at all, only through database functions.
- **Database functions are hardened:** each `security definer` function fixes `search_path`, checks `auth.uid()`, and there is no dynamic SQL anywhere (no `EXECUTE`, no string-built queries).
- **No double rewards:** rewards have a unique key per user and source, rows are locked in a fixed order, and completing an already-completed quest pays nothing.
- **Duels and squads are checked server-side:** participant, active duel, today only, value within range, current week, squad membership.
- **Google sign-in** uses PKCE (S256, 32-byte random verifier, expires in 10 minutes), checks the origin of every browser message, and the server re-verifies the token.
- **Redirect URLs** must be https (or localhost) with no credentials, query or fragment.
- **Neutral sign-up messages** don't reveal whether an email already has an account.
- **HTML output:** every custom HTML block escapes user text; photo URLs must be `data:image/…` and are attribute-escaped.
- **Photos** are re-encoded to an 80×80 JPEG (removes metadata and disguised files; decompression bombs are rejected).
- **AI answers are validated** before use; the prompt treats input as data; only free models are used; no name, email or location is sent.
- **CSV exports** neutralise cells starting with `= + - @` (CSV injection).
- **Dependencies:** three direct packages, pinned exactly, audited with `pip-audit` on every push (no known vulnerabilities).

## How the fixes are tested

| Test | Checks |
|---|---|
| `test_security.py` | No credentials in the repo; secrets file ignored; XP not user-writable; the hardening SQL contains every fix; upload cap. |
| `test_features.py` | Database errors are hidden; Markdown is escaped; HTML is escaped; photos are validated. |
| `test_workflows.py` | End to end: a malicious squad name is shown as text; wrong invite code is rejected; logout revokes the session; profile updates can't include points. |

The SQL files were checked with the PostgreSQL parser. Their *behaviour* is not tested against a real database (no test database in CI). After running them, try the demo checklist once.

## What the team must do

1. Supabase → SQL Editor: run `supabase/protect-profile-points.sql`, then `supabase/security-hardening.sql`.
2. Supabase → Authentication → Policies: minimum password length 8.
3. Then follow the demo checklist in `architecture.md` once, to confirm squads and quests still work.


## Live verification — 22 November 2026

Both `protect-profile-points.sql` and `security-hardening.sql` were applied
successfully to the shared Supabase project. Read-only catalog checks confirmed:
all public tables have RLS; authenticated users cannot update profile points or
insert squad memberships directly; the old reward RPC is disabled; the new
completion RPC includes the daily reward cap. The Auth password minimum was set
to 8 characters.

A transaction with three temporary accounts checked eight behaviours against the
real database: personal completion/replay protection, identical shared quests,
exactly one reward per participant after two confirmations, outsider rejection,
identical duel quests, separate editable scores, out-of-range rejection and
outsider score rejection. All eight checks passed. The transaction was rolled
back, including accounts, memberships, scores and XP.

A scan of 124 unique historical file blobs found no local configured keys or
JWT/API-token patterns. This is an automated pattern check, not a guarantee that
every possible kind of secret can be detected.
