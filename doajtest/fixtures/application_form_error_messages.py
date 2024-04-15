from datetime import datetime

current_year = datetime.now().year

class FixtureMessages(object):
    ERROR_YES_REQUIRED = "You must answer Yes to continue"
    ERROR_OA_STATEMENT = "DOAJ only indexes open access journals which comply with the statement above. Please check and update the open access statement of your journal. You may return to this application at any time."
    ERROR_OA_STATEMENT_URL = "Enter the URL for the journal’s Open Access statement page"
    ERROR_OA_START_REQUIRED = "Enter the Year (YYYY)."
    ERROR_OA_START_INVALID_VALUE = f'This value should be between 1900 and {current_year}'
    ERROR_INVALID_URL = "This value should be a valid url."
    ERROR_YES_OR_NO_REQUREID = "Select Yes or No"
    ERROR_JOURNAL_URL_REQUIRED = "Enter the URL for the journal’s homepage"
    ERROR_JOURNAL_URL_INVALID = "This value should be a valid url."