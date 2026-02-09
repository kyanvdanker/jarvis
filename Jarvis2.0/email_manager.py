import smtplib
import imaplib
import email
from email.message import EmailMessage

EMAIL_ADDRESS = "YOUR_EMAIL"
EMAIL_PASSWORD = "YOUR_APP_PASSWORD"
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def read_inbox(limit=5):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    mail.select("inbox")
    status, data = mail.search(None, "ALL")
    ids = data[0].split()[-limit:]
    messages = []
    for msg_id in reversed(ids):
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg.get("Subject", "")
        from_ = msg.get("From", "")
        messages.append(f"From: {from_}, Subject: {subject}")
    mail.logout()
    return "\n".join(messages)

def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    return f"Email sent to {to}."
