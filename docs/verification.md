# Verification and known limits

What we checked before submitting, how we checked it, and what we know is still open.
The final state was checked on 23 November 2026. Details of each security finding are in [security-audit.md](security-audit.md); how the app is built is in [architecture.md](architecture.md).

## Automated checks (run on every push)

| Check | Command | Result |
|---|---|---|
| Python tests (`tests/` and `checks/`) | `uv run pytest` | 238 passed |
| JavaScript tests (Google sign-in, remembered sign-in) | `node --test tests/*.test.cjs checks/*.test.cjs` | 8 passed |
| Dependency audit | `uvx pip-audit -r requirements.txt` | No known vulnerabilities |

GitHub Actions runs all three on every push ([tests.yml](../.github/workflows/tests.yml)). The app tests use an in-memory stand-in for Supabase (`tests/fake_supabase.py`), so they prove the app's behaviour, not the real database rules. The real database is checked separately (next section).

## Checks against the real database

The SQL files in `supabase/` that start with `check-` create made-up test users and data, assert the expected result, and then **roll everything back**, so real players are never touched. The privacy checks switch to the normal signed-in user role, so Row Level Security cannot be skipped by accident.

| File | Checks | Result |
|---|---|---|
| `check-privacy.sql` | One user cannot read or change another user's profile or quests; users cannot write their own XP; account erasure needs an exact confirmation and keeps other players' earned XP | 19 passed |
| `check-product-fixes.sql` | Duplicate completions are ignored; invitation permissions; scores; opt-in reminders; the reminder worker's restricted access | 14 passed |
| `check-weekly-leaderboard.sql` | Weekly reset; prizes paid exactly once; tie rules | 15 passed |

Run them in the Supabase SQL editor after the migrations (order in [team-setup.md](team-setup.md)).

## Security checks

- **Secrets:** we scanned every file and the whole Git history for keys, tokens and passwords. Nothing was found, and `.streamlit/secrets.toml` has never been committed. `tests/test_security.py` repeats a scan on every push. A pattern scan cannot prove that no unusual secret exists, so keys are only ever kept in Streamlit and GitHub Secrets.
- **Keys in the app:** the app only has the public Supabase "anon" key. Access is decided by the database rules, never by the key. The reminder worker has its own restricted database access, stored in GitHub Secrets.
- **Sign-in:** Google sign-in uses PKCE, and replayed or foreign messages are rejected. Staying signed in keeps only a refresh credential, which Supabase verifies again on every restore. Logout clears it on every tab.

## Checks on the deployed app

- Sign-up, onboarding, Home, Recap, Squad, Competition, Settings and Leaderboard opened without errors.
- Invalid input is rejected with a clear message (for example, a password that is too short is refused before an account is created).
- Staying signed in worked across three reloads and a new tab; logout stayed logged out and signed out the other tab.
- All signed-in screens were checked at phone width (390px) and desktop width (1280px): no sideways scrolling, every form field has a name, every image has alt text, and the keyboard can reach the navigation.

## Accessibility

Fixed after review:
- White text on the orange buttons was 4.10:1, below the 4.5:1 minimum. The orange is now `#BF4A1A` (4.99:1).
- The keyboard focus outline on the navigation was almost invisible (1.49:1). It now uses the same orange (about 5:1).
- Home had no main heading. The greeting name is now the level-1 heading.
- On phones, the hosting platform's controls covered part of the navigation. The navigation now sits higher.

Not done: a full screen-reader walkthrough (VoiceOver or NVDA) and testing on many physical devices. This is not a formal WCAG certification.

## Where the services run

| Service | Used for | Where / setting |
|---|---|---|
| Supabase | Accounts and database | Ireland (eu-west-1), free plan |
| Streamlit Community Cloud | Hosting | United States; allowed for educational use |
| Requesty | Optional AI quest wording and reflections | Request logging is off for our key |
| Brevo | Confirmation and reminder emails | Logs kept one month; message previews off |
| Photon / OpenStreetMap | City search | Only the typed city text is sent |

## Known limits

- **AI model and privacy.** The free AI model we use keeps prompts for 30 days and may use them for training. We never send names or email addresses, only habit themes, targets and city/country, and the privacy notice says so. A free model without retention or training (`novita/ling-3.1-flash`) passed our quality checks in all four languages and is the obvious next step. Without any AI, the app still works from its built-in habit library.
- **Backups.** The free Supabase plan has no automatic backups. Recovery would need a manual export.
- **Account deletion** is done by an administrator after an email request, not by a button in the app ([privacy-operations.md](privacy-operations.md)).
- **Email delivery.** The provider confirms delivery, but some university mail filters still hide the confirmation email. Gmail works.
- **Reminders** are sent by an hourly GitHub Actions job, so they arrive within about an hour of the chosen time, not exactly on time.
- **GDPR.** We wrote a privacy notice in four languages and an erasure procedure. A real launch would still need the data-processing agreements with each provider reviewed. We do not claim full GDPR compliance.
