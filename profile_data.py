"""Shared account metadata helpers; all seven pillars are available to everyone."""
import streamlit as st


def pillar_limit(current=0):
    return 7


def country_of(location):
    return (location or '').split(',')[-1].strip()


def save_user_data(api,data):
    user,error=api('PUT','/auth/v1/user',{'data':data},st.session_state.access_token)
    if error:
        return error
    if isinstance(user,dict) and user.get('id'):
        st.session_state.user=user
    else:
        st.session_state.user.setdefault('user_metadata',{}).update(data)
    return None
