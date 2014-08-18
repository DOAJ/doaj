import uuid

from flask import flash, request, url_for

from portality import util, app_email
from portality.models import Account
from portality.core import app

ERROR_MSG_TEMPLATE = \
"""Problem while creating account while turning suggestion into journal.
There should be a {missing_thing} on user {username} but there isn't.
Created the user but not sending the email.
""".replace("\n", ' ')


def create_account_on_suggestion_approval(suggestion, journal):
    o = Account.pull(suggestion.owner)
    if o:
        flash('Account {username} already exists, so simply associating the new journal with it.'.format(username=o.id), 'success')
        o.add_journal(journal.id)
        if not o.has_role('publisher'):
            o.add_role('publisher')
        o.save()
        return o

    suggestion_contact = util.listpop(suggestion.contacts())
    if not suggestion_contact.get('email'):
        msg = ERROR_MSG_TEMPLATE.format(username=o.id, missing_thing='journal contact email in the application')
        app.logger.error(msg)
        flash(msg)
        return o

    send_info_to = suggestion_contact.get('email')
    o = Account.make_account(
        suggestion.owner,
        name=suggestion_contact.get('name'),
        email=send_info_to,
        roles=['publisher'],
        associated_journal_ids=[journal.id]
    )

    o.save()

    url_root = request.url_root
    if url_root.endswith("/"):
        url_root = url_root[:-1]

    if not o.reset_token:
        msg = ERROR_MSG_TEMPLATE.format(username=o.id, missing_thing='reset token')
        app.logger.error(msg)
        flash(msg)
        return o

    reset_url = url_root + url_for('account.reset', reset_token=o.reset_token)
    forgot_pw_url = url_root + url_for('account.forgot')


    password_create_timeout_seconds = int(app.config.get("PASSWORD_CREATE_TIMEOUT", app.config.get('PASSWORD_RESET_TIMEOUT', 86400) * 14))
    password_create_timeout_days = password_create_timeout_seconds / (60*60*24)

    to = [send_info_to]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - account created"


    try:
        if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/account_created.txt",
                                reset_url=reset_url,
                                username=o.id,
                                timeout_days=password_create_timeout_days,
                                forgot_pw_url=forgot_pw_url
            )
            flash('Sent email to ' + send_info_to + ' to tell them about the new account.', 'success')
        else:
            flash('Did not email to ' + send_info_to + ' to tell them about the new account, as publisher emailing is disabled.', 'error')
        if app.config.get('DEBUG',False):
            util.flash_with_url('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
    except Exception as e:
        magic = str(uuid.uuid1())
        util.flash_with_url('Hm, sending the account creation email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!', 'error')
        if app.config.get('DEBUG',False):
            util.flash_with_url('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
        app.logger.error(magic + "\n" + repr(e))
        raise e

    flash('Account {username} created'.format(username=o.id), 'success')
    return o

def send_suggestion_approved_email(journal_name, email):
    url_root = request.url_root
    if url_root.endswith("/"):
        url_root = url_root[:-1]

    to = [email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - journal accepted"

    try:
        if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/suggestion_accepted.txt",
                                journal_name=journal_name.encode('utf-8', 'replace'),
                                url_root=url_root
            )
            flash('Sent email to ' + email + ' to tell them about their journal getting accepted into DOAJ.', 'success')
        else:
            flash('Did not send email to ' + email + ' to tell them about their journal getting accepted into DOAJ, as publisher emails are disabled.', 'error')
    except Exception as e:
        magic = str(uuid.uuid1())
        util.flash_with_url('Hm, sending the journal acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!', 'error')
        app.logger.error(magic + "\n" + repr(e))
        raise e