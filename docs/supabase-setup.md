# Supabase setup

The application will use Supabase for persistent data and row-level security.

## Setup

1. Create a free project at [supabase.com](https://supabase.com/).
2. Open the Supabase SQL Editor.
3. Run [`supabase/schema.sql`](../supabase/schema.sql).
4. Configure an OIDC provider for Streamlit authentication, such as Google.
5. Add the local authentication values to `.streamlit/secrets.toml`.

The secrets file must stay local and must never be committed. It should contain
the Streamlit `[auth]` configuration and the Supabase project URL and anon key.

The app must use the authenticated user's ID for every database query. It must
never trust a user ID supplied by a widget or URL parameter.

## Security rules

- Users can read and update only their own profile.
- Users can create completions only for themselves.
- Users cannot award themselves points directly.
- Active challenges are readable by authenticated users.
- Squad membership is checked by Supabase row-level security.
