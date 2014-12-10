from flask import render_template
from flask_mail import Mail, Message
from portality.core import app

# Flask-Mail version of email service from util.py
def send_mail(to, fro, subject, template_name=None, bcc=[], files=[], msg_body=None, **template_params):

    # ensure that email isn't sent if it is disabled
    if not app.config.get("ENABLE_EMAIL", False):
        return

    assert type(to) == list
    assert type(files) == list
    if bcc and not isinstance(bcc, list):
        bcc = [bcc]

    if app.config.get('CC_ALL_EMAILS_TO'):
        bcc.append(app.config.get('CC_ALL_EMAILS_TO'))

    # Get the body text from the msg_body parameter (for a contact form),
    # or render from a template.
    # TODO: This could also find and render a HTML template if present
    if msg_body:
        plaintext_body = msg_body
    else:
        plaintext_body = render_template(template_name, **template_params)

    # create a message
    msg = Message(subject=subject,
                  recipients=to,
                  body=plaintext_body,
                  html=None,
                  sender=fro,
                  cc=None,
                  bcc=bcc,
                  attachments=files,
                  reply_to=None,
                  date=None,
                  charset=None,
                  extra_headers=None
    )

    mail = Mail(app)
    mail.send(msg)