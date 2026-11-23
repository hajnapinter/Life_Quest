"""Share only invite codes; joining always requires an explicit authenticated action."""
import json
from pathlib import Path
import re
from urllib.parse import urlencode
import streamlit as st
from auth_helpers import valid_app_url
from personalization import tr


def valid_invitation(value):
    if not isinstance(value,dict):
        return None
    kind=value.get('kind');code=value.get('code')
    if kind not in ('squad','competition') or not isinstance(code,str):
        return None
    code=code.strip().upper()
    size=8 if kind=='squad' else 12
    return {'kind':kind,'code':code} if re.fullmatch('[A-F0-9]{'+str(size)+'}',code) else None


def capture_invitation():
    value=valid_invitation({'kind':st.query_params.get('join'),'code':st.query_params.get('invite')})
    if value:
        st.session_state.pending_invitation=value


def base_url():
    try:
        configured=st.secrets.get('app',{}).get('url')
    except FileNotFoundError:
        configured=None
    if configured and valid_app_url(configured):
        return configured
    try:
        configured=json.loads((Path(__file__).parent/'auth_config.json').read_text()).get('app_url')
    except (OSError,ValueError,AttributeError):
        return None
    return configured if isinstance(configured,str) and valid_app_url(configured) else None


def invitation_url(root,kind,code):
    invitation=valid_invitation({'kind':kind,'code':code})
    if not root or not valid_app_url(root) or not invitation:
        return None
    return root+'?'+urlencode({'join':invitation['kind'],'invite':invitation['code']})


def render_share(kind,code):
    language=st.session_state.get('language','en')
    link=invitation_url(base_url(),kind,code)
    if link:
        st.caption(tr(('Copy this invitation link with the copy button, then send it to your friend.',
                       'Copia este link com o botão de copiar e envia-o ao teu amigo.',
                       'Copie ce lien avec le bouton de copie, puis envoie-le à ton ami.',
                       'Kopiere diesen Einladungslink mit der Kopiertaste und sende ihn deinem Freund.'),language))
        st.code(link,language=None,wrap_lines=True)
    with st.expander(tr(('Or share just the code','Ou partilha apenas o código','Ou partage seulement le code','Oder teile nur den Code'),language)):
        st.code(code,language=None)


def clear_invitation():
    st.session_state.pop('pending_invitation',None)
    for key in ('join','invite'):
        if key in st.query_params:
            del st.query_params[key]


def render_invitation(api=None):
    invitation=valid_invitation(st.session_state.get('pending_invitation'))
    if not invitation:
        return
    language=st.session_state.get('language','en')
    with st.container(key='card_invitation'):
        title=tr(('Squad invitation','Convite para uma equipa','Invitation à une équipe','Teameinladung'),language) if invitation['kind']=='squad' else tr(('Competition invitation','Convite para uma competição','Invitation à un défi','Wettbewerbseinladung'),language)
        st.subheader(title)
        if api is None:
            st.info(tr(('Sign in or create your account to review and accept this invitation.',
                        'Entra ou cria uma conta para veres e aceitares este convite.',
                        'Connecte-toi ou crée ton compte pour consulter et accepter cette invitation.',
                        'Melde dich an oder erstelle ein Konto, um diese Einladung anzusehen und anzunehmen.'),language))
        else:
            st.caption(tr(('Accept to join. Your other squads, competitions and history stay as they are.',
                           'Aceita para participar. As outras equipas, competições e histórico mantêm-se.',
                           'Accepte pour participer. Tes autres équipes, défis et ton historique sont conservés.',
                           'Nimm teil. Deine anderen Teams, Wettbewerbe und dein Verlauf bleiben erhalten.'),language))
            if st.button(tr(('Accept invitation','Aceitar convite','Accepter l’invitation','Einladung annehmen'),language),key='accept_link_invitation',type='primary'):
                squad=invitation['kind']=='squad'
                rpc='join_squad' if squad else 'join_friend_duel'
                payload={'invite_code_input':invitation['code']} if squad else {'invite':invitation['code']}
                _,error=api('POST','/rest/v1/rpc/'+rpc,payload,st.session_state.access_token)
                if error:
                    # Never include raw RPC errors or another account's details.
                    st.error(tr(('This invitation could not be accepted. It may be closed, invalid or intended for someone else.',
                                 'Não foi possível aceitar. O convite pode estar fechado, ser inválido ou destinado a outra pessoa.',
                                 'Impossible d’accepter. L’invitation peut être fermée, invalide ou destinée à une autre personne.',
                                 'Die Einladung konnte nicht angenommen werden. Sie ist möglicherweise geschlossen, ungültig oder für jemand anderen.'),language))
                else:
                    clear_invitation()
                    st.session_state.current_page='👥 Squad' if squad else '⚔️ Competition'
                    st.session_state.main_navigation=st.session_state.current_page
                    st.session_state.social_notice=tr(('Invitation accepted.','Convite aceite.','Invitation acceptée.','Einladung angenommen.'),language)
                    st.rerun()
        if st.button(tr(('Dismiss invitation','Ignorar convite','Fermer l’invitation','Einladung schließen'),language),key='dismiss_link_invitation'):
            clear_invitation();st.rerun()
