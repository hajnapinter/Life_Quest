"""Repository-level security checks: no committed secrets, XP not user-writable."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", "design ideas"}
SECRET_PATTERNS = [
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),     # JWTs, e.g. Supabase keys
    re.compile(r"service_role\s*[:=]\s*['\"][^'\"]+"),             # Supabase service key assignment
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),                          # API keys in the sk-... style
    re.compile(r"anon_key\s*=\s*\"(?!YOUR_|THE_|PASTE_)[^\"]{20,}\""),  # a real anon key in a template
]


def project_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts):
            if path.name != "secrets.toml" and path.suffix not in {".png", ".jpg", ".jpeg", ".lock", ".pyc"}:
                yield path


def test_no_credentials_in_the_repository():
    leaks = []
    for path in project_files():
        text = path.read_text(errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                leaks.append(f"{path.relative_to(ROOT)}: {pattern.pattern}")
    assert not leaks, "Possible credentials committed:\n" + "\n".join(leaks)


def test_local_secrets_file_is_git_ignored():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert ".streamlit/secrets.toml" in ignored


def test_users_cannot_write_their_own_xp():
    sql = (ROOT / "supabase" / "protect-profile-points.sql").read_text().lower()
    assert "revoke insert, update on public.profiles from authenticated" in sql
    grants = re.findall(r"grant\s+(insert|update)\s*\(([^)]*)\)\s*on public\.profiles", sql)
    assert {kind for kind, _ in grants} == {"insert", "update"}
    for _, columns in grants:
        assert "points" not in columns


def test_app_never_sends_points_in_profile_writes():
    app = (ROOT / "app.py").read_text()
    for call in re.findall(r'api_request\(\s*"(?:POST|PATCH)",\s*f?"/rest/v1/profiles[^)]*\)', app, re.S):
        assert "points" not in call
    assert '"points"' not in app.split("def save_onboarding", 1)[1].split("def ", 1)[0]


def test_hardening_migration_closes_the_audit_findings():
    sql = (ROOT / "supabase" / "security-hardening.sql").read_text().lower()
    assert sql.strip().startswith("--") and "begin;" in sql and sql.rstrip().endswith("commit;")
    # H1: no direct inserts into squads / squad members
    assert 'drop policy if exists "users can join squads as themselves" on public.squad_members' in sql
    assert "revoke insert, update, delete on public.squads, public.squad_members from authenticated, anon" in sql
    # H2: daily XP cap, upper bound on targets, old completion function closed
    assert "done_today<20" in sql and "not between 1 and 20000" in sql
    assert "revoke all on function public.finish_ai_quest(uuid,text,boolean) from public, anon, authenticated" in sql
    # M1 / L1 / L2 / L4
    assert "at most 5 squads" in sql
    assert "revoke insert, update, delete on public.completed_challenges from authenticated, anon" in sql
    assert "profiles_display_name_length" in sql and "profiles_known_pillars" in sql
    assert "revoke all on function public.join_squad(text) from public, anon" in sql


def test_uploads_are_capped_by_streamlit():
    config = (ROOT / ".streamlit" / "config.toml").read_text()
    assert re.search(r"^\s*maxUploadSize\s*=\s*8\b", config, re.M)
