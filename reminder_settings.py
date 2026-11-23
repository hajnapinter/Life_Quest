"""Opt-in calendar settings for the real scheduled email worker."""
from zoneinfo import available_timezones
import streamlit as st
from urllib.parse import urlencode
from personalization import tr


def render_reminder_settings(api):
    lang=st.session_state.get('language','en'); profile=st.session_state.profile
    status,error=api('POST','/rest/v1/rpc/get_reminder_status',{},st.session_state.access_token)
    healthy=not error and isinstance(status,dict) and status.get('healthy')
    if not healthy:
        st.info(tr(('Reminder delivery is being connected. You can save your preferences now.',
                    'O envio de lembretes está a ser ligado. Já podes guardar as tuas preferências.',
                    'L’envoi des rappels est en cours de connexion. Tu peux enregistrer tes préférences.',
                    'Der Erinnerungsversand wird eingerichtet. Du kannst deine Einstellungen bereits speichern.'),lang))
    with st.form('email_reminder_settings'):
        enabled=st.toggle(tr(('Daily email reminders','Lembretes diários por email','Rappels quotidiens par e-mail','Tägliche E-Mail-Erinnerungen'),lang),
                          value=bool(profile.get('email_reminders')))
        hours=list(range(24)); hour=int(profile.get('reminder_hour',9))
        selected=st.selectbox(tr(('Send after','Enviar após','Envoyer après','Senden nach'),lang),hours,index=hours.index(hour),format_func=lambda h:f'{h:02d}:00')
        zones=['UTC',*sorted(z for z in available_timezones() if z!='UTC')]
        zone=profile.get('reminder_timezone','UTC'); zone=zone if zone in zones else 'UTC'
        selected_zone=st.selectbox(tr(('Time zone','Fuso horário','Fuseau horaire','Zeitzone'),lang),zones,index=zones.index(zone))
        st.caption(tr(('One email per day. Delivery is checked hourly, so it may arrive later than the selected hour. Turn this off at any time.',
                       'Um email por dia. O envio é verificado de hora a hora, por isso pode chegar depois da hora escolhida. Podes desativar quando quiseres.',
                       'Un e-mail par jour. L’envoi est vérifié chaque heure et peut arriver après l’heure choisie. Tu peux désactiver à tout moment.',
                       'Eine E-Mail pro Tag. Der Versand wird stündlich geprüft und kann später als zur gewählten Stunde erfolgen. Jederzeit ausschaltbar.'),lang))
        save=st.form_submit_button(tr(('Save reminder settings','Guardar lembretes','Enregistrer les rappels','Erinnerungen speichern'),lang))
    if save:
        changes={'email_reminders':enabled,'reminder_hour':selected,'reminder_timezone':selected_zone}
        query=urlencode({'id':'eq.'+st.session_state.user['id']})
        _,error=api('PATCH','/rest/v1/profiles?'+query,changes,st.session_state.access_token)
        if error:
            st.error(tr(('Could not save reminders. Please retry.','Não foi possível guardar os lembretes. Tenta novamente.',
                         'Impossible d’enregistrer les rappels. Réessaie.','Erinnerungen konnten nicht gespeichert werden. Bitte versuche es erneut.'),lang))
        else:
            profile.update(changes)
            st.success(tr(('Reminder settings saved.','Lembretes guardados.','Rappels enregistrés.','Erinnerungen gespeichert.'),lang))
