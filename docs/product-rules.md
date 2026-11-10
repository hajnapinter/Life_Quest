# Life Quest product rules

## Users and profiles

- A user can create a personal profile.
- A user can choose one or more life areas.
- A user can view and edit their own profile.
- A user cannot view or edit another user's private profile data.

## Challenges

- A user can view challenges matching their selected areas.
- A user can complete a challenge only once.
- Completing a challenge adds the challenge's points to the user's score.
- A completed challenge cannot award points twice.
- A user can receive one random challenge per day.

## Progress

- A user can view their total points.
- A user can view their current level.
- A user can view their current streak.
- A user can view their weekly progress.

## Squads

- A user can create a squad.
- A user can join a squad using an invite code.
- Squad members can view the squad's shared progress.
- A squad member cannot change another member's points.

## Leaderboard

- Users can view the weekly leaderboard.
- The leaderboard shows points earned during the current week.
- Users can only appear on the leaderboard after completing at least one challenge.

## Example acceptance tests

### Completing a challenge

Accepted:

- A user completes an unfinished challenge.
- The user's points increase by the challenge value.
- The challenge appears as completed.

Rejected:

- A user tries to complete the same challenge twice.
- The user does not receive points a second time.
