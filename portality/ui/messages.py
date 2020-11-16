from flask import flash


class Messages(object):
    ADMIN__QUICK_REJECT__NO_OWNER = """There is no user attached to this application. 
        <a href="https://testdoaj.cottagelabs.com/account/register">Create the user account first</a>."""

    APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted. You may make further changes until the DOAJ Editorial Team picks it up
        for review. Click 'Edit this update request' to make further changes.
        """, 'success')

    ARTICLE_METADATA_SUBMITTED_FLASH = ("Article created/updated", "success")
    ARTICLE_METADATA_MERGE_CONFLICT = ("""Article could not be submitted, as it matches more than one existing article.
    Please check your metadata, and contact us if you cannot resolve the issue yourself.""", "error")
    ARTICLE_METADATA_UPDATE_CONFLICT = ("""Article could not be updated, as it matches another existing article.
        Please check your metadata, and contact us if you cannot resolve the issue yourself.""", "error")

    SENT_ACCEPTED_APPLICATION_EMAIL = """Sent email to '{email}' to tell them that their journal was accepted."""
    SENT_REJECTED_APPLICATION_EMAIL_TO_OWNER = """Sent email to user '{user}' ({name}, {email}) to tell them that their journal application was rejected."""
    SENT_REJECTED_APPLICATION_EMAIL_TO_SUGGESTER = """Sent email to suggester {name} ({email}) to tell them that their journal application was rejected."""
    SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Sent email to '{email}' to tell them that their journal update was accepted."""
    SENT_REJECTED_UPDATE_REQUEST_EMAIL = """Sent email to user '{user}' ({name}, {email}) to tell them that their journal update was rejected."""
    SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = """Sent email to user '{user}' to tell them that their journal update requires revisions.  You will need to contact them separately with details."""
    SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = """Sent email to journal contact '{email}' to tell them their journal was accepted."""
    SENT_JOURNAL_CONTACT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Sent email to journal contact '{email}' to tell that an update to their journal was accepted."""
    SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = """An email has been sent to the Journal Contact alerting them that you are working on their application."""
    SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = """An email has been sent to the Journal Contact alerting them that an editor has been assigned to their application."""
    SENT_PUBLISHER_IN_PROGRESS_EMAIL = """An email has been sent to the Owner alerting them that you are working on their application."""
    SENT_PUBLISHER_ASSIGNED_EMAIL = """An email has been sent to the Owner alerting them that an editor has been assigned to their application."""

    NOT_SENT_ACCEPTED_APPLICATION_EMAIL = """Did not send email to '{email}' to tell them that their journal was accepted.  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_APPLICATION_EMAILS = """Did not send email to user '{user}' or application suggester to tell them that their journal was rejected  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Did not send email to '{email}' to tell them that their update was accepted  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL = """Did not send email to user '{user}' to tell them that their update was rejected. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = """Did not send email to user '{user}' to tell them that their update required revisions. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = """Did not send email to '{email}' to tell them that their application/update request was accepted. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = """An email could not be sent to the Journal Contact alerting them that you are working on their application. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = """An email could not be sent to the Journal Contact alerting them that an editor has been assigned to their application. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_PUBLISHER_IN_PROGRESS_EMAIL = """An email could not be sent to the Owner alerting them that you are working on their application. Email may be disabled, or there is a problem with the email address. """
    NOT_SENT_PUBLISHER_ASSIGNED_EMAIL = """An email could not be sent to the Owner alerting them that an editor has been assigned to their application. Email may be disabled, or there is a problem with the email address"""

    IN_PROGRESS_NOT_SENT_EMAIL_DISABLED = """Did not send email to Owner or Journal Contact about the status change, as publisher emails are disabled."""

    DIFF_TABLE_NOT_PRESENT = """-- Not held in journal metadata --"""

    REJECT_NOTE_WRAPPER = """{editor}: This application was rejected with the reason '{note}'"""

    EXCEPTION_ARTICLE_BATCH_DUPLICATE = "One or more articles in this batch have duplicate identifiers"
    EXCEPTION_ARTICLE_BATCH_FAIL = "One or more articles failed to ingest; entire batch ingest halted"
    EXCEPTION_ARTICLE_BATCH_CONFLICT = "One or more articles in this batch matched multiple articles as duplicates; entire batch ingest halted"
    EXCEPTION_DETECT_DUPLICATE_NO_ID = "The article you provided has neither doi nor fulltext url, and as a result cannot be deduplicated"
    EXCEPTION_ARTICLE_MERGE_CONFLICT = "The article matched multiple existing articles as duplicates, and we cannot tell which one to update"
    EXCEPTION_NO_DOI_NO_FULLTEXT = "The article must have a DOI and/or a Full-Text URL"
    EXCEPTION_ARTICLE_OVERRIDE = "Cannot update the article. An article with this URL and DOI already exists. If you are sure you want to replace it please delete it and then re-create it."

    PREVENT_DEEP_PAGING_IN_API = """You cannot access results beyond {max_records} records via this API.
    If you would like to see more results, you can download all of our data from
    {data_dump_url}. You can also harvest from our OAI-PMH endpoints; articles: {oai_article_url}, journals: {oai_journal_url}"""

    CONSENT_COOKIE_VALUE = """By using the DOAJ website you have agreed to our cookie policy."""

    FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__USER_EMAIL_ERROR = "We were unable to send you an email confirmation - possible problem with the email address provided"
    FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__LOG_EMAIL_ERROR = 'Error sending application received email.'

    @classmethod
    def flash(cls, tup):
        if isinstance(tup, tuple):
            flash(tup[0], tup[1])
        else:
            flash(tup)

    @classmethod
    def flash_with_url(cls, message, category):
        flash(message, category + '+contains-url')

    @classmethod
    def flash_with_param(cls, message, category="error", **kwargs):
        for key, value in kwargs.items():
            if key != "message" or key != "category":
                message = message + (" {0}: {1},".format(key, value))
        flash(message, category)
