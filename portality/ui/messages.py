from flask import flash


class Messages(object):
    APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted. You may make further changes until the DOAJ Editorial Team picks it up
        for review. Click 'Edit this update request' to make further changes.
        """, 'success')

    SENT_ACCEPTED_APPLICATION_EMAIL = u"""Sent email to '{email}' to tell them that their journal was accepted."""
    SENT_REJECTED_APPLICATION_EMAIL = u"""Sent email to '{email}' to tell them that their journal application was rejected."""
    SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Sent email to '{email}' to tell them that their journal update was accepted."""
    SENT_REJECTED_UPDATE_REQUEST_EMAIL = u"""Sent email to '{email}' to tell them that their journal update was rejected."""
    SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = u"""Sent email to '{email}' to tell them that their journal update requires revisions.  You will need to contact them separately with details."""
    SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = u"""Sent email to journal contact '{email}' to tell them their journal was accepted."""
    SENT_JOURNAL_CONTACT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Sent email to journal contact '{email}' to tell that an update to their journal was accepted."""

    NOT_SENT_ACCEPTED_APPLICATION_EMAIL = u"""Did not send email to '{email}' to tell them that their journal was accepted.  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_APPLICATION_EMAIL = u"""Did not send email to '{email}' to tell them that their journal was rejected  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = u"""Did not send email to '{email}' to tell them that their update was accepted  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL = u"""Did not send email to '{email}' to tell them that their update was rejected. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = u"""Did not send email to '{email}' to tell them that their update required revisions. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = u"""Did not send email to '{email}' to tell them that their application/update request was accepted. Email may be disabled, or there is a problem with the email address"""

    DIFF_TABLE_NOT_PRESENT = """-- Not held in journal metadata --"""

    REJECT_NOTE_WRAPPER = u"""{editor}: This application was rejected with the reason '{note}'"""

    EXCEPTION_ARTICLE_BATCH_DUPLICATE = u"One or more articles in this batch have duplicate identifiers"
    EXCEPTION_ARTICLE_BATCH_FAIL = u"One or more articles failed to ingest; entire batch ingest halted"
    EXCEPTION_DETECT_DUPLICATE_NO_ID = u"The article you provided has neither doi nor fulltext url, and as a result cannot be deduplicated"

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')
