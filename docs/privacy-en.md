_Last updated: 23 November 2026_

### Who is responsible?
Hajna Pinter is the controller for the Life Quest student project. Contact: **81324@novasbe.pt**. This notice covers the app, not the providers' own websites.

### What we use and why
- **Account:** email, Supabase user ID, password authentication handled by Supabase, or Google sign-in identity. These enable sign-in, account verification and security. The app does not store your plaintext password.
- **Profile and preferences:** nickname, optional photo, avatar ring, city/country, selected pillars, starting levels, language and onboarding answers. These personalise your experience. Photos are resized and re-encoded; they are stored in account metadata.
- **Activity:** quests, feedback, completions, dates, targets, XP, squad membership and confirmations, invitations and competition scores. These provide progress tracking and multiplayer features. We do not measure your actual steps or access your bank account: results are self-reported.
- **Optional reminders:** email, preferred hour/time zone and opt-in setting, delivery/retry records. You can switch reminders off in Settings. Device notification permission is managed by your browser; the app currently offers a test notification, not background push delivery.
- **Technical information:** service providers may process IP addresses, browser information, security and delivery logs. Session credentials are kept in server memory and browser tab sessionStorage; Google sign-in also uses a temporary PKCE value in localStorage (10-minute validity). Log out on shared devices.

We use account and activity data to provide the service you request (GDPR Article 6(1)(b)), operational security and proportionate personalisation under legitimate interests (6(1)(f)), and optional reminders under consent (6(1)(a)). You can withdraw reminder consent in Settings and object to processing based on legitimate interests. Quest suggestions are automated personalisation; they do not make decisions with legal or similarly significant effects. Do not put medical information, passwords or other sensitive information in names or feedback.

### Storage, recipients and visibility
The database and authentication are hosted by **Supabase**; the Python app runs on **Streamlit Community Cloud**. Authorised project administrators can access data for support and operation. Private server secrets are not included in the GitHub source. **GitHub Actions** runs reminder and competition settlement jobs with restricted credentials.

Other signed-in users see your nickname, avatar and weekly XP on the global leaderboard. Squad members see participation and squad rankings; your competition partner sees shared scores. Do not use a real name/photo if you do not want other users to see it. Your email and location are not included in leaderboard responses.

**Requesty and the selected free model provider (currently NVIDIA)** receive city/country, preferences, levels, recent quest text and feedback for quest generation; translations receive quest text; reflections receive activity summaries and targets. The app does not deliberately send your name, email or photo in AI requests. Do not include identifying details in quest text/feedback. AI can be inaccurate; activity targets and XP follow the app's rules. Provider-side retention is governed by their arrangements; we cannot promise zero retention.

**Brevo** processes recipient email addresses and message content for verification and optional reminders. **Google** handles optional Google sign-in and serves the app's web fonts; **Photon/Komoot** receives typed city searches. Providers may process network information and data outside the EEA. A database location alone does not guarantee EU-only processing. Contact the controller for the current hosting region, provider agreements and applicable international-transfer safeguards before submitting sensitive information. These contractual and transfer arrangements still require controller review; this notice is not a certification of GDPR compliance. We do not sell your app data or use it for advertising.

Provider information: [Supabase](https://supabase.com/privacy), [Streamlit](https://streamlit.io/privacy-policy), [Requesty](https://www.requesty.ai), [NVIDIA](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/), [Brevo](https://www.brevo.com/legal/privacypolicy/), [Google](https://policies.google.com/privacy), [Komoot](https://www.komoot.com/privacy).

### Retention and deletion
Account and activity data remain while your account exists, until a verified erasure request is fulfilled, except information we must lawfully retain. Optional reminders stop when disabled; an already handed-off email may still arrive. Contact messages are kept while resolving your request and for any justified legal record; the controller reviews the need to retain them. Provider backups and operational logs may expire later under their own retention schedules; deletion is not a promise to instantly erase every backup or a delivered email.

Deletion removes your Auth account, profile, quests, scores, rewards and reminder records from the live application. A shared squad is transferred to a remaining member where possible; otherwise it is removed. Competitions involving you are removed, while other participants' already-earned XP remains. We cannot delete copies other people have independently saved.

### Your rights and how to contact us
Email **81324@novasbe.pt** from your account email to request access, a copy/portability where applicable, correction, erasure, restriction or to object. If you cannot access that email, contact us to arrange proportionate identity verification. Do not send a password or ID document unless a necessary, secure verification method has been agreed. The Settings links open an email draft: **you must send it**. They do not automatically delete your account.

We normally respond within one month; a lawful extension or refusal will be explained. You may complain to your local supervisory authority, including Portugal's [CNPD](https://www.cnpd.pt/). Providing core account data is needed to use an account; optional photos and reminders are not required. Contact us if you disagree with personalisation or want your account removed. Changes to this notice will be dated here.
