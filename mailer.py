"""
mailer.py
Sends an email digest of new, relevant job postings via SMTP
(works with Gmail app passwords or any standard SMTP provider).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
MAIL_TO = os.environ.get("MAIL_TO", SMTP_USER)


def build_email_body(jobs):
    lines = []
    for j in jobs:
        lines.append(
            f"• {j['title']} — {j['company']}\n"
            f"  Location: {j['location']} | Match: {j['score']}/100\n"
            f"  Why: {j['reason']}\n"
            f"  Apply: {j['url']}\n"
        )
    return "\n".join(lines)


def send_digest(jobs):
    if not jobs:
        print("No relevant new jobs -- skipping email.")
        return

    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP_USER / SMTP_PASS environment variables not set.")

    subject = f"{len(jobs)} new AI job match{'es' if len(jobs) != 1 else ''} — Dubai/UAE"
    body = (
        f"Found {len(jobs)} new job posting(s) matching your profile:\n\n"
        + build_email_body(jobs)
    )

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, MAIL_TO, msg.as_string())

    print(f"Sent digest email to {MAIL_TO} with {len(jobs)} job(s).")
