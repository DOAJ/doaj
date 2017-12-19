from flask import flash

class Messages(object):
    APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted and it is editable until the DOAJ editorial team picks it up for review.
        You will find your update request in your list of updates below.  Select 'edit this update request' to make changes
        """, 'success')

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')