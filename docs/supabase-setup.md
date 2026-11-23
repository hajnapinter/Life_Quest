# Authentication and email delivery

Life Quest uses **Supabase Auth**, not Streamlit's separate OIDC accounts.
The existing email/password flow and Google both produce Supabase sessions;
all database requests use the authenticated user's access token and RLS.

## Local connection and deployment

Use the existing team Supabase project. Locally, supply `[supabase]` with `url`
and `anon_key` in `.streamlit/secrets.toml` (the latter accepts a publishable key).
The file is ignored by Git. Configure the same values in your hosting platform's
secrets when deploying. Never use a service-role or secret API key in this app.

`auth_config.json` contains only the public app URL. It currently points to
`http://127.0.0.1:8502/`. Change it to the actual HTTPS URL for deployment.
Under Supabase Authentication → URL Configuration, configure Site URL and add
that exact app URL to Redirect URLs. For local testing also allow the local URL.
Do not leave a production app redirecting to a developer's localhost.

The existing database must have the repository's SQL schema and RPCs installed.
Do not rerun schema setup merely to change authentication.

## Reliable confirmation emails (custom SMTP)

This is provider configuration, not an email-sending function inside Streamlit.
Supabase must generate and send the verification link so it can validate it.

1. Obtain a domain and an email service supporting SMTP (for example Resend).
2. Verify your sending domain in that service using its exact DNS records
   (including SPF/DKIM; configure DMARC according to the provider's guide).
3. In Supabase Authentication → Emails → SMTP Settings, enter the provider's
   SMTP host, port, username and password, plus a verified sender address and
   sender name such as Life Quest. Keep SMTP credentials in Supabase, not Git.
4. Save and set a sending limit appropriate for the provider under Rate Limits.
5. Keep email confirmation enabled. Test signup with an address you control,
   check Supabase Auth logs and provider delivery/bounce logs, then follow the
   verification link and log in. A successful API request is not proof of inbox
   delivery. Check institutional quarantine if the provider reports delivery.

The built-in Supabase sender is for testing, limited to team addresses and a low
project-wide quota. The app's 60-second resend delay does not increase that quota.
Existing users do not need to register again after SMTP is configured; use Resend.
Do not buy a domain, subscribe to a service or change DNS without the owner's choice.

## Google login activation

1. In Google Cloud create/select a project and configure the OAuth consent screen.
   Request only the email/profile identity scopes. Add test users if in testing mode.
2. Create an OAuth client of type Web application. Its authorized redirect URI is:
   `https://vyemhzsrqgybunoowuvl.supabase.co/auth/v1/callback`
   This is Supabase's callback, **not** the Streamlit app URL.
3. In Supabase Authentication → Sign In / Providers → Google, enter the client ID
   and client secret and enable the provider. Keep the secret only in Supabase.
4. Configure the app's Redirect URL as described above. After enabling Google,
   allow up to 60 seconds for the app's provider-availability cache to refresh.
5. Use Continue with Google; a new tab opens and returns to the app. Complete
   the flow in the same browser and on the same app origin (do not switch between
   localhost and 127.0.0.1). Browser storage must be enabled. A new attempt replaces
   any pending attempt in that browser. Restart if the flow expires.

The component uses SHA-256 PKCE, persists only the temporary verifier in browser
storage, exchanges the one-time code directly with Supabase, and never puts an
access token in a URL. Python revalidates the token with `/auth/v1/user` before
accepting the identity. A new WebSocket session after redirect is supported.
Google's verified identity does not need a separate Supabase signup email.

## App behavior and verification

- Signup and resend share a server-side, per-address 60-second cooldown.
- The resend countdown updates every second; server rate limits remain authoritative.
- Responses avoid claiming delivery or revealing whether an account exists.
- Unconfirmed email, invalid login, mail quota and unavailable sender have clear messages.
- Google remains disabled until its Supabase provider and app URL are configured.
- Run `uv run pytest` and `node tests/oauth.test.cjs`.
- Live acceptance: verify signup → email → confirmation → login; resend cooldown;
  Google success/cancel; two browser profiles cannot use each other's PKCE code;
  authenticated profile/quest access. These require configured external providers.

## References

- https://supabase.com/docs/guides/auth/auth-smtp
- https://supabase.com/docs/guides/auth/social-sign-in/auth-google
- https://supabase.com/docs/guides/auth/sessions/pkce-flow
- https://supabase.com/docs/reference/javascript/auth-resend

Privacy: apply `supabase/privacy.sql` after `supabase/weekly-leaderboard.sql`, then run `supabase/check-privacy.sql`. The first installs an owner-only procedure; the second rolls back synthetic test data. See [privacy operations](privacy-operations.md).

Competition totals: apply `supabase/competition-no-score-cap.sql` last, after leaderboard/privacy SQL, to remove per-quest score ceilings. Verify using the rolled-back fixture script `supabase/check-competition-no-score-cap.sql`.
