from flask import flash

class Messages(object):
    APPLICATION_UPDATE_SUBMITTED_FLASH = ('Your update request has been submitted and it is editable until the DOAJ editorial team picks it up for review.', 'success')
    APPLICATION_UPDATE_CLOSE_TAB_FLASH = ("Close this tab to return to your Publisher's Area.", 'success')

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')