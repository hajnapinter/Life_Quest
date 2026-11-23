"""An in-memory stand-in for Supabase, used by the workflow tests.

It answers the same HTTP requests app.py sends (Auth + REST + RPC), following the
rules in supabase/*.sql closely enough to drive the real app end to end:
- save_quest_slots: completing a quest awards 10 + 5 x difficulty XP and saves the
  replacement; only one active quest per (pillar, slot); completing twice is a no-op.
- squads: invite codes, membership checks, two confirmations unlock 30 XP each.
- every REST/RPC call needs a valid token, like Row Level Security.
It never touches the network or the real database.
"""
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
import io
import itertools
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

URL = "https://fake.supabase.test"
ANON_KEY = "fake-anon-key"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class FakeSupabase:
    def __init__(self):
        self.users = {}          # email -> user dict (with password)
        self.tokens = {}         # token -> email
        self.profiles = {}       # user id -> profile
        self.quests = []         # ai_quests rows
        self.squads = []         # {id, name, invite_code, members: [user ids]}
        self.squad_quests = []   # {id, squad_id, title, description, confirmed: [user ids]}
        self.rewards = []
        self.calls = []          # (method, path) log, for assertions
        self._ids = itertools.count(1)

    # ---------- helpers ----------

    def new_id(self, prefix):
        return f"{prefix}-{next(self._ids)}"

    def add_user(self, email, password="password123", metadata=None, profile=None):
        user = {"id": self.new_id("user"), "email": email, "password": password, "user_metadata": metadata or {}}
        self.users[email] = user
        if profile is not None:
            self.profiles[user["id"]] = {"id": user["id"], "points": 0, "email_reminders": False,
                                         "location": "", "selected_categories": [], **profile}
        return user

    def public_user(self, user):
        return {k: v for k, v in user.items() if k != "password"}

    def session(self, user):
        token = self.new_id("token")
        self.tokens[token] = user["email"]
        return {"access_token": token, "token_type": "bearer", "user": self.public_user(user)}

    @staticmethod
    def error(code, message, error_code=""):
        raise HTTPError(URL, code, message, {}, io.BytesIO(json.dumps({"msg": message, "error_code": error_code}).encode()))

    # ---------- urlopen replacement ----------

    def urlopen(self, request, timeout=None):
        parsed = urlparse(request.full_url)
        method = request.get_method()
        body = json.loads(request.data.decode()) if request.data else None
        auth = request.get_header("Authorization") or ""
        token = auth.removeprefix("Bearer ").strip() or None
        self.calls.append((method, parsed.path))
        result = self.handle(method, parsed.path, parse_qs(parsed.query), body, token)
        payload = b"" if result is None else json.dumps(result, default=str).encode()
        return nullcontext(io.BytesIO(payload))

    def current_user(self, token):
        email = self.tokens.get(token)
        if not email:
            self.error(401, "JWT expired", "bad_jwt")
        return self.users[email]

    def handle(self, method, path, query, body, token):
        # ----- Auth -----
        if path == "/auth/v1/settings":
            return {"external": {"google": False}}
        if path == "/auth/v1/signup" and method == "POST":
            if body["email"] in self.users:
                self.error(422, "User already registered", "user_already_exists")
            return self.session(self.add_user(body["email"], body["password"]))
        if path == "/auth/v1/token" and method == "POST":
            user = self.users.get(body["email"])
            if not user or user["password"] != body["password"]:
                self.error(400, "Invalid login credentials", "invalid_credentials")
            return self.session(user)
        if path == "/auth/v1/logout" and method == "POST":
            self.tokens.pop(token, None)          # the session can no longer be used
            return None
        if path == "/auth/v1/user":
            user = self.current_user(token)
            if method == "PUT":
                user["user_metadata"] = {**user["user_metadata"], **(body or {}).get("data", {})}
            return self.public_user(user)

        user = self.current_user(token)          # everything below needs a login (like RLS)
        uid = user["id"]

        # ----- REST tables -----
        if path == "/rest/v1/profiles":
            if method == "GET":
                wanted = query.get("id", [""])[0].removeprefix("eq.")
                if wanted != uid:
                    return []                    # RLS: only your own row
                return [self.profiles[uid]] if uid in self.profiles else []
            if method == "POST":
                if body.get("id") != uid:
                    self.error(403, "new row violates row-level security policy", "42501")
                self.profiles[uid] = {"points": 0, "email_reminders": False, **body}
                return None
            if method == "PATCH":
                if "points" in body:
                    self.error(403, "permission denied for table profiles", "42501")  # protect-profile-points.sql
                self.profiles[uid].update(body)
                return None
        if path in ("/rest/v1/challenges", "/rest/v1/completed_challenges"):
            return []
        if path == "/rest/v1/ai_quests" and method == "GET":
            mine = [q for q in self.quests if q["user_id"] == uid]
            offset = int(query.get("offset", ["0"])[0])
            return mine[offset:offset + int(query.get("limit", ["500"])[0])]

        # ----- RPC (database functions) -----
        name = path.removeprefix("/rest/v1/rpc/")
        handler = getattr(self, "rpc_" + name, None)
        if handler is None:
            self.error(404, f"Could not find the function public.{name}", "PGRST202")
        return handler(uid, body or {})

    # ---------- RPC: quests ----------

    def rpc_save_quest_slots(self, uid, body):
        finished = body.get("finished_id")
        if finished:
            old = next((q for q in self.quests if q["id"] == finished and q["user_id"] == uid), None)
            if old is None:
                self.error(400, "Quest not found", "P0001")
            if old["status"] == "active":            # completing twice does nothing (idempotent)
                old.update(status="skipped" if body.get("skip") else "completed",
                           feedback=body.get("rating"), completed_at=now_iso())
                if not body.get("skip"):
                    self.profiles[uid]["points"] += 10 + 5 * old["difficulty"]
        for row in body.get("quest_rows", []):
            taken = any(q["user_id"] == uid and q["category"] == row["category"] and q["slot"] == row["slot"]
                        and q["status"] == "active" for q in self.quests)
            if not taken:
                self.quests.append({**row, "id": self.new_id("quest"), "user_id": uid, "status": "active",
                                    "feedback": None, "created_at": now_iso(), "completed_at": None})
        return self.profiles[uid]["points"]

    def rpc_get_weekly_leaderboard(self, uid, body):
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=today.weekday())
        board = []
        for profile in self.profiles.values():
            done = [q for q in self.quests if q["user_id"] == profile["id"] and q["status"] == "completed"
                    and datetime.fromisoformat(q["completed_at"]).date() >= start]
            if done:
                board.append({"display_name": profile["display_name"],
                              "weekly_points": sum(10 + 5 * q["difficulty"] for q in done), "quests_completed": len(done)})
        return sorted(board, key=lambda r: -r["weekly_points"])

    # ---------- RPC: squads ----------

    def rpc_get_my_squad(self, uid, body):
        squad = next((s for s in self.squads if uid in s["members"]), None)
        return [{"squad_id": squad["id"], "invite_code": squad["invite_code"]}] if squad else []

    def rpc_create_squad(self, uid, body):
        name = (body.get("squad_name_input") or "").strip()
        if not 2 <= len(name) <= 50:
            self.error(400, "Squad name must be 2 to 50 characters", "P0001")
        squad = {"id": self.new_id("squad"), "name": name, "invite_code": f"CODE{len(self.squads) + 1:04d}", "members": [uid]}
        self.squads.append(squad)
        for title in ("Cook a new recipe together", "Visit a free museum day", "Go for a group walk"):
            self.squad_quests.append({"id": self.new_id("sq"), "squad_id": squad["id"], "title": title,
                                      "description": "Do it together.", "confirmed": []})
        return [{"squad_id": squad["id"], "invite_code": squad["invite_code"]}]

    def rpc_join_squad(self, uid, body):
        squad = next((s for s in self.squads if s["invite_code"] == body.get("invite_code_input")), None)
        if squad is None:
            self.error(400, "That invite code is not valid.", "P0001")
        if uid not in squad["members"]:
            squad["members"].append(uid)
        return [{"squad_id": squad["id"]}]

    def rpc_confirm_squad_quest(self, uid, body):
        quest = next((q for q in self.squad_quests if q["id"] == body.get("quest_id")), None)
        squad = next((s for s in self.squads if quest and s["id"] == quest["squad_id"]), None)
        if not quest or uid not in squad["members"]:
            self.error(400, "Not your squad quest", "P0001")
        if uid not in quest["confirmed"]:
            quest["confirmed"].append(uid)
            if len(quest["confirmed"]) == 2:          # two confirmations unlock 30 XP for both
                for member in quest["confirmed"]:
                    self.profiles[member]["points"] += 30
                    self.rewards.append({"user_id":member,"category":"Squad","title":quest["title"],"points":30,"status":"completed","completed_at":now_iso(),"source":"squad_quest"})
        return None

    def rpc_get_social_state(self, uid, body):
        today = datetime.now(timezone.utc).date()
        squads = []
        for s in self.squads:
            if uid in s["members"]:
                squads.append({"id": s["id"], "name": s["name"], "invite_code": s["invite_code"],
                               "members": [{"id": m, "name": self.profiles[m]["display_name"]} for m in s["members"]],
                               "quests": [{"id": q["id"], "title": q["title"], "description": q["description"],
                                           "confirmed": list(q["confirmed"])} for q in self.squad_quests if q["squad_id"] == s["id"]]})
        friends = sorted({m for s in self.squads if uid in s["members"] for m in s["members"] if m != uid})
        return {"today": today.isoformat(), "week_start": (today - timedelta(days=today.weekday())).isoformat(),
                "squads": squads, "duels": [], "friends": [{"id": f, "name": self.profiles[f]["display_name"]} for f in friends],
                "points": self.profiles[uid]["points"]}

    def rpc_get_activity_history(self,uid,body):
        return [q for q in self.rewards if q['user_id']==uid]

    def rpc_get_squad_leaderboard(self,uid,body):
        squad=next((s for s in self.squads if s['id']==body.get('squad_id_input') and uid in s['members']),None)
        if not squad: self.error(400,'Not your squad','P0001')
        result=[]
        for member in squad['members']:
            rows=[q for q in self.quests if q['user_id']==member and q['status']=='completed']+[q for q in self.rewards if q['user_id']==member]
            result.append({'user_id':member,'display_name':self.profiles[member]['display_name'],'weekly_points':sum(q.get('points',10+5*q.get('difficulty',1)) for q in rows),'quests_completed':len(rows)})
        return result

    def rpc_leave_squad(self,uid,body):
        squad=next((s for s in self.squads if s['id']==body.get('squad_id_input') and uid in s['members']),None)
        if not squad: self.error(400,'Not your squad','P0001')
        squad['members'].remove(uid)
