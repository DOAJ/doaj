import uuid

from flask import flash, request, url_for

from portality import util
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
    # TODO: New email template system
    text = \
"""An account has been created for you at DOAJ. You will need this account to see your journals, upload article metadata and update your details.

Your username is: {username}

Please visit {reset_url} and choose a password. You have {timeout_days} days from the date of this email.

If you do not set a password within {timeout_days} days, go to {forgot_pw_url} and enter your username. This will let you set your password.

Regards,
The DOAJ Team
""".format(reset_url=reset_url, username=o.id, timeout_days=password_create_timeout_days, forgot_pw_url=forgot_pw_url)

    try:
        if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            util.send_mail(to=to, fro=fro, subject=subject, text=text)
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

# TODO: New email template system
SUGGESTION_ACCEPTED_EMAIL_TEMPLATE = \
"""
Dear publisher,

The journal {journal_name} has now been added to DOAJ.
You may access the journal in your Publisher Area: {url_root}/publisher/ .
You will need your username and password.
If you do not already have a DOAJ account, you will receive more information in a separate email. (If you do not have your username or the instructions to set your password then please contact us: {url_root}/contact .)

To increase the visibility, impact, distribution and usage* of your journal, we urge you to upload the journal's article metadata to us. You may do this from the Publisher Area in two ways:

1) Upload Article XML: {url_root}/publisher/uploadfile
You must log into your account first. You may either upload XML to DOAJ or provide us with a URL from where we can download it. All XML files uploaded to DOAJ must conform to the DOAJ Native XML schema: {url_root}/static/doaj/doajArticles.xsd. New articles will appear on the site after 1 hour. If there are problems with your file, an error message will be displayed. Correct the error and reupload the file.
Find out more about the XML file structure here: {url_root}/features in the section "File upload info"
If you need further help with XML, we recommend you do a search online as there are many resources available.

2) Enter Article Metadata: {url_root}/publisher/metadata
You may enter article metadata manually. You will need to complete the form for each article. If you make a mistake, re-enter the metadata again and the new file will overwrite the old one. New articles will appear on the site immediately.

If you are adding content to an existing issue, you only need to supply the latest content to us. DOAJ does not accept PDFs.

You can check that your articles have been successfully added to your journal by going to 'Your Journals' in the 'Publisher Area' and clicking the journal title.

*Benefits of supplying DOAJ with metadata:

- Our statistics show more than 900 000 page views a month to DOAJ from all over the world.
- Many web crawlers collect content from DOAJ to be a part of their search engines.
- DOAJ is OAI compliant and once an article is in DOAJ, it is automatically harvestable.
- Over 95% of the DOAJ Publisher community said that DOAJ is important for increasing their journal's visbility
- Many aggregators and database providers regularly harvest DOAJ content in order to include it to their commercial databases.
- DOAJ is often cited as a source of quality, open access journals in research and scholarly publishing circles.

The DOAJ Team
"""


def send_suggestion_approved_email(journal_name, email):
    url_root = request.url_root
    if url_root.endswith("/"):
        url_root = url_root[:-1]

    to = [email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - journal accepted"
    text = SUGGESTION_ACCEPTED_EMAIL_TEMPLATE.format(journal_name=journal_name.encode('utf-8', 'replace'), url_root=url_root)

    try:
        if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            util.send_mail(to=to, fro=fro, subject=subject, text=text)
            flash('Sent email to ' + email + ' to tell them about their journal getting accepted into DOAJ.', 'success')
        else:
            flash('Did not send email to ' + email + ' to tell them about their journal getting accepted into DOAJ, as publisher emails are disabled.', 'error')
    except Exception as e:
        magic = str(uuid.uuid1())
        util.flash_with_url('Hm, sending the journal acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!', 'error')
        app.logger.error(magic + "\n" + repr(e))
        raise e