"""Public notice must not depend on authentication; rights links must be honest."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pytest
from streamlit.testing.v1 import AppTest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from privacy import TEXT, notice_text, request_url

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('lang', ['en', 'pt', 'fr', 'de'])
def test_public_policy_available_without_configuration(lang):
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20)
    at.query_params['privacy'] = '1'
    at.session_state['language'] = lang
    at.secrets['supabase'] = {'url': 'YOUR_URL', 'anon_key': 'YOUR_KEY'}
    at.run()
    assert not at.exception
    assert not at.error
    assert at.title[0].value == TEXT[lang][0]
    body = notice_text(lang)
    for required in ['Hajna Pinter', '81324@novasbe.pt', 'Requesty', 'Brevo', 'Supabase', 'sessionStorage', 'CNPD']:
        assert required in body
    assert not at.text_input  # Never shows credentials or login on the public notice.


@pytest.mark.parametrize('lang', TEXT)
def test_rights_request_is_user_sent_email_not_backend_deletion(lang):
    for deletion in (True, False):
        url = urlparse(request_url(deletion, lang))
        assert url.scheme == 'mailto'
        assert url.path == '81324@novasbe.pt'
        assert parse_qs(url.query)['subject'] == ['Life Quest — ' + TEXT[lang][2 if deletion else 3]]


def test_erasure_procedure_is_owner_only_and_transfers_shared_squads():
    sql = (ROOT / 'supabase/privacy.sql').read_text().lower()
    assert 'from public,anon,authenticated,service_role' in sql
    assert "confirmation is distinct from 'erase '||subject::text" in sql
    assert 'set created_by=successor' in sql
    assert 'r.user_id<>subject' in sql
    assert "at time zone 'utc',r.awarded_at)" in sql
