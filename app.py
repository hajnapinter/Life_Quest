from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from datetime import date, datetime, timedelta, timezone
from collections import Counter

import streamlit as st


st.set_page_config(page_title="Life Quest", page_icon="🗺️", layout="centered")

st.markdown(
      """
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #243B2D;
    }

    h1, h2, h3 {
        color: #245C43;
    }

    /* Forest green buttons */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background-color: #245C43 !important;
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        border-color: #245C43;
        color: #245C43;
    }

    /* Mint statistics cards */
    div[data-testid="stMetric"] {
        background-color: #DFF7EA;
        padding: 14px;
        border-radius: 14px;
    }

    /* Mint sidebar */
    section[data-testid="stSidebar"] {
        background-color: #DFF7EA;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #245C43;
    }

    /* Forest green progress bar */
    div[data-testid="stProgress"] div[role="progressbar"] > div {
        background-color: #245C43 !important;
    }

    /* Forest green selected statistics controls */
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        background-color: #245C43 !important;
        color: #FFFFFF !important;
    }

    /* Mint table borders */
    div[data-testid="stDataFrame"] {
        border: 1px solid #C7EEDC;
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def initialise_state() -> None:
    defaults = {
        "access_token": None,
        "user": None,
        "profile": None,
        "challenges": [],
        "completed_challenges": set(),
        "completion_dates": [],
        "leaderboard": [],
        "squad": [],
        "squad_invite_code": None,
        "squad_error": None,
        "auth_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def supabase_config() -> tuple[str, str] | None:
    try:
        config = st.secrets["supabase"]
        url = str(config["url"]).strip()
        anon_key = str(config["anon_key"]).strip()
    except (KeyError, FileNotFoundError):
        return None

    if not url or not anon_key or "YOUR_" in url or "YOUR_" in anon_key:
        return None
    return url.rstrip("/"), anon_key


def api_request(
    method: str,
    path: str,
    payload: dict | None = None,
    access_token: str | None = None,
) -> tuple[object | None, str | None]:
    config = supabase_config()
    if config is None:
        return None, "Supabase secrets are not configured."

    base_url, anon_key = config
    headers = {"apikey": anon_key, "Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read().decode("utf-8")
            return (json.loads(response_body) if response_body else None), None
    except HTTPError as error:
        message = error.read().decode("utf-8")
        try:
            details = json.loads(message)
            message = details.get("msg") or details.get("message") or details.get("error_description") or message
        except json.JSONDecodeError:
            pass
        return None, message
    except URLError:
        return None, "The Supabase service could not be reached. Check your internet connection."


def authenticate(email: str, password: str, sign_up: bool) -> None:
    if sign_up:
        data, error = api_request("POST", "/auth/v1/signup", {"email": email, "password": password})
        if error:
            st.session_state.auth_message = error
            return
        if not isinstance(data, dict) or not data.get("access_token"):
            st.session_state.auth_message = "Account created. Check your email before signing in."
            return
    else:
        query = urlencode({"grant_type": "password"})
        data, error = api_request("POST", f"/auth/v1/token?{query}", {"email": email, "password": password})
        if error:
            st.session_state.auth_message = error
            return

    if isinstance(data, dict) and data.get("access_token") and data.get("user"):
        st.session_state.access_token = data["access_token"]
        st.session_state.user = data["user"]
        st.session_state.auth_message = None
        st.rerun()
    else:
        st.session_state.auth_message = (
            "The account exists, but Supabase did not return a login session. "
            "Confirm the email and try again."
        )


def render_auth() -> None:
    st.title("🌱 Welcome to Life Quest")
    st.subheader("Turn your everyday life into an adventure")

    st.write(
        "Life Quest helps you build better habits, discover new experiences, "
        "and grow through small daily challenges. Complete quests, earn points, "
        "level up, and stay motivated with friends. "
        "Because every small step brings you closer to your goals."
    )

    st.write("Create an account to begin your adventure!")

    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Log in", type="primary")
        sign_up = st.form_submit_button("Create account")

    if login or sign_up:
        if not email.strip() or len(password) < 6:
            st.error("Enter a valid email and a password with at least 6 characters.")
        else:
            authenticate(email.strip(), password, sign_up)

    if st.session_state.auth_message: 
        st.info(st.session_state.auth_message)


def load_user_data() -> bool:
    token = st.session_state.access_token
    user_id = st.session_state.user["id"]
    profile_query = urlencode({"select": "*", "id": f"eq.{user_id}"})
    profiles, error = api_request("GET", f"/rest/v1/profiles?{profile_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.profile = profiles[0] if profiles else None

    challenge_query = urlencode({"select": "*", "is_active": "eq.true", "order": "id"})
    challenges, error = api_request("GET", f"/rest/v1/challenges?{challenge_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.challenges = challenges or []

    completed_query = urlencode({"select": "challenge_id,completed_at", "user_id": f"eq.{user_id}"})
    completed, error = api_request("GET", f"/rest/v1/completed_challenges?{completed_query}", access_token=token)
    if error:
        st.error(error)
        return False
    st.session_state.completed_challenges = {row["challenge_id"] for row in completed or []}
    st.session_state.completion_dates = [row["completed_at"] for row in completed or [] if row.get("completed_at")]

    leaderboard, error = api_request(
        "POST", "/rest/v1/rpc/get_weekly_leaderboard", {}, access_token=token
    )
    if error:
        st.error(error)
        return False
    st.session_state.leaderboard = leaderboard or []

    squad, error = api_request("POST", "/rest/v1/rpc/get_my_squad", {}, access_token=token)
    st.session_state.squad_error = error
    st.session_state.squad = squad or [] if not error else []
    if st.session_state.squad:
        st.session_state.squad_invite_code = st.session_state.squad[0].get("invite_code")
    return True


def save_profile(location: str, categories: list[str]) -> None:
    user = st.session_state.user
    profile = {
        "id": user["id"],
        "display_name": user.get("email", "Life Quest user").split("@")[0],
        "location": location.strip(),
        "selected_categories": categories,
    }
    data, error = api_request("POST", "/rest/v1/profiles", profile, st.session_state.access_token)
    if error:
        st.error(error)
        return
    st.session_state.profile = data[0] if isinstance(data, list) and data else profile
    st.rerun()


def render_profile_setup() -> None:
    st.title("Complete your profile")
    st.write("Tell us where you are and which areas you would like to improve.")
    categories = ["Adventure", "Finance", "Fitness", "Health", "Languages", "Personal Growth", "Social"]

    with st.form("profile_form"):
        location = st.text_input("Where are you currently?", placeholder="e.g. Lisbon")
        selected = st.multiselect("Which areas would you like to improve?", categories, default=categories)
        submitted = st.form_submit_button("Start your quest", type="primary")

    if submitted:
        if not location.strip() or not selected:
            st.error("Enter your location and choose at least one area.")
        else:
            save_profile(location, selected)


def complete_challenge(challenge_id: int) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/complete_challenge",
        {"challenge_id_input": challenge_id},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    if isinstance(data, list) and data:
        st.session_state.profile["points"] = data[0]["new_points"]
    st.session_state.completed_challenges.add(challenge_id)
    st.rerun()


def create_squad(name: str) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/create_squad",
        {"squad_name_input": name.strip()},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    if isinstance(data, list) and data:
        st.session_state.squad_invite_code = data[0]["invite_code"]
    load_user_data()
    st.rerun()


def join_squad(invite_code: str) -> None:
    data, error = api_request(
        "POST",
        "/rest/v1/rpc/join_squad",
        {"invite_code_input": invite_code.strip().upper()},
        st.session_state.access_token,
    )
    if error:
        st.error(error)
        return
    load_user_data()
    st.rerun()


def render_squad() -> None:
    st.divider()
    st.subheader("Squad mode")
    if st.session_state.squad_error:
        st.warning(
            "Squad mode is ready, but the squad list could not be loaded yet. "
            "You can still try creating or joining a squad."
        )
    if st.session_state.squad:
        squad_name = st.session_state.squad[0]["squad_name"]
        st.write(f"You are in **{squad_name}**.")
        st.info(f"Invite code: **{st.session_state.squad_invite_code}**")
        members = [
            {
                "Member": member["display_name"],
                "Points": member["member_points"],
            }
            for member in st.session_state.squad
        ]
        st.dataframe(members, hide_index=True, width="stretch", alt="Squad members and points")
        return

    st.write("Create a squad with friends or join one using an invite code.")
    create_column, join_column = st.columns(2)
    with create_column:
        with st.form("create_squad_form"):
            squad_name = st.text_input("New squad name")
            create = st.form_submit_button("Create squad", type="primary")
        if create:
            if len(squad_name.strip()) < 2:
                st.error("The squad name must have at least 2 characters.")
            else:
                create_squad(squad_name)

    with join_column:
        with st.form("join_squad_form"):
            invite_code = st.text_input("Invite code")
            join = st.form_submit_button("Join squad")
        if join:
            if not invite_code.strip():
                st.error("Enter an invite code.")
            else:
                join_squad(invite_code)
def calculate_statistics(completion_dates: list[str]) -> tuple[int, int, list[int]]:
    days = []

    for value in completion_dates:
        completed_day = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
        days.append(completed_day)

    today = datetime.now(timezone.utc).date()
    completed_days = set(days)

    streak = 0
    current_day = today

    # Keep yesterday's streak if no quest was completed today.
    if current_day not in completed_days:
        current_day -= timedelta(days=1)

    while current_day in completed_days:
        streak += 1
        current_day -= timedelta(days=1)

    weekly_counts = [
        days.count(today - timedelta(days=offset))
        for offset in range(6, -1, -1)
    ]

    return len(days), streak, weekly_counts
def render_quests() -> None:
    profile = st.session_state.profile
    selected_categories = set(profile.get("selected_categories", []))
    challenges = [
        challenge for challenge in st.session_state.challenges
        if challenge["category"] in selected_categories
    ]

    if not challenges:
        st.info("No challenges are available for your selected areas yet.")

    for challenge in challenges:
        challenge_id = challenge["id"]
        challenge_column, action_column = st.columns([4, 1])
        challenge_column.write(f"**{challenge['title']}** · {challenge['category']}")
        challenge_column.caption(f"{challenge['description']} (+{challenge['points']} points)")

        if challenge_id in st.session_state.completed_challenges:
            action_column.success("Completed")
        elif action_column.button("Complete", key=f"complete_{challenge_id}"):
            complete_challenge(challenge_id)
def render_dashboard() -> None:
    profile = st.session_state.profile
    points = profile.get("points", 0)
    level = points // 100 + 1
    progress = (points % 100) / 100

    with st.sidebar:
        st.header("🌲 Life Quest")

        page = st.radio(
            "Navigation",
            ["🏠 Home", "✅ Quests", "👥 Squad", "🏆 Leaderboard"],
            key="current_page",
        )

        st.divider()
        st.header("Profile")
        st.write(f"📍 {profile.get('location', 'Not set')}")
        st.write(f"**{points} points** · Level {level}")

        st.divider()
        st.subheader("🌍 Settings")
        st.subheader("🔔 Notifications")

        if "email_reminders" not in st.session_state:
            st.session_state.email_reminders = bool(
                profile.get("email_reminders", False)
            )

        email_reminders = st.toggle(
            "Daily email reminders",
            key="email_reminders",
            help="Receive reminders to complete your daily quests.",
        )
        if email_reminders != bool(profile.get("email_reminders", False)):
            query = urlencode({"id": f"eq.{st.session_state.user['id']}"})
            _, error = api_request(
                "PATCH",
                f"/rest/v1/profiles?{query}",
                {"email_reminders": email_reminders},
                st.session_state.access_token,
            )
            if error:
                st.error(f"Could not save reminder setting: {error}")
            else:
                profile["email_reminders"] = email_reminders

        if email_reminders:
            st.caption("Email reminders are enabled in your settings.")    


        st.selectbox(
            "Language",
            ["🇬🇧 English", "🇵🇹 Português", "🇫🇷 Français", "🇩🇪 Deutsch"],
            key="language",
        )

        if st.button("Log out"):
            for key in ("access_token", "user", "profile", "challenges", "leaderboard", "squad", "squad_invite_code", "squad_error"):
                st.session_state[key] = None if key in ("access_token", "user", "profile", "squad_invite_code", "squad_error") else []
            st.session_state.completed_challenges = set()
            st.rerun()

    if page == "👥 Squad":
        render_squad()
        return

    st.title("Life Quest")
    if page == "✅ Quests":
        st.subheader("Your quests")
        render_quests()
        return
    st.write(f"Your adventure in **{profile.get('location', 'your area')}** starts now.")
    first, second, third = st.columns(3)
    first.metric("Points", points)
    second.metric("Level", level)
    third.metric("Completed quests", len(st.session_state.completed_challenges))
    st.progress(progress, text=f"{100 - points % 100} points to the next level")

    st.divider()
    if st.session_state.get("current_page", "🏠 Home") == "🏆 Leaderboard":
        st.subheader("Weekly leaderboard")
        st.caption("Points earned since the start of this week")
        if st.session_state.leaderboard:
            leaderboard_rows = [
                {
                "Rank": position,
                "Player": row["display_name"],
                "Points": row["weekly_points"],
                "Quests": row["quests_completed"],
                }
                for position, row in enumerate(st.session_state.leaderboard, start=1)
            ]
            st.dataframe(
                leaderboard_rows,
                hide_index=True,
                width="stretch",
                alt="Weekly Life Quest leaderboard",
            )
        else:
            st.info("Complete a quest to appear on the weekly leaderboard.")

    if page != "🏠 Home":
        return

    st.subheader("📊 Your Statistics")
    period = st.segmented_control(
        "View statistics by",
        ["Day", "Week", "Month"],
        default="Week",
    )

    total_quests, streak, weekly_counts = calculate_statistics(
        st.session_state.completion_dates
    )

    today = datetime.now(timezone.utc).date()

    if period == "Day":
        days_to_show = 1
    elif period == "Week":
        days_to_show = 7
    else:
        days_to_show = 30

    activity_counts = []

    for offset in range(days_to_show - 1, -1, -1):
        selected_day = today - timedelta(days=offset)

        count = sum(
            1
            for value in st.session_state.completion_dates
            if datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date() == selected_day
        )

        activity_counts.append(
            {"Date": selected_day, "Quests": count}
        )

    period_quests = sum(row["Quests"] for row in activity_counts)
    average_quests = period_quests / days_to_show

    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("Total XP", points)
    stat2.metric("Quests in period", period_quests)
    stat3.metric("🔥 Daily streak", f"{streak} days")

    st.metric("Average quests per day", f"{average_quests:.1f}")

    st.write(f"**Quest activity — {period}**")

    st.bar_chart(
        activity_counts,
        x="Date",
        y="Quests",
        x_label="Date",
        y_label="Quests completed",
    )
    st.divider()
    
    
    

initialise_state()

if supabase_config() is None:
    st.error("Supabase is not configured for this deployment.")
    st.info(
        "The person who manages the Streamlit deployment must add the existing "
        "Supabase Project URL and anon key as deployment secrets under "
        "[supabase]. Local files named .streamlit/secrets.toml are not uploaded "
        "automatically."
    )
    st.stop()

if not st.session_state.access_token:
    render_auth()
elif st.session_state.profile is None:
    if load_user_data():
        if st.session_state.profile is None:
            render_profile_setup()
        else:
            render_dashboard()
else:
    render_dashboard()
