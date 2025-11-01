import os
import smtplib
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()
SMTP_HOST = os.getenv('SMTP_HOST','')
SMTP_PORT = int(os.getenv('SMTP_PORT','587') or 587)
SMTP_USER = os.getenv('SMTP_USER','')
SMTP_PASS = os.getenv('SMTP_PASS','')
EMAIL_TO  = os.getenv('EMAIL_TO','')
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN','')
TG_CHAT_ID   = os.getenv('TG_CHAT_ID','')
def send_email(subject: str, body: str) -> bool:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        return False
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [EMAIL_TO], msg.as_string())
        return True
    except Exception:
        return False
def send_telegram(text: str) -> bool:
    if not (TG_BOT_TOKEN and TG_CHAT_ID):
        return False
    try:
        url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage'
        r = requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': text})
        return r.status_code == 200
    except Exception:
        return False
