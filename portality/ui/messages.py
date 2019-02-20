from flask import flash


class Messages(object):
    APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted. You may make further changes until the DOAJ Editorial Team picks it up
        for review. Click 'Edit this update request' to make further changes.
        """, 'success')

    SENT_ACCEPTED_APPLICATION_EMAIL = u"""Sent email to '{email}' to tell them that their journal was accepted."""
    SENT_REJECTED_APPLICATION_EMAIL_TO_OWNER = u"""Sent email to user '{user}' ({name}, {email}) to tell them that their journal application was rejected."""
    SENT_REJECTED_APPLICATION_EMAIL_TO_SUGGESTER = u"""Sent email to suggester {name} ({email}) to tell them that their journal application was rejected."""
    SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Sent email to '{email}' to tell them that their journal update was accepted."""
    SENT_REJECTED_UPDATE_REQUEST_EMAIL = u"""Sent email to user '{user}' ({name}, {email}) to tell them that their journal update was rejected."""
    SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = u"""Sent email to user '{user}' to tell them that their journal update requires revisions.  You will need to contact them separately with details."""
    SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = u"""Sent email to journal contact '{email}' to tell them their journal was accepted."""
    SENT_JOURNAL_CONTACT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Sent email to journal contact '{email}' to tell that an update to their journal was accepted."""
    SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = u"""An email has been sent to the Journal Contact alerting them that you are working on their application."""
    SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = u"""An email has been sent to the Journal Contact alerting them that an editor has been assigned to their application."""
    SENT_PUBLISHER_IN_PROGRESS_EMAIL = u"""An email has been sent to the Owner alerting them that you are working on their application."""
    SENT_PUBLISHER_ASSIGNED_EMAIL = u"""An email has been sent to the Owner alerting them that an editor has been assigned to their application."""

    NOT_SENT_ACCEPTED_APPLICATION_EMAIL = u"""Did not send email to '{email}' to tell them that their journal was accepted.  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_APPLICATION_EMAILS = u"""Did not send email to user '{user}' or application suggester to tell them that their journal was rejected  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Did not send email to '{email}' to tell them that their update was accepted  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL = u"""Did not send email to user '{user}' to tell them that their update was rejected. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = u"""Did not send email to user '{user}' to tell them that their update required revisions. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = u"""Did not send email to '{email}' to tell them that their application/update request was accepted. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = u"""An email could not be sent to the Journal Contact alerting them that you are working on their application. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = u"""An email could not be sent to the Journal Contact alerting them that an editor has been assigned to their application. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL = u"""An email could not be sent to the Owner alerting them that you are working on their application. Email may be disabled, or there is a problem with the email address. """
    NOT_SENT_PUBLISHER_ASSIGNED_EMAIL = u"""An email could not be sent to the Owner alerting them that an editor has been assigned to their application. Email may be disabled, or there is a problem with the email address"""

    DIFF_TABLE_NOT_PRESENT = """-- Not held in journal metadata --"""

    REJECT_NOTE_WRAPPER = u"""{editor}: This application was rejected with the reason '{note}'"""

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')
