from flask import url_for
import json

from portality import models, app_email
from portality.core import app
from portality.dao import Facetview2
from portality.ui.messages import Messages

def send_admin_ready_email(application, editor_id):
    """ send email to the managing editors when an application is ready """
    journal_name = application.bibjson().title
    url_root = app.config.get("BASE_URL")
    query_for_id = Facetview2.make_query(query_string=application.id)
    string_id_query = json.dumps(query_for_id).replace(' ', '')       # Avoid '+' being added to URLs by removing spaces
    url_for_application = url_root + url_for("admin.suggestions", source=string_id_query)

    # This is to the managing editor email list
    to = [app.config.get('MANAGING_EDITOR_EMAIL', 'managing-editors@doaj.org')]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - application ready"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/admin_application_ready.txt",
                        application_title=journal_name,
                        editor=editor_id,
                        url_for_application=url_for_application)


def send_editor_group_email(obj):
    """ Send an email to the editor of a group """
    if type(obj) is models.Suggestion:
        template = "email/editor_application_assigned_group.txt"
        subject = app.config.get("SERVICE_NAME", "") + " - new application assigned to your group"
    elif type(obj) is models.Journal:
        template = "email/editor_journal_assigned_group.txt"
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
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')

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
        template = "email/assoc_editor_application_assigned.txt"
        subject = app.config.get("SERVICE_NAME", "") + " - new application assigned to you"
    elif type(obj) is models.Journal:
        template = "email/assoc_editor_journal_assigned.txt"
        subject = app.config.get("SERVICE_NAME", "") + " - new journal assigned to you"
    else:
        app.logger.error("Attempted to send email to editors for something that's not an Application or Journal")
        return

    assoc_editor = models.Account.pull(obj.editor)
    eg = models.EditorGroup.pull_by_key("name", obj.editor_group)

    url_root = app.config.get("BASE_URL")
    to = [assoc_editor.email]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')

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
            "name" : owner.name,
            "email" : owner.email,
            "sent_alert" : Messages.SENT_PUBLISHER_ASSIGNED_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_ASSIGNED_EMAIL
        }
    ]

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - your update request has been assigned an editor for review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/publisher_update_request_editor_assigned.txt",
                            application_title=application.bibjson().title,
                            publisher_name=instructions["name"])
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts



def send_publisher_application_editor_assigned_email(application):
    """ Send email to publisher informing them an editor has been assigned """

    contact_name = application.get_latest_contact_name()
    contact_email = application.get_latest_contact_email()
    send_list = [
        {
            "name" : contact_name,
            "email" : contact_email,
            "sent_alert" : Messages.SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL
        }
    ]

    owner = models.Account.pull(application.owner)
    if owner is not None:
        send_list.append(
            {
                "name" : owner.name,
                "email" : owner.email,
                "sent_alert" : Messages.SENT_PUBLISHER_ASSIGNED_EMAIL,
                "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_ASSIGNED_EMAIL
            }
        )

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME","") + " - your application has been assigned an editor for review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/publisher_application_editor_assigned.txt",
                            application_title=application.bibjson().title,
                            publisher_name=instructions["name"])
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts


def send_editor_inprogress_email(application):
    """ Inform editor in charge of an application that the status is has been reverted from ready by a ManEd """
    journal_name = application.bibjson().title
    url_root = app.config.get("BASE_URL")
    query_for_id = Facetview2.make_query(query_string=application.id)
    string_id_query = json.dumps(query_for_id).replace(' ', '')       # Avoid '+' being added to URLs by removing spaces
    url_for_application = url_root + url_for("editor.group_suggestions", source=string_id_query)

    # This is to the editor in charge of this AssEd's group
    editor_group_name = application.editor_group
    editor_group_id = models.EditorGroup.group_exists_by_name(name=editor_group_name)

    try:
        editor_group = models.EditorGroup.pull(editor_group_id)
        editor_acc = editor_group.get_editor_account()
        editor_id = editor_acc.id
        to = [editor_acc.email]
    except AttributeError:
        raise

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - Application reverted to 'In Progress' by Managing Editor"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/editor_application_inprogress.txt",
                        editor=editor_id,
                        application_title=journal_name,
                        url_for_application=url_for_application)


def send_assoc_editor_inprogress_email(application):
    """ Inform the associate editor assigned to application that the status has been reverted by an Ed or ManEd """
    journal_name = application.bibjson().title
    url_root = app.config.get("BASE_URL")
    query_for_id = Facetview2.make_query(query_string=application.id)
    string_id_query = json.dumps(query_for_id).replace(' ', '')       # Avoid '+' being added to URLs by removing spaces
    url_for_application = url_root + url_for("editor.group_suggestions", source=string_id_query)

    # This is to the associate editor assigned to this application
    assoc_editor = models.Account.pull(application.editor)
    to = [assoc_editor.email]

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - an application assigned to you has not passed review."

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/assoc_editor_application_inprogress.txt",
                        assoc_editor=assoc_editor.id,
                        application_title=journal_name,
                        url_for_application=url_for_application)


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
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - application marked 'completed'"

    # The status change will have come from the associate editor assigned to the journal
    assoc_id = application.editor

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/editor_application_completed.txt",
                        editor=editor_id,
                        associate_editor=assoc_id,
                        application_title=journal_name,
                        url_for_application=url_for_application)

def send_publisher_update_request_inprogress_email(application):
    """Tell the publisher the UR is underway"""
    journal_title = application.bibjson().title

    owner = models.Account.pull(application.owner)
    send_list = [
        {
            "name" : owner.name,
            "email" : owner.email,
            "sent_alert" : Messages.SENT_PUBLISHER_IN_PROGRESS_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL
        }
    ]

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your update request is under review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_update_request_inprogress.txt",
                                publisher_name=instructions["name"],
                                journal_title=journal_title)
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts

def send_publisher_application_inprogress_email(application):
    """Tell the publisher the application is underway"""
    journal_title = application.bibjson().title

    contact_name = application.get_latest_contact_name()
    contact_email = application.get_latest_contact_email()
    send_list = [
        {
            "name" : contact_name,
            "email" : contact_email,
            "sent_alert" : Messages.SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL,
            "not_sent_alert" : Messages.NOT_SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL
        }
    ]

    owner = models.Account.pull(application.owner)
    if owner is not None:
        send_list.append(
            {
                "name" : owner.name,
                "email" : owner.email,
                "sent_alert" : Messages.SENT_PUBLISHER_IN_PROGRESS_EMAIL,
                "not_sent_alert" : Messages.NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL
            }
        )

    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your application is under review"

    alerts = []
    for instructions in send_list:
        to = [instructions["email"]]
        try:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_application_inprogress.txt",
                                publisher_name=instructions["name"],
                                journal_title=journal_title)
            alerts.append(instructions["sent_alert"])
        except app_email.EmailException:
            alerts.append(instructions["not_sent_alert"])

    return alerts

def send_received_email(application):
    """ Email the publisher when an application is received """
    suggester = application.suggester

    to = [suggester.get("email")]
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your application to DOAJ has been received"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/publisher_application_received.txt",
                        publisher_name=suggester.get("name", "Applicant"),
                        title=application.bibjson().title,
                        url=application.bibjson().get_single_url(urltype="homepage"))


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
    fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    subject = app.config.get("SERVICE_NAME", "") + " - your update request requires revisions"

    app_email.send_mail(to=to,
                        fro=fro,
                        subject=subject,
                        template_name="email/publisher_update_request_revisions.txt",
                        publisher_name=publisher_name,
                        journal_title=journal_title)


def send_publisher_reject_email(application, note=None, update_request=False, send_to_owner=True, send_to_suggester=False):
    """Tell the publisher their application was rejected"""
    journal_title = application.bibjson().title

    send_instructions = []
    if send_to_owner:
        owner = models.Account.pull(application.owner)
        if owner is not None:
            send_instructions.append({
                "name" : owner.name,
                "email" : owner.email,
                "type" : "owner"
            })

    if send_to_suggester:
        sug = application.suggester
        if sug is not None:
            send_instructions.append({
                "name" : sug["name"],
                "email" : sug["email"],
                "type" : "suggester"
            })

    if len(send_instructions) == 0:
        raise app_email.EmailException("Application {x} does not have an owner or suggester, cannot send email".format(x=application.id))

    # determine if this is an application or an update request
    app_type = "application" if update_request is False else "update"

    for instructions in send_instructions:
        to = [instructions["email"]]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - your " + app_type + " was rejected"

        if update_request:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_update_request_rejected.txt",
                                publisher_name=instructions["name"],
                                journal_title=journal_title,
                                note=note)
        else:
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/publisher_application_rejected.txt",
                                publisher_name=instructions["name"],
                                journal_title=journal_title,
                                note=note)

    return send_instructions