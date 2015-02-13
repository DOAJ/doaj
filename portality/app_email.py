<<<<<<< HEAD
from flask import render_template
from flask_mail import Mail, Message
=======
from flask import render_template, request, flash
from flask_mail import Mail, Message, Attachment
>>>>>>> 492f20c04c3ee1252f159219d7e1dc75e4daa1a3
from portality.core import app

import uuid

# Flask-Mail version of email service from util.py
def send_mail(to, fro, subject, template_name=None, bcc=[], files=[], msg_body=None, **template_params):

    # ensure that email isn't sent if it is disabled
    if not app.config.get("ENABLE_EMAIL", False):
        return

    assert type(to) == list
    assert type(files) == list
    if bcc and not isinstance(bcc, list):
        bcc = [bcc]

<<<<<<< HEAD
    if app.config.get('CC_ALL_EMAILS_TO'):
=======
    to_is_invalid = True
    for t in to:
        if t:
            to_is_invalid = False
        # a list of None, None, None or even just a [None] is no good!

    if to_is_invalid:
        magic = str(uuid.uuid1())
        app.logger.error('Bad To list while trying to send email with subject \"{0}\". Magic num for log grep {1}'.format(subject, magic))
        flash("Invalid email address - no email specified at all. Trying to send email with subject \"{0}\". Magic number to help identify error: {1}".format(subject, magic), 'error')
        return

    if app.config.get('CC_ALL_EMAILS_TO', None) is not None:
>>>>>>> 492f20c04c3ee1252f159219d7e1dc75e4daa1a3
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

<<<<<<< HEAD
    mail = Mail(app)
    mail.send(msg)
=======
    if appcontext:
        mail = Mail(app)
        mail.send(msg)
    else:
        with app.test_request_context():
            mail = Mail(app)
            mail.send(msg)

def to_unicode(val):
    if isinstance(val, unicode):
        return val
    elif isinstance(val, basestring):
        try:
            return val.decode("utf8", "replace")
        except UnicodeDecodeError:
            raise ValueError("Could not decode string")
    else:
        return val

def make_attachment(filename, content_type, data, disposition=None, headers=None):
    """
    Provide a function which can make attachments, insulating the caller from the flask-mail
    underlying implementation.

    :param filename:
    :param content_type:
    :param data:
    :param disposition:
    :param headers:
    :return:
    """
    return Attachment(filename, content_type, data, disposition, headers)
>>>>>>> 492f20c04c3ee1252f159219d7e1dc75e4daa1a3
