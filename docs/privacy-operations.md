# Privacy operations — administrators only

Controller and contact: **Hajna Pinter — 81324@novasbe.pt**.
Read this mailbox daily. Settings opens a user-sent email draft; it does not submit a request to a database or automatically erase anything. Acknowledge requests, record the received date and normally respond within one month. Explain any lawful extension/refusal. Verify identity proportionately through the account email; never request passwords. Arrange a secure alternative if that email is inaccessible. Do not publish request correspondence in issues or commits.

For access/portability: securely provide the verified requester's own Auth identity/metadata, profile, quests, completions, memberships, confirmations, scores, rewards and reminder records. A quest-history CSV alone is not a full account export. Exclude other users' personal data. Rectification, restriction and objections need case-by-case review. Review correspondence retention after closing each request rather than keeping it indefinitely.

## Verified erasure requests

1. Identify the exact Auth user UUID and account email in Supabase. Check the request and identity; explain that shared competitions disappear, other players keep earned XP, shared squad ownership transfers and backups/provider logs follow their own expiry. Obtain explicit confirmation of this concrete action.
2. Disable email reminders for that user. Check Brevo for queued deliveries: already handed-off messages may still arrive. A running worker can have already claimed a recipient, so coordinate with the scheduled job; pausing the worker briefly avoids that race.
3. Apply `supabase/privacy.sql` **after** the leaderboard migration. It installs a private database-owner function, never callable by app, anon, authenticated or service_role. It does not erase anyone when installed. Do not grant it to clients or add an app service-role key.
4. In the admin SQL editor, use a transaction, the exact verified UUID and the confirmation string `ERASE <same-uuid>` with `public.admin_erase_account(subject,confirmation)`. Review a dry run with ROLLBACK first. Only COMMIT the irreversible deletion for a verified, confirmed request. Never paste real identity data into a shared SQL snippet or Git.
5. Confirm absence from Auth/users, profiles, quests, completions, memberships, confirmations, scores, rewards, leaderboard_prizes and reminder_outbox. Auth sessions/identities follow Auth's cascades. Shared squads with remaining members must still exist; other members retain XP. Notify the requester through the agreed secure channel. Browser copies are not remotely wiped: tell them to log out/clear local site data.
6. Remove any separately held support copies that are no longer needed, handle provider-side deletion where applicable, and record only a minimal justified completion record. Backups are not immediately overwritten; ensure any restore re-applies completed deletion requests before reopening the app.

Reproduce the synthetic deletion and two-user isolation tests with `supabase/check-privacy.sql`; its transaction rolls back. It sends no email and deletes only fixture users inside the rolled-back transaction. Do not replace fixture IDs with real users.

## Outstanding controller review

Before claiming full GDPR compliance or opening beyond the course audience, verify current Supabase region, provider processor/subprocessor agreements, data-transfer safeguards, log/backup retention and deletion mechanisms (including Requesty/model providers), the legitimate-interest assessment, and that this mailbox is staffed. The notice discloses the uncertainty rather than making an EU-only/zero-retention promise. Technical tests cannot certify legal compliance.
