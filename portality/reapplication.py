from portality.clcsv import ClCsv
from portality import models
from portality.core import app
import os

class CsvValidationException(Exception):
    pass

class CsvIngestException(Exception):
    pass

class ContentValidationException(Exception):
    def __init__(self, message, errors=None, *args, **kwargs):
        super(ContentValidationException, self).__init__(message, *args, **kwargs)
        self.errors = errors

# FIXME: this needs to contain the actual list of questions in the spreadsheet, which should
# actually come from somewhere standard (like the re-application to spreadsheet crosswalk)
QUESTIONS = [
    'Q1',
    'Q2',
    'Q3',
    'Q4',
    'Q5',
    'Q6',
    'Q7',
    'Q8',
    'Q9',
    'Q10',
    'Q11',
    'Q12',
    'Q13',
    'Q14',
    'Q15',
    'Q16',
    'Q17',
    'Q18',
    'Q19',
    'Q20',
    'Q21',
    'Q22',
    'Q23',
    'Q24',
    'Q25',
    'Q26',
    'Q27',
    'Q28',
    'Q29',
    'Q30',
    'Q31',
    'Q32',
    'Q33',
    'Q34',
    'Q35',
    'Q36',
    'Q37',
    'Q38',
    'Q39',
    'Q40',
    'Q41',
    'Q42',
    'Q43',
    'Q44',
    'Q45',
    'Q46',
    'Q47',
    'Q48',
    'Q49',
    'Q50',
    'Q51',
    'Q52',
    'Q53',
    'Q54',
    'Q55',
    'Q56'
]

def open_csv(path):
    try:
        sheet = ClCsv(path)
    except:
        raise CsvValidationException("Unable to open CSV - may be corrupt or a different file format.")
    return sheet

def validate_csv_structure(sheet, account):
    sheet_questions = sheet.get_column(0)
    if sheet_questions is None:
        raise CsvValidationException("CSV does not contain any questions in the first column")

    sheet_questions = [q.strip() for q in sheet_questions]
    if sheet_questions != QUESTIONS:
        raise CsvValidationException("The list of questions in the csv has been modified; spreadsheet is invalid")

    headers = sheet.headers()
    dedupe = list(set(headers))
    if len(headers) != dedupe:
        raise CsvValidationException("There were one or more repeated ISSNs in the csv header row; spreadsheet is invalid")

    allowed = models.Journal.issns_by_owner(account.id)
    for issn in dedupe:
        if not issn in allowed:
            raise CsvValidationException("The ISSN " + str(issn) + " is not owned by this user account; spreadsheet is invalid")


def validate_csv_contents(sheet, account):
    failed = []
    for issn, questions in sheet.columns():
        # depends on merge with the form context.  Approximately:
        # fc = formcontext.ApplicationFormFactory.get_form_context("csv", source=questions)
        # if not fc.validate():
        #   failed.append(fc.errors)
        pass
    if len(failed) > 0:
        raise ContentValidationException("One or more records in the CSV failed to validate", errors=failed)

def generate_spreadsheet_error(sheet, exception):
    pass

def ingest_csv(path, account):
    sheet = open_csv(path)
    validate_csv_structure(sheet, account)
    try:
        fcs = validate_csv_contents(sheet, account)
    except ContentValidationException as e:
        generate_spreadsheet_error(sheet, e)
        raise e

def ingest_from_upload(upload):
    upload_dir = app.config.get("REAPPLICATION_UPLOAD_DIR")
    path = os.path.join(upload_dir, upload.local_filename)
    account = models.Account.pull(upload.owner)
    if account is None:
        raise CsvIngestException("Unable to ingest CVS for non-existant account")

    try:
        ingest_csv(path, account)
    except CsvValidationException as e:
        # this is where the structure of the csv itself is broken
        upload.failed(e.message)
        upload.save()
        return
    except ContentValidationException as e:
        upload.failed(e.message)
        upload.save()
        return


