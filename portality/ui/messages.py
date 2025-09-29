from flask import flash


class Messages(object):
    ADMIN__QUICK_REJECT__NO_OWNER = """There is no user attached to this application. 
        <a href="https://testdoaj.cottagelabs.com/account/register" target="_blank">Assign a user account first</a>."""

    PUBLISHER_APPLICATION_UPDATE_SUBMITTED_FLASH = ("""
        Your update request has been submitted. You may make further changes until the DOAJ Editorial Team picks it up
        for review. Click the 'Edit' button to make further changes or 'Delete' to cancel the request.
        """, 'success')
    PUBLISHER_UPLOAD_ERROR = """An error has occurred and your upload did not succeed. {error_str} <br \> If the problem persists, please send the error details from the Notes column of the History of Uploads box below and a screenshot of the entire error message"""
    NO_FILE_UPLOAD_ID="""No file upload record has been specified"""

    ARTICLE_METADATA_SUBMITTED_FLASH = ("<a href='{url}' target='_blank'>Article created/updated</a>", "success")
    ARTICLE_METADATA_MERGE_CONFLICT = ("""Article could not be submitted, as it matches more than one existing article.
    Please check your metadata, and contact us if you cannot resolve the issue yourself.""", "error")
    ARTICLE_METADATA_UPDATE_CONFLICT = ("""Article could not be updated, as it matches another existing article.
        Please check your metadata, and contact us if you cannot resolve the issue yourself.""", "error")

    CONCURRENT_UPDATE_REQUEST = """You have submitted an Update Request for the same journal in a short period of time.  If this is in error, you don't need to do anything, your first request is being processed.  If this was intentional, please try again in a moment."""

    SENT_ACCEPTED_APPLICATION_EMAIL = """Sent notification to '{user}' to tell them that their journal was accepted."""
    SENT_REJECTED_APPLICATION_EMAIL_TO_OWNER = """Sent notification to user '{user}' to tell them that their journal application was rejected."""
    SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Sent notification to '{user}' to tell them that their journal update was accepted."""
    SENT_REJECTED_UPDATE_REQUEST_EMAIL = """Sent email to user '{user}' ({name}, {email}) to tell them that their journal update was rejected."""
    SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = """Sent email to user '{user}' to tell them that their journal update requires revisions.  You will need to contact them separately with details."""
    SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = """Sent email to journal contact '{email}' to tell them their journal was accepted."""
    SENT_JOURNAL_CONTACT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Sent email to journal contact '{email}' to tell that an update to their journal was accepted."""
    SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = """An email has been sent to the Journal Contact alerting them that you are working on their application."""
    SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = """An email has been sent to the Journal Contact alerting them that an editor has been assigned to their application."""

    NOT_SENT_ACCEPTED_APPLICATION_EMAIL = """Did not send notification to '{user}' to tell them that their journal was accepted.  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_APPLICATION_EMAILS = """Did not send email to user '{user}' or application suggester to tell them that their journal was rejected  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL = """Did not send notification to '{user}' to tell them that their update was accepted  Email may be disabled, or there is a problem with the email address."""
    NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL = """Did not send email to user '{user}' to tell them that their update was rejected. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL = """Did not send email to user '{user}' to tell them that their update required revisions. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL = """Did not send email to '{email}' to tell them that their application/update request was accepted. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_IN_PROGRESS_EMAIL = """An email could not be sent to the Journal Contact alerting them that you are working on their application. Email may be disabled, or there is a problem with the email address"""
    NOT_SENT_JOURNAL_CONTACT_ASSIGNED_EMAIL = """An email could not be sent to the Journal Contact alerting them that an editor has been assigned to their application. Email may be disabled, or there is a problem with the email address"""

    IN_PROGRESS_NOT_SENT_EMAIL_DISABLED = """Did not send email to Owner or Journal Contact about the status change, as publisher emails are disabled."""

    DIFF_TABLE_NOT_PRESENT = """-- Not held in journal metadata --"""

    REJECT_NOTE_WRAPPER = """{editor}: This application was rejected with the reason '{note}'"""

    EXCEPTION_ARTICLE_BATCH_DUPLICATE = "One or more articles in this batch have duplicate identifiers"
    EXCEPTION_ARTICLE_BATCH_FAIL = "One or more articles failed to ingest; entire batch ingest halted"
    EXCEPTION_ARTICLE_BATCH_CONFLICT = "One or more articles in this batch matched multiple articles as duplicates; entire batch ingest halted"
    EXCEPTION_DETECT_DUPLICATE_NO_ID = "The article you provided has neither doi nor fulltext URL, and as a result cannot be deduplicated"
    EXCEPTION_ARTICLE_MERGE_CONFLICT = "The article matched multiple existing articles as duplicates, and we cannot tell which one to update"
    EXCEPTION_NO_DOI_NO_FULLTEXT = "The article must have a DOI and/or a Full-Text URL"
    EXCEPTION_ARTICLE_OVERRIDE = "Cannot update the article. An article with this URL and DOI already exists. If you are sure you want to replace it please delete it and then re-create it."
    EXCEPTION_SCRIPT_TAG_FOUND = "Metadata contains <script> tag. Please remove any <script> tags from your metadata and try again."
    EXCEPTION_ADDING_ARTICLE_TO_WITHDRAWN_JOURNAL = "You are trying to add the articles to a journal that has been withdrawn from DOAJ. We accept articles only for journals currently in DOAJ"

    EXCEPTION_NO_CONTRIBUTORS_FOUND = "No contributors found."
    EXCEPTION_NO_CONTRIBUTORS_EXPLANATION = "DOAJ requires at least one author for each article."

    EXCEPTION_TOO_MANY_ISSNS = "Too many ISSNs. Only 2 ISSNs are allowed: one Print ISSN and one Online ISSN."
    EXCEPTION_MISMATCHED_ISSNS = "ISSNs provided don't match any journal."
    EXCEPTION_ISSNS_OF_THE_SAME_TYPE = "Both ISSNs have the same type: {type}"
    EXCEPTION_IDENTICAL_PISSN_AND_EISSN = "The Print and Online ISSNs supplied are identical. If you supply two ISSNs, they must be different."
    EXCEPTION_NO_ISSNS = "Neither the Print ISSN nor Online ISSN have been supplied. DOAJ requires at least one ISSN."
    EXCEPTION_INVALID_BIBJSON = "Invalid article bibjson: "  # + Dataobj exception message

    EXCEPTION_IDENTIFIER_CHANGE_CLASH = "DOI or Fulltext URL has been changed to match another article that already exists in DOAJ"
    EXCEPTION_IDENTIFIER_CHANGE = "Either the DOI or Fulltext URL has been changed.  This operation is not permitted; please contact an administrator for help."
    EXCEPTION_DUPLICATE_NO_PERMISSION = "You do not have permission to carry out the requested change"

    EXCEPTION_EDITING_ACCEPTED_JOURNAL = "You cannot edit applications which have been accepted into DOAJ."
    EXCEPTION_EDITING_WITHDRAWN_JOURNAL = "This journal has been withdrawn, update request cannot be accepted."
    EXCEPTION_EDITING_DELETED_JOURNAL = "This journal has been deleted, update request cannot be accepted."
    EXCEPTION_EDITING_NON_EXISTING_APPLICATION = "You cannot edit a not-existent application"

    EXCEPTION_NOTIFICATION_NO_ACCOUNT = "Account with id {x} not found"
    EXCEPTION_NOTIFICATION_NO_EMAIL = "Account with id {x} does not have an email address"
    EXCEPTION_NOTIFICATION_NO_NOTIFICATION = "Notification with id {n} does not exist"

    PREVENT_DEEP_PAGING_IN_API = """You cannot access results beyond {max_records} records via this API.
    If you would like to see more results, you can download all of our data from
    {data_dump_url}. You can also harvest from our OAI-PMH endpoints; articles: {oai_article_url}, journals: {oai_journal_url}"""

    CONSENT_COOKIE_VALUE = """By using our website, you have agreed to our cookie policy."""

    FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__USER_EMAIL_ERROR = "We were unable to send you an email confirmation - possible problem with the email address provided"
    FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__LOG_EMAIL_ERROR = 'Error sending application received email.'
    FORMS__APPLICATION_PROCESSORS__ADMIN_APPLICATION__FINALISE__COULD_NOT_UNREJECT = "Could not unreject application, as a new Update Request for the journal now exists"
    FORMS__APPLICATION_PROCESSORS__ASSOCIATE_APPLICATION__FINALISE__STATUS_COMPLETED_NOTIFIED = "A confirmation email has been sent to notify the editor of the change in status."

    BLL__UNREJECT_APPLICATION__NO_APPLICATION = "You must supply an application to unreject_application"
    BLL__UNREJECT_APPLICATION__NO_ACCOUNT = "You must supply an account to unreject_application"
    BLL__UNREJECT_APPLICATION__WRONG_ROLE = "This user is not allowed to unreject applications"
    BLL__UNREJECT_APPLICATION__ILLEGAL_STATE_REJECTED = "The application {id} is in 'rejected' state; place it into the correct new state before calling unreject_application"
    BLL__UNREJECT_APPLICATION__ILLEGAL_STATE_DISALLOWED = "The application {id} is in '{x}' status, which is disallowed in this call context"
    BLL__UNREJECT_APPLICATION__DUPLICATE_UR = """Creating an update request from rejected application {id} is not possible as another application {urid} exists which is an update request for journal {jid}"""
    BLL__UNREJECT_APPLICATION__JOURNAL_MISSING = "Journal {jid} related to application {id} does not exist"
    BLL__UNREJECT_APPLICATION__SAVE_FAIL = "Save on {obj} {id} in unreject_application failed"

    ADMIN__WITHDRAW_REINSTATE = "<a href='{url}'>Job to withdraw/reinstate journal has been submitted</a>"

    CANNOT_CHANGE_THE_STATUS__OTHER_JOURNAL_IN_DOAJ_EXISTS = "The status couldn't be changed. For the following journals, other with matching ISSN(s) already exists in doaj: {ids}"

    AUTOMATICALLY_REJECTED_UPDATE_REQUEST_NOTE = "Update request was automatically rejected because the associated journal was withdrawn or deleted."
    AUTOMATICALLY_REJECTED_UPDATE_REQUEST_WITH_ID = "Update request {urid} automatically rejected"
    NO_UPDATE_REQUESTS = "No update requests found."

    BULK_JOURNAL_DELETE = "About to delete an estimated {journal_no} journals with {article_no} articles associated with their ISSNs. Existing update requests will be automatically rejected."
    BULK_JOURNAL_DELETE_COMPLETED = "Deleted {journal_no} journals and all articles associated with their ISSNs."

    NOTIFY__DEFAULT_SHORT_NOTIFICATION = "You have a new notification"
    NOTIFY__DEFAULT_ACTION_INTRO = "To take action based on this notification, follow this link: "

    DISCONTINUED_JOURNAL_FOUND_LOG = "Journal discontinuing soon found: {id}"
    DISCONTINUED_JOURNALS_FOUND_NOTIFICATION_SENT_LOG = "Notification with journals discontinuing soon sent."
    DISCONTINUED_JOURNALS_FOUND_NOTIFICATION_ERROR_LOG = "Error sending notification with journals discontinuing soon."
    NO_DISCONTINUED_JOURNALS_FOUND_LOG = "No journals discontinuing soon found"

    FORMS__APPLICATION_STATUS__PENDING = "Pending"
    FORMS__APPLICATION_STATUS__IN_PROGRESS = 'In Progress'
    FORMS__APPLICATION_STATUS__COMPLETED = 'Completed'
    FORMS__APPLICATION_STATUS__POST_SUBMISSION_REVIEW = 'Post Submission Automation'
    FORMS__APPLICATION_STATUS__UPDATE_REQUEST = 'Update Request'
    FORMS__APPLICATION_STATUS__REVISIONS_REQUIRED = 'Revisions Required'
    FORMS__APPLICATION_STATUS__ON_HOLD = 'On Hold'
    FORMS__APPLICATION_STATUS__READY = 'Ready'
    FORMS__APPLICATION_STATUS__REJECTED = 'Rejected'
    FORMS__APPLICATION_STATUS__ACCEPTED = 'Accepted'

    JOURNAL_CSV_VALIDATE__HEADER_CASE_MISMATCH = '"{h}" has a mismatching case to the expected header "{expected}".'
    JOURNAL_CSV_VALIDATE__INVALID_HEADER = '"{h}" is not a valid column header. Please revert it to match what was sent to you in the original file.'
    JOURNAL_CSV_VALIDATE__REQUIRED_HEADER_MISSING = '"{h}" is a required column missing from this upload. Please refer to the original file and restore the column.'
    JOURNAL_CSV_VALIDATE__MISSING_JOURNAL = "There is no journal record in DOAJ for ISSN(s) {issns}.  The record may not exist, or it may be withdrawn."
    JOURNAL_CSV_VALIDATE__OWNER_MISMATCH = "Your account '{acc}' doesn't own the journal with ISSN(s) {issns}. You may not update it."
    JOURNAL_CSV_VALIDATE__NO_DATA_CHANGE = "The data you supplied didn't change anything in the journal record."
    JOURNAL_CSV_VALIDATE__QUESTION_CANNOT_CHANGE = 'You may not change "{question}". Please revert it to match what was sent to you in the original file.'
    JOURNAL_CSV_VALIDATE__CANNOT_MAKE_UR = "We couldn't create an update for this journal because: {reason}"
    JOURNAL_CSV_VALIDATE__INVALID_DATA = "We couldn't understand the information in '{question}'"

    PRESERVATION_NO_FILE = "No file provided for upload"

    ARE_YOU_A_HUMAN = "Are you sure you're a human? If you're having trouble logging in, please <a href='/contact'>contact us</a>."

    AUTOASSIGN__OWNER_MAPPED = "owner '{owner}' is mapped to editor group '{target}'"
    AUTOASSIGN__COUNTRY_MAPPED = "country '{country}' ({country_code}) is mapped to editor group '{target}'"
    AUTOASSIGN__NOTE__EDITOR_GROUP_MISSING = "Autoassign: Editor group '{target}' does not exist, cannot auto assign"
    AUTOASSIGN__NOTE__ASSIGN = "Autoassign: Editor group auto assigned to '{target}' because {reason}"

    FORMS__APPLICATION_FLAG__RESOLVED = "This flag was resolved on {date} by {username};\n Original note: {note}"
    FORMS_APPLICATION_FLAG__PAST_DEADLINE_WARNING = "Provided deadline is in the past. Is it correct?"

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
