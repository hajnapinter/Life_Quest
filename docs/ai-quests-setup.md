# Free personalised quests with Requesty

The course guide recommends Requesty. Life Quest now uses Requesty's free plan and the fixed model `nvidia/nemotron-3.5-lightning-30b-a3b`. It does not use an OpenAI API key or the OpenAI API endpoint. No additional Python package is required: the integration uses the standard library.

## Activation

1. Create a free account at https://app.requesty.ai. Do not add a payment method, buy credits or enable paid routing/fallbacks.
2. Create a Requesty API key. Set `REQUESTY_API_KEY` in the Streamlit server environment, or an `api_key` entry under `[requesty]` in deployment Secrets. Keep the key out of Git, logs, screenshots and chat. The Python server reads it; it is never sent to the browser.
3. Restart Streamlit. Complete onboarding with a real test account. Check that a quest appears for every chosen pillar; complete one, verify that XP is awarded once and a new quest is generated.

The `supabase/ai-quests.sql` migration was applied to the Life-Quest project on 2026-11-11. RLS, its two policies, the completion function and the combined weekly leaderboard were verified. Existing deployments of the repository need that migration too.

## Cost controls and free limits

Requesty's free plan currently provides 200 requests/day and 20/minute per organisation across its free models, without a payment card. Quotas and free model availability can change.

Before **every** generation, the app reads the live `/v1/models` catalogue and verifies the approved model has explicit zero input and output prices in every tier. Any other advertised token price must also be zero. Missing, malformed, changed or non-zero pricing stops generation before the completion request. Only the exact approved model ID is allowed; there is no paid fallback or automatic model routing. Unknown catalogue formats fail closed. This check depends on the provider reporting prices correctly; keeping the account on the free plan without a payment method remains the account-side control.

On 429, the app explains the free limit and keeps existing quests usable. Model output is validated before saving. A generated quest that fails to save stays in the session for retry without spending another generation call. The Requesty key was configured locally on 2026-11-11 in the ignored Streamlit server secrets file with owner-only permissions. A live catalogue check confirmed all model prices were zero, and a live generated Adventure quest passed validation. The model uses reasoning_effort=none and a 2,000-token output limit to avoid truncation. No payment method or credits were added. Configure a separate server-side Requesty secret when deploying elsewhere.

## Five independent habit tracks

Apply `supabase/five-quest-slots.sql` after `supabase/ai-quests.sql` on a new deployment. Both have been applied to the existing Life-Quest project. The upgrade preserves history and retires old unstructured active quests without XP. It also adds the notification preference column already used by the app.

Every selected pillar has five independent slots with different practical focuses (see `quest_plan.py`). First-load and missing slots use the curated habit library immediately, personalised by the onboarding level. Finishing one quest requests one fresh AI variation for that same slot, target and focus; other slots remain unchanged. AI may vary the activity inside a focus, but cannot change its numeric target. Titles are at most 90 characters; descriptions at most 240. No poetic scavenger hunts or abstract sensory tasks.

Step goals start at 2k/4k/6k/8k/10k according to the selected level. A successful walking quest raises its replacement by 2k, capped at 12k. Too-hard feedback lowers it by 1k (floor 1k). Other numeric habit targets increase after each successful completion within their own track, up to the catalogue ceiling. Experience quests gain variety and complexity rather than pointless time limits. Skips do not give XP or advance success counts. The interface treats a checkmark as successful completion; there are no difficulty-rating or swap controls in the personal quest rows. Historical feedback remains in saved history.

The AI request has an 8-second catalogue timeout and 12-second generation timeout. Free-limit errors, invalid output, changed prices or timeouts fall back to practical curated suggestions. The UI briefly states when the habit library was used instead of AI. No paid fallback exists. Repeated habits are deliberately allowed; the old global unique-title restriction is removed.

`save_quest_slots` serialises writes on the profile row and atomically records completion, awards XP and saves the replacement. A partial unique index enforces one active quest per user/pillar/slot (1..5). Replaying a completion is idempotent. Invalid replacement data rolls the entire transaction back. The app retains an unsaved batch for retry without another AI call. Direct authenticated table inserts are disabled in the upgrade.

Home contains a greeting and five active quests per selected pillar. The fixed, horizontally scrollable bottom navigation opens each pillar's page: completed total, XP, rolling seven-day count and comparison, streak, fourteen-day activity chart, per-track current targets and completion history. Existing shared quest completions are included when available. Squad, leaderboard and settings remain accessible.

Validation included mocked UI tests for replacement and pillar isolation, all 35 tracks at five starting levels, and a live authenticated PostgreSQL transaction verifying five slots, replacement, single XP award, idempotent replay, invalid-replacement rollback and ownership checks. All database verification writes were rolled back.

## Data and limitations

Only pillar, numeric level, recent generated quest text and ratings go to Requesty and the model host. Name, email, user ID and location are not included. Provider retention and training policies can differ; review the model's data policy before public release. The UI tells users which service receives these answers.

RLS isolates users' quest histories. Completion remains self-reported. Direct inserts are revoked, but the authenticated slot RPC accepts client-supplied content and difficulty; this remains a self-improvement app, not an anti-cheating system for adversarial competition. A trusted generation backend would be needed for that use case.

Generated quests must have a clear completion criterion, gentle progression, no mandatory spending and an easier adaptation. Prompt constraints do not guarantee safety; review generated samples before public release.

## Sources

- Course guide: https://2477-introduction-programming.gitlab.io/wiki/guides/ai-in-your-app.html
- Free models and quotas: https://docs.requesty.ai/features/free-models
- Pricing: https://www.requesty.ai/pricing
- Model catalogue/prices: https://docs.requesty.ai/api-reference/endpoint/models-list
- Structured JSON: https://docs.requesty.ai/features/structured-outputs

## Compact quest interaction

Personal quests render as one-line checkbox rows on Home and pillar pages. The row contains only the task sentence. Checking queues an atomic completion/replacement; failures restore the unchecked row for retry. Requests remain queued until handled, supporting multiple quick checks and safe retries. The old row fades and the new ID enters with a short slide/fade; reduced-motion preferences are respected. XP is shown in a toast after successful storage, and the Home total is refreshed. Per-pillar statistics and history are unchanged.

Shared squad missions use the same compact checkbox style while retaining their two-participant confirmation rule. Competition score-entry forms remain because that mode compares numeric results.
