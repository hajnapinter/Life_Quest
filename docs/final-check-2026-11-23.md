# Final check — 23 November 2026

Scope: the checklist supplied by the team. Results distinguish executed checks from human/legal work. No Moodle submission and no repository visibility change were performed.

| Checklist item | Result and evidence |
|---|---|
| Privacy notice: data, purpose, storage and access | Added a public notice in en/pt/fr/de, naming the approved controller/contact. Describes Auth/profile/activity, social visibility, AI, reminders, browser storage and providers. See `privacy-*.md`. Hosting/transfer contracts remain a controller review item. |
| Rights and deletion requests | Settings and public notice open explicitly user-sent email requests to the controller. No misleading instant-delete or automatic-submission claim. Access/portability, correction, restriction, objection and erasure are explained. |
| Privacy link in app and README | Verified in production sign-up and authenticated Settings; anonymous `?privacy=1` works without account/configuration. README links the public app notice and source. |
| Account deletion and third-party sharing | Installed an owner-only procedure; all 19 rolled-back live database checks passed, including real fixture Auth sessions/identities, exact-confirmation guard, two-user RLS, client XP protection, squad ownership transfer and surviving player's weekly XP dates. No real account was deleted. Operational instructions cover queued mail, provider copies and backups. Provider deletion/transfer guarantees still need review. |
| Secret scan | Scanned all 236 unique historical blobs existing before this change and 92 working files including the new source, matching credential patterns and two configured local key values. No findings. Ignored local Secrets were read only in memory for comparison; values were not logged. Pattern scans do not prove absence of every possible secret type. |
| Two-user data protection | Synthetic accounts in the real Postgres database, with `SET LOCAL ROLE authenticated` so the test cannot silently bypass RLS. B cannot read A's profile/quests, can read its own profile, and cannot write XP. All fixture work rolled back. |
| API keys and Auth | New erasure RPC unavailable to anon/authenticated/service_role. Existing PKCE, replay/origin checks, verified token restoration and logout checks passed. No service-role key added to app. Private secrets configuration preserved. |
| Dependencies and CI | `pip-audit -r requirements.txt --progress-spinner off`: **No known vulnerabilities found**. CI [45169359980](https://github.com/hajnapinter/Life_Quest/actions/runs/45169359980) passed Python, JS and audit on commit `351d402`. |
| Automated app workflows/error handling | **232 Python tests passed** (including registration/onboarding, quest completion, Settings, multiplayer, error handling and 9 new privacy checks). **4 JavaScript tests passed**. Tests use fake Supabase for app workflows; they are not live email-delivery proof. |
| Real database multiplayer and prizes | Reran the 14 product and 15 weekly-leaderboard checks after installing privacy.sql. All passed with assertions, each transaction rolled back. Includes replay/deduplication, invitation permissions, scores, opt-in reminders, restricted worker, weekly reset and idempotent prizes. |
| Deployed application | Anonymous sign-up/public policy and signed-in Home, Recap, Squad, Competition, Settings and Leaderboard opened without app exceptions. A deliberately short registration password was rejected before account creation. New rights links and all four policy languages verified. Existing real players' scores and quests were not changed. |
| Responsive layout and accessibility | Public policy inspected at 390px with document/content width both 390px, no horizontal overflow or app exceptions; also inspected desktop layout. Signed-in navigation/content inspected at 692px with no overflow. Labels, skip link, keyboard-operated navigation and reduced-motion CSS checked. This is a limited inspection, not a complete screen-reader/WCAG audit across every screen/device. |
| Verification email delivery | Prior Gmail receipt was confirmed by the user. University inbox delivery remains unconfirmed. SMTP acceptance cannot guarantee inbox placement for every provider; this run did not send additional mail. |
| Live demo | Walkthrough and rehearsal checklist prepared in `walkthrough.md`. The team must still rehearse personally; automated tests do not demonstrate each student's understanding. |
| Public GitHub repo | Still **private**, respecting the user's instruction. Requires separate team/user approval before publication. |
| Moodle | **Not submitted**, respecting the user's instruction. The team must handle submission and check the stated deadline itself. |

## Reproduction

```text
UV_CACHE_DIR=/private/tmp/lifequest-qa-uv uv run --offline pytest -q
232 passed in 7.24s

node --test tests/*.test.cjs checks/*.test.cjs
4 passed, 0 failed

uvx pip-audit -r requirements.txt --progress-spinner off
No known vulnerabilities found
```

Use writable temporary cache/tool directories if the host restricts default caches. SQL: apply `privacy.sql` after `weekly-leaderboard.sql`; run `check-privacy.sql`, `check-product-fixes.sql`, `check-weekly-leaderboard.sql` in the owner SQL editor. They create synthetic fixtures and ROLLBACK. Do not replace fixture accounts with real users.

## Remaining limits before calling everything finished

- Controller review of processor agreements, actual regions, international-transfer safeguards, provider log/backup retention, and the legitimate-interest assessment. A policy plus tests does not certify GDPR compliance. Official guidance: [European Commission — individual rights](https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en).
- Staff the published rights-request mailbox; fulfil verified requests under the runbook. Account deletion is an administrator action, not an automatic self-service button.
- Full screen-reader/device accessibility testing and university inbox delivery have not been established.
- Team rehearsal, explicit approval to publish the repository, and team-performed Moodle submission remain human actions.

## Follow-up review and remembered sign-in

See [the detailed provider and accessibility review](provider-review-2026-11-23.md). Supabase region is now verified as Ireland, Streamlit hosting is US-based, the Requesty key has request logging off, and the current free model advertises training and 30-day retention. The user explicitly declined a model switch. All six signed-in screens passed the 390px overflow/form-name/alt-attribute inspection. Remaining contrast/heading findings and the unsuccessful university mailbox/quarantine lookup are documented rather than marked complete.

The requested session repair now persists only a rotating refresh credential for up to 30 days since authenticated renewal, verifies identity before restoring access, clears both storage types on logout and offers retry after connection failures. Unit/regression checks: **236 Python passed; 8 JavaScript passed**. Live refresh/reopen/logout verification follows deployment. Earlier tab-only documentation is superseded by this change.
