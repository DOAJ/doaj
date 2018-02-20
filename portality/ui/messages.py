from flask import flash

class Messages(object):
    APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted. You may make further changes until the DOAJ Editorial Team picks it up
        for review. Click 'Edit this update request' to make further changes.
        """, 'success')

    SENT_ACCEPTED_APPLICATION_EMAIL = """Sent email to {email} to tell them that their journal was accepted."""

    SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """'Sent email to {email} to tell them that their journal update was accepted."""

    NOT_SENT_ACCEPTED_APPLICATION_EMAIL = """Did not send email to {email} to tell them tht their journal was accepted, as publisher emails are disabled."""

    NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Did not send email to {email} to tell them that their updagte was accepted, as publisher emails are disabled."""

    DIFF_TABLE_NOT_PRESENT = """-- Not held in journal metadata --"""

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')