-- Protect XP from being edited directly.
--
-- Problem: the "Users can update their own profile" policy lets a signed-in user
-- PATCH any column of their own row through the REST API, including `points`.
-- Fix: users may only write the columns the app actually edits. XP keeps changing
-- through the existing security-definer functions (save_quest_slots, finish_ai_quest,
-- complete_challenge, social_award), which run as the table owner and are not affected.
--
-- Safe to run more than once. Run it once in the Supabase SQL editor.

revoke insert, update on public.profiles from authenticated, anon;

grant insert (id, display_name, location, selected_categories)
    on public.profiles to authenticated;

grant update (display_name, location, selected_categories, email_reminders)
    on public.profiles to authenticated;

-- Row-level security still applies on top of these column grants:
-- users can only insert/update the row whose id equals auth.uid().
