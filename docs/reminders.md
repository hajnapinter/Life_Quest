# Scheduled email reminders

This is an opt-in daily email, separate from Supabase confirmation emails and the device push test. No subscription modes or payment integration exist.

## Installation

After the existing schema, five quest slots, social play and security migrations, apply `supabase/product-fixes.sql`, then `supabase/reminders.sql`. These were installed on the shared project on 23 November 2026.

Create a random 32-byte worker credential. Store only its SHA-256 hex digest in `reminder_worker_keys.key_hash`; retain the raw credential exclusively in private GitHub Actions Secrets. Do not use a service-role key. The worker can only claim opted-in confirmed recipients, acknowledge deliveries and settle competitions under the existing rules. It cannot edit arbitrary profiles or quests.

Configure six repository Actions Secrets:
- `REMINDER_SUPABASE_URL`
- `REMINDER_SUPABASE_ANON_KEY`
- `REMINDER_WORKER_KEY`
- `REMINDER_SMTP_USERNAME`
- `REMINDER_SMTP_PASSWORD` (dedicated Brevo SMTP credential)
- `REMINDER_SMTP_SENDER` (verified sender)

Use Actions → Daily reminders → Run workflow with `check_only=true` to verify SMTP authentication and the restricted RPC without sending email. Never paste credentials into an issue, source file or workflow log. Revoke the database worker hash and SMTP key when retiring the worker; rotate both together with their Secrets. Monitor the SMTP key's provider expiry/inactivity limits.

## Delivery behavior and limits

The default branch workflow runs hourly at minute 17 UTC. Each user chooses an IANA time zone and a local hour in Settings; the first eligible run after that hour claims the day's email. GitHub scheduled jobs can be delayed or skipped under load: this is approximate daily delivery, not an exact-time service. Private-repository Actions usage and provider quotas still apply; no paid billing was enabled by this setup.

The outbox has one row per user/local date, an advisory lock, batches of 50, a 250-claim daily ceiling and at least 20 hours between successful sends. This leaves capacity within Brevo's current free daily quota for confirmation emails, but does not reserve capacity against unrelated mail. Explicit SMTP refusals can retry up to three attempts with a 30-minute gap. Ambiguous connection failures are marked uncertain and are not automatically retried, avoiding duplicate messages. Operators must inspect provider delivery logs for these cases. Successful SMTP submission does not prove inbox placement.

Only confirmed Auth emails with `profiles.email_reminders=true` are selected. Turning the setting off excludes future claims; an already claimed message may still be in flight. Emails use the saved UI language (en/pt/fr/de), contain no quest completion details and link to the app and Settings. The scheduler also settles due competitions even when no email is due. Score rules and progression are unchanged.

`get_reminder_status` shows only configuration and worker heartbeat health; it does not expose credentials. `--check` refreshes that heartbeat but does not certify a completed delivery. Review Actions and Brevo logs when investigating delivery.
