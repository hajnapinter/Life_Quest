"""Free scheduled reminder worker. Only confirmed, opted-in accounts can be claimed.

Credentials come from CI Secrets, never source files. The database handles the
calendar, consent, daily limits and retries; uncertain SMTP deliveries are not
retried automatically, to avoid duplicate messages.
"""
import argparse
from email.message import EmailMessage
import json
import os
import smtplib
import ssl
from urllib.request import Request,urlopen

COPY={
 'en':('Your next small step is ready 🌱','Hi {name},\n\nYour Life Quest board is ready. Choose one small quest that fits today.\n\nOpen Life Quest: {url}\n\nYou can turn these reminders off in Settings.'),
 'pt':('O teu próximo pequeno passo está pronto 🌱','Olá {name},\n\nAs tuas missões estão prontas. Escolhe um pequeno desafio que combine com o teu dia.\n\nAbre o Life Quest: {url}\n\nPodes desativar estes lembretes nas Definições.'),
 'fr':('Ton prochain petit pas est prêt 🌱','Salut {name},\n\nTes quêtes sont prêtes. Choisis une petite quête qui te convient aujourd’hui.\n\nOuvre Life Quest : {url}\n\nTu peux désactiver ces rappels dans les Paramètres.'),
 'de':('Dein nächster kleiner Schritt wartet 🌱','Hallo {name},\n\nDeine Quests sind bereit. Wähle eine kleine Aufgabe, die heute zu dir passt.\n\nLife Quest öffnen: {url}\n\nDu kannst diese Erinnerungen in den Einstellungen ausschalten.')}


def rpc(config,name,payload):
    request=Request(config['SUPABASE_URL'].rstrip('/')+'/rest/v1/rpc/'+name,
                    headers={'apikey':config['SUPABASE_ANON_KEY'],'Content-Type':'application/json'},
                    data=json.dumps({'worker_key':config['REMINDER_WORKER_KEY'],**payload}).encode(),method='POST')
    with urlopen(request,timeout=20) as response:
        return json.load(response)


def message(recipient,config):
    subject,body=COPY.get(recipient.get('language'),COPY['en'])
    mail=EmailMessage()
    mail['Subject']=subject
    mail['From']='Life Quest <'+config['SMTP_SENDER']+'>'
    mail['To']=recipient['email']
    mail['Message-ID']='<lifequest-reminder-'+recipient['id']+'@life-quest-team.streamlit.app>'
    mail.set_content(body.format(name=recipient.get('name') or '🌱',url=config['APP_URL']))
    return mail


def run(config,check_only=False):
    if not check_only:
        rpc(config,'settle_due_competitions',{})
    with smtplib.SMTP(config['SMTP_HOST'],int(config.get('SMTP_PORT','587')),timeout=20) as smtp:
        smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo()
        smtp.login(config['SMTP_USERNAME'],config['SMTP_PASSWORD'])
        if check_only:
            rpc(config,'check_reminder_worker',{})
            print('SMTP and limited reminder credential verified. No mail sent.')
            return
        recipients=rpc(config,'claim_reminders',{})
        if not isinstance(recipients,list):
            raise ValueError('Invalid reminder batch')
        outcomes={'sent':0,'failed':0,'uncertain':0}
        for recipient in recipients:
            try:
                mail=message(recipient,config)
            except (ValueError,KeyError):
                outcome='failed'
            else:
                try:
                    smtp.send_message(mail)
                    outcome='sent'
                except (smtplib.SMTPRecipientsRefused,smtplib.SMTPSenderRefused,smtplib.SMTPDataError):
                    outcome='failed'
                except (OSError,smtplib.SMTPException):
                    outcome='uncertain'
            rpc(config,'finish_reminder',{'event_id':recipient['id'],'outcome':outcome})
            outcomes[outcome]+=1
        print(json.dumps(outcomes))  # Never log recipients, names, tokens or SMTP responses.


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    required=['SUPABASE_URL','SUPABASE_ANON_KEY','REMINDER_WORKER_KEY','SMTP_HOST','SMTP_USERNAME','SMTP_PASSWORD','SMTP_SENDER','APP_URL']
    if any(not os.environ.get(key) for key in required):
        raise SystemExit('Reminder Secrets are not configured.')
    try:
        run(dict(os.environ),args.check)
    except Exception:
        raise SystemExit('Reminder worker failed. Check private configuration and delivery logs.') from None
