# Shared quests and daily friend competitions

Apply `supabase/social-play.sql` after the existing schema, squad functions and AI quest migrations. Applied to the current project on 2026-11-11. The migration also refreshes active experience quests to remove arbitrary time targets; history and XP are preserved.

## Squad quests

A squad has three shared quests each Monday–Sunday UTC week. A nine-task catalogue rotates weekly and by squad. Joining members receive the same stored quest IDs. Users confirm their own participation after doing a task together. A minimum of two distinct confirmations unlocks 30 XP for each confirming participant, including later participants; repeated confirmations cannot award twice. Only current squad members can see/confirm the group's missions, and closed weeks cannot be confirmed retroactively.

The UI supports several squads, sharing invite codes, joining friends and choosing the current squad. Starting or joining a group by itself awards no XP.

## 1v1 competitions

Create an invite code for any friend, or select several current squadmates to create separate invitations. Each invite must be accepted by its intended friend. There is one persistent competition per unordered friend pair. An open code can be claimed by one other signed-in user; targeted invitations can only be accepted by their target. No emails or messages are sent automatically.

Each active pair gets one shared, stored quest per UTC day. Examples are steps walked, pages read, words learned, new recipes cooked or new places explored. The task rotates using the pair ID and date, preferring a metric that neither participant has in another competition that day. If all five metrics are already in use, a metric can repeat. Different pairs have independent quest IDs and scores; a metric may recur across several pairs. Both members always get exactly the same title, unit and limit for their pair that day.

Players enter a non-negative integer total and may edit their own score until 23:59 UTC. Bounds are enforced by the server (steps 50,000; pages 300; words 200; recipes 5; places 10). Scores are self-reported. Missing entries count as zero for comparison but receive no daily participation XP.

After closure, a submitting winner receives 35 XP, a submitting other player 15, or tied submitting players 25 each. The weekly winner is determined by daily wins, with a 50 XP bonus. A tied week gives 20 bonus XP only to players who submitted at least once that week. No entries means no weekly award. New Monday counters start fresh; recent daily and weekly history stays visible.

Settlement is lazy: expired days and weeks are finalised when either participant opens or refreshes the social page. This avoids requiring a paid scheduler. If no one opens the app at midnight, awards arrive on the next visit. This behaviour and UTC deadlines are shown in the UI. There are no push reminders yet.

## Storage and verification

Social tables have RLS enabled and no direct client privileges. Authenticated callers use narrowly scoped RPCs. Internal XP and settlement functions are not executable by clients. XP rewards have unique participant/event keys; profile and quest locks prevent double awards. Global weekly rankings include social rewards.

Verification used three temporary accounts within a rolled-back PostgreSQL transaction: shared squad IDs, two-person confirmation, idempotent awards, invitation acceptance, pair-identical daily quests, editable own scores, out-of-range rejection, outsider isolation, multiple friend pairs, closed-day rejection, weekly winners and repeat settlement. No test accounts, invitations or XP were retained.

This is a social self-improvement feature, not a verified athletic or educational competition: the app does not verify steps, reading or vocabulary externally.
