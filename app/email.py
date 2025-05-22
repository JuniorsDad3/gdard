# app/email.py

from flask_mail import Message
from flask import render_template, current_app
from app import mail

def send_email(subject: str, recipients: list, **context):
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_USERNAME'],
        recipients=recipients
    )

    # Comment these lines out if you’re not using email templates
    # msg.body = render_template(template + '.txt', **context)
    # msg.html = render_template(template + '.html', **context)

    # Instead, provide simple content directly
    msg.body = f"Welcome to GDARD, {context.get('user').username}!"

    mail.send(msg)