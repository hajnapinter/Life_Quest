# Deploying Life Quest (Streamlit Community Cloud)

About 15 minutes. You need a GitHub account with access to this repository.

## 1. Put the code on `main`

On GitHub, open the pull request from `add-login-screen` and click **Merge pull request → Confirm merge**.

## 2. Create the app

1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Repository: `hajnapinter/Life_Quest` · Branch: `main` · Main file path: `app.py`.
4. Choose an **App URL**, for example `life-quest`. Write it down: `https://life-quest.streamlit.app/`.
5. Open **Advanced settings**:
   - **Python version**: 3.12 (anything from 3.11 works).
   - **Secrets**: paste the block below with the real values (the same ones as in your local `.streamlit/secrets.toml`):

   ```toml
   [supabase]
   url = "https://vyemhzsrqgybunoowuvl.supabase.co"
   anon_key = "PASTE_THE_ANON_KEY_HERE"

   [app]
   url = "https://life-quest.streamlit.app/"   # the App URL from step 4, with the final /

   # Optional: AI wording of quests (free models only). Without it, the habit library is used.
   # [requesty]
   # api_key = "PASTE_THE_REQUESTY_KEY_HERE"
   ```
6. Click **Deploy**. Dependencies are installed from `requirements.txt` (pinned versions).

## 3. Tell Supabase about the new address

Supabase dashboard → **Authentication → URL Configuration**:
- **Site URL**: the App URL.
- **Redirect URLs**: add the App URL (keep `http://127.0.0.1:8502/` for local work).

This is needed for confirmation emails and Google sign-in to return to the deployed app.

## 4. Protect XP (once)

Supabase dashboard → **SQL Editor** → paste the contents of `supabase/protect-profile-points.sql` → **Run**.
It is safe to run more than once.

## 5. Finish the README

Paste the App URL under **Deployed application** in `README.md`, and fill in every member's name and student number.

## 6. Check it

Open the App URL in a private window and follow the demo checklist at the end of `docs/architecture.md`.

### If something goes wrong

| Symptom | Fix |
|---|---|
| "Supabase is not configured" | The `[supabase]` secrets are missing or misspelled. Edit them in the app's **Settings → Secrets**, then **Reboot app**. |
| Google sign-in says it is not configured for this address | `[app] url` is missing or doesn't match the App URL exactly (including `https://` and the final `/`). |
| Confirmation email links open `127.0.0.1` | Update the Site URL in Supabase (step 3). |
| Build fails while installing packages | Check the Python version is 3.11 or newer (step 2.5). |
