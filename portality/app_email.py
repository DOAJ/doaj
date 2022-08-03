# ~~Email:Library~~
from flask import render_template, flash
from flask_mail import Mail, Message, Attachment
from portality.core import app

import uuid
import markdown


class EmailException(Exception):
    pass


def send_markdown_mail(to, fro, subject, template_name=None, bcc=None, files=None, msg_body=None, markdown_template_name=None, **template_params):
    html_body = None
    if markdown_template_name:
        try:
            markdown_body = render_template(markdown_template_name, **template_params)
        except:
            with app.test_request_context():
                markdown_body = render_template(markdown_template_name, **template_params)

        md = markdown.Markdown()
        html_body = md.convert(markdown_body)

    send_mail(to, fro, subject, template_name=template_name, bcc=bcc, files=files, msg_body=msg_body, html_body=html_body, **template_params)

# Flask-Mail version of email service from util.py
def send_mail(to, fro, subject, template_name=None, bcc=None, files=None, msg_body=None, html_body=None, **template_params):
    """
    ~~-> Email:ExternalService~~
    ~~-> FlaskMail:Library~~
    :param to:
    :param fro:
    :param subject:
    :param template_name:
    :param bcc:
    :param files:
    :param msg_body:
    :param template_params:
    :return:
    """
    bcc = [] if bcc is None else bcc
    files = [] if files is None else files

    # ensure that email isn't sent if it is disabled
    if not app.config.get("ENABLE_EMAIL", False):
        app.logger.info("Email template {0} called to send, but email has been disabled.\nto:{1}\tsubject:{2}".format(template_name, to, subject))
        return

    assert type(to) == list
    assert type(files) == list
    if bcc and not isinstance(bcc, list):
        bcc = [bcc]

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
        bcc.append(app.config.get('CC_ALL_EMAILS_TO'))

    # Get the body text from the msg_body parameter (for a contact form),
    # or render from a template.
    # TODO: This could also find and render an HTML template if present
    if msg_body:
        plaintext_body = msg_body
    else:
        try:
            plaintext_body = render_template(template_name, **template_params)
        except:
            with app.test_request_context():
                plaintext_body = render_template(template_name, **template_params)

    # strip all the leading and trailing whitespace from the body, which the templates
    # leave lying around
    plaintext_body = plaintext_body.strip()

    # create a message
    msg = Message(subject=subject,
                  recipients=to,
                  body=plaintext_body,
                  html=html_body,
                  sender=fro,
                  cc=None,
                  bcc=bcc,
                  attachments=files,
                  reply_to=None,
                  date=None,
                  charset=None,
                  extra_headers=None
                  )

    try:
        mail = Mail(app)
        with app.app_context():
            mail.send(msg)
            app.logger.info("Email template {0} sent.\nto:{1}\tsubject:{2}".format(template_name, to, subject))
    except Exception as e:
        raise EmailException(e)


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


def email_archive(data_dir, archv_name):
    """
    Compress and email the reports to the specified email address.
    :param data_dir: Directory containing the reports
    :param archv_name: Filename for the archive and resulting email attachment
    """
    import shutil, os

    email_to = app.config.get('REPORTS_EMAIL_TO', ['helpdesk@doaj.org'])
    email_from = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    email_sub = app.config.get('SERVICE_NAME', '') + ' - generated {0}'.format(archv_name)
    msg = "Attached: {0}.zip\n".format(archv_name)

    # Create an archive of the reports
    archv = shutil.make_archive(archv_name, "zip", root_dir=data_dir)

    # Read the archive to create an attachment, send it with the app email
    with open(archv, 'rb') as f:
        dat = f.read()
        attach = [make_attachment(filename=archv_name, content_type='application/zip', data=dat)]
        send_mail(to=email_to, fro=email_from, subject=email_sub, msg_body=msg, files=attach)

    # Clean up the archive
    os.remove(archv)
