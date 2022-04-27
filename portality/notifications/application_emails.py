# ~~ Email:Notifications~~
from flask import url_for
import json

from portality import models, app_email, constants
from portality.core import app
from portality.dao import Facetview2
from portality.ui.messages import Messages
from portality.lib import dates


def send_editor_group_email(obj):
    """ Send an email to the editor of a group """
    if type(obj) is models.Suggestion:
        # this section has now been superseded by the notification being sent
        template = "email/editor_application_assigned_group.jinja2"
        subject = app.config.get("SERVICE_NAME", "") + " - new application assigned to your group"
    elif type(obj) is models.Journal:
        template = "email/editor_journal_assigned_group.jinja2"
        subject = app.config.get("SERVICE_NAME", "") + " - new journal assigned to your group"
    else:
        app.logger.error("Attempted to send editor group email for something that's not an Application or Journal")
        return

    eg = models.EditorGroup.pull_by_key("name", obj.editor_group)
    if eg is None:
        return
    editor = eg.get_editor_account()

    url_root = app.config.get("BASE_URL")
    to = [editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name=template,
                        editor=editor.id,
                        journal_name=obj.bibjson().title,
                        url_root=url_root)


def send_assoc_editor_email(obj):
    """ Inform an associate editor that a journal or application has been assigned to them """
    if type(obj) is models.Suggestion:
        template = "email/assoc_editor_application_assigned.jinja2"
        subject = app.config.get("SERVICE_NAME", "") + " - new application assigned to you"
    elif type(obj) is models.Journal:
        template = "email/assoc_editor_journal_assigned.jinja2"
        subject = app.config.get("SERVICE_NAME", "") + " - new journal assigned to you"
    else:
        app.logger.error("Attempted to send email to editors for something that's not an Application or Journal")
        return

    if obj.editor is None:
        return

    assoc_editor = models.Account.pull(obj.editor)
    eg = models.EditorGroup.pull_by_key("name", obj.editor_group)

    if assoc_editor is None or eg is None:
        return

    url_root = app.config.get("BASE_URL")
    to = [assoc_editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name=template,
                        associate_editor=assoc_editor.id,
                        journal_name=obj.bibjson().title,
                        group_name=eg.name,
                        url_root=url_root)

def send_publisher_update_request_editor_assigned_email(application):
    """ Send email to publisher informing them an editor has been assigned """

    owner = models.Account.pull(application.owner)
    send_list = [
        {
            "owner" : owner,
            "name" : owner.name,
            "email" : owner.email,
            "sent_alert" : Messages.SENT_PUBLISHER_ASSIGNED_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_ASSIGNED_EMAIL
        }
    ]

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - your update request has been assigned an editor for review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/publisher_update_request_editor_assigned.jinja2",
                            owner=instructions["owner"],
                            application=application)
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts



def send_publisher_application_editor_assigned_email(application):
    """ Send email to publisher informing them an editor has been assigned """
    send_list = []

    owner = models.Account.pull(application.owner)
    if owner is not None:
        send_list.append(
            {
                "owner" : owner,
                "name" : owner.name,
                "email" : owner.email,
                "sent_alert" : Messages.SENT_PUBLISHER_ASSIGNED_EMAIL,
                "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_ASSIGNED_EMAIL
            }
        )

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - your application has been assigned an editor for review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/publisher_application_editor_assigned.jinja2",
                            application=application,
                            owner=instructions["owner"])
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts


def send_editor_completed_email(application):
    """ inform the editor in charge of an application that it has been completed by an associate editor """
    journal_name = application.bibjson().title
    url_root = app.config.get("BASE_URL")
    query_for_id = Facetview2.make_query(query_string=application.id)
    string_id_query = json.dumps(query_for_id).replace(' ', '')       # Avoid '+' being added to URLs by removing spaces
    url_for_application = url_root + url_for("editor.group_suggestions", source=string_id_query)

    # This is to the editor in charge of this application's assigned editor group
    editor_group_name = application.editor_group
    editor_group_id = models.EditorGroup.group_exists_by_name(name=editor_group_name)
    editor_group = models.EditorGroup.pull(editor_group_id)
    editor_acc = editor_group.get_editor_account()

    editor_id = editor_acc.id
    to = [editor_acc.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - application marked 'completed'"

    # The status change will have come from the associate editor assigned to the journal
    assoc_id = application.editor

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/editor_application_completed.jinja2",
                        editor=editor_id,
                        associate_editor=assoc_id,
                        application_title=journal_name,
                        url_for_application=url_for_application)

def send_publisher_update_request_inprogress_email(application):
    """Tell the publisher the UR is underway"""
    owner = models.Account.pull(application.owner)
    send_list = [
        {
            "owner" : owner,
            "name" : owner.name,
            "email" : owner.email,
            "sent_alert" : Messages.SENT_PUBLISHER_IN_PROGRESS_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL
        }
    ]

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your update request is under review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_update_request_inprogress.jinja2",
                                owner=instructions["owner"],
                                application=application)
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts

def send_publisher_application_inprogress_email(application):
    """Tell the publisher the application is underway"""
    send_list = []

    owner = models.Account.pull(application.owner)
    if owner is not None:
        send_list.append(
            {
                "owner" : owner,
                "name" : owner.name,
                "email" : owner.email,
                "sent_alert" : Messages.SENT_PUBLISHER_IN_PROGRESS_EMAIL,
                "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL
            }
        )

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your application is under review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_application_inprogress.jinja2",
                                owner=instructions["owner"],
                                application=application)
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts


def send_received_email(application):
    """ Email the publisher when an application is received """
    owner = models.Account.pull(application.owner)

    to = [owner.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your application to DOAJ has been received"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/publisher_application_received.jinja2",
                        owner=owner,
                        application=application)


def send_publisher_update_request_revisions_required(application):
    """Tell the publisher their update request requires revisions"""
    journal_title = application.bibjson().title

    owner = models.Account.pull(application.owner)
    if owner is None:
        raise app_email.EmailException("Application {x} does not have an owner, cannot send email".format(x=application.id))

    # This is to the publisher contact on the application
    publisher_name = owner.name
    publisher_email = owner.email

    to = [publisher_email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your update request requires revisions"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/publisher_update_request_revisions.jinja2",
                        application=application,
                        owner=owner)


def send_publisher_reject_email(application, note=None, update_request=False):
    """Tell the publisher their application was rejected"""
    send_instructions = []

    owner = models.Account.pull(application.owner)
    if owner is not None:
        send_instructions.append({
            "owner" : owner,
            "name" : owner.name,
            "email" : owner.email,
            "type" : "owner"
        })

    if len(send_instructions) == 0:
        raise app_email.EmailException("Application {x} does not have an owner or suggester, cannot send email".format(x=application.id))

    # determine if this is an application or an update request
    app_type = "application" if update_request is False else "update"

    for instructions in send_instructions:
        to = [instructions["email"]]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - your " + app_type + " was rejected"

        if update_request:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_update_request_rejected.jinja2",
                                owner=instructions["owner"],
                                application=application,
                                note=note)
        else:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_application_rejected.jinja2",
                                owner=instructions["owner"],
                                application=application,
                                note=note)

    return send_instructions


def send_account_created_email(account):
    reset_url = url_for('account.reset', reset_token=account.reset_token, _external=True)
    forgot_pw_url = url_for('account.forgot', _external=True)

    password_create_timeout_seconds = int(
        app.config.get("PASSWORD_CREATE_TIMEOUT", app.config.get('PASSWORD_RESET_TIMEOUT', 86400) * 14))
    password_create_timeout_days = password_create_timeout_seconds / (60 * 60 * 24)

    to = [account.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - account created, please verify your email address"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/account_created.jinja2",
                        reset_url=reset_url,
                        email=account.email,
                        timeout_days=password_create_timeout_days,
                        forgot_pw_url=forgot_pw_url
                        )


def send_account_password_reset_email(account):
    reset_url = url_for('account.reset', reset_token=account.reset_token, _external=True)

    to = [account.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', app.config['ADMIN_EMAIL'])
    subject = app.config.get("SERVICE_NAME", "") + " - password reset"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/account_password_reset.jinja2",
                        email=account.email,
                        reset_url=reset_url,
                        forgot_pw_url=url_for('account.forgot', _external=True)
                        )
