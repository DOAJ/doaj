from portality.clcsv import ClCsv
from portality import models, datasets, app_email
from portality.core import app
import os, re, string, uuid
from portality.formcontext.xwalk import SuggestionFormXWalk
from portality.formcontext import formcontext, choices
from copy import deepcopy
from werkzeug.datastructures import MultiDict
from collections import OrderedDict
from datetime import datetime

#################################################################
# Code for handling validation of incoming spreadsheets
#################################################################

class CsvValidationException(Exception):
    pass

class CsvIngestException(Exception):
    pass

class ContentValidationException(Exception):
    def __init__(self, message, errors=None, *args, **kwargs):
        super(ContentValidationException, self).__init__(message, *args, **kwargs)
        self.errors = errors

def open_csv(path):
    try:
        sheet = ClCsv(path)
    except:
        raise CsvValidationException("Unable to open CSV - may be corrupt or a different file format.")
    return sheet

def validate_csv_structure(sheet, account):
    tup = sheet.get_column(0)
    if tup is None:
        raise CsvValidationException("Could not retrieve any content from the CSV; spreadsheet is invalid")

    _, sheet_questions = tup
    sheet_questions = [q.strip() for q in sheet_questions]
    valid_questions = Suggestion2QuestionXwalk.question_list()
    if sheet_questions != valid_questions:
        raise CsvValidationException("The list of questions in the csv has been modified; spreadsheet is invalid")

    try:
        headers = sheet.headers()[1:] # everything except the first header (which is the question column)
    except:
        raise CsvValidationException("There were no journals specified in the spreadsheet; spreadsheet is invalid")

    dedupe = list(set(headers))
    if len(headers) != len(dedupe):
        raise CsvValidationException("There were one or more repeated ISSNs in the csv header row; spreadsheet is invalid")

    allowed = models.Journal.issns_by_owner(account.id)
    for issn in dedupe:
        if not issn in allowed:
            raise CsvValidationException("The ISSN " + str(issn) + " is not owned by this user account; spreadsheet is invalid")

def validate_csv_contents(sheet):
    failed = {}     # here is where we will log the issn to formcontext mapping for contexts which fail to validate
    succeeded = []  # here is where we will record all the successful formcontexts (they will not be mapped to issn, as this will not be important once successful)
    skip = []       # here is where we will record the ISSNs of all the columns that will not be imported

    for issn, questions in sheet.columns():
        # skip the question column
        if issn == "":
            continue

        # conver the questions into form data and then into a multidict, which is the form_data format required by
        # the formcontext
        try:
            forminfo = Suggestion2QuestionXwalk.question2form(questions)
        except SuggestionXwalkException:
            raise CsvValidationException("Too many or too few values under ISSN " + str(issn) + "; spreadsheet is invalid")

        # convert to a multidict
        form_data = MultiDict(forminfo)

        # lookup the suggestion upon which this application is based
        suggs = models.Suggestion.find_by_issn(issn)
        if suggs is None or len(suggs) == 0:
            raise CsvValidationException("Unable to locate a ReApplication with the issn " + issn + "; spreadsheet is invalid")
        if len(suggs) > 1:
            raise CsvValidationException("Unable to locate a unique ReApplication with the issn " + issn + "; please contact an administrator")
        s = suggs[0]

        # determine if the existing record's status allows us to import
        if s.application_status not in ["reapplication", "submitted"]:
            skip.append(issn)
            continue

        fc = formcontext.ApplicationFormFactory.get_form_context("csv", source=s, form_data=form_data)
        if not fc.validate():
            failed[issn] = fc
        else:
            succeeded.append(fc)

    if len(failed) > 0:
        raise ContentValidationException("One or more records in the CSV failed to validate", errors=failed)

    return succeeded, skip

def generate_spreadsheet_error(sheet, exception):
    def int2base(x, base):
        digs = string.uppercase
        if x == 0: return digs[0]
        digits = []
        while x:
            digits.append(digs[x % base])
            x /= base
        digits.reverse()
        return ''.join(digits)

    # first read all the errors out into a data structure that we can order
    # and extract all the relevant information for each line
    report = {}
    for issn, fc in exception.errors.iteritems():
        report[issn] = {}
        for field, messages in fc.errors.iteritems():
            q = Suggestion2QuestionXwalk.q(field)
            msg = "; ".join(messages)
            c = sheet.get_colnumber(issn)
            c = int2base(c, 26)     # should work, as csv columns are zero indexed
            r = Suggestion2QuestionXwalk.q2idx(field) + 2   # add 2 for the offset from the header + the 0 indexed array
            report[issn][r] = (issn, q, r, c, msg)

    """
    NOTE: this makes a long string suitable for writing as a text file
    # register where we will store the actual strings of the rows in the error report
    rows = []

    # iterate through issns in the order that they should appear in the spreadsheet
    issns = report.keys()
    issns.sort()
    for issn in issns:
        # iterate through the rows in the order that they appear in the spreadsheet
        qs = report.get(issn, {}).keys()
        qs.sort()
        for r in qs:
            _, q, _, c, msg = report.get(issn, {}).get(r, (None, None, None, None, None))
            rows.append(str(issn) + " | " + str(q) + " | cell " + str(c) + str(r) + " - " + str(msg))

    return "\n".join(rows)
    """

    import cStringIO
    from portality import clcsv
    stream = cStringIO.StringIO()
    writer = clcsv.UnicodeWriter(stream)
    writer.writerow(["ISSN", "Question", "Cell", "Error message"])
    writer.writerow([])

    issns = report.keys()
    issns.sort()
    for issn in issns:
        # iterate through the rows in the order that they appear in the spreadsheet
        qs = report.get(issn, {}).keys()
        qs.sort()
        for r in qs:
            _, q, _, c, msg = report.get(issn, {}).get(r, (None, None, None, None, None))
            writer.writerow([str(issn), str(q), str(c) + str(r), str(msg)])
        writer.writerow([])

    return stream.getvalue()


#################################################################
# Workflow functions for ingesting a spreadsheet
#################################################################

def ingest_csv(path, account, error_callback=None):
    sheet = open_csv(path)
    validate_csv_structure(sheet, account)
    try:
        fcs, skip = validate_csv_contents(sheet)

        # if an exception is not thrown, we are clear to begin the process of import
        for fc in fcs:
            fc.finalise()

        return {"reapplied" : len(fcs), "skipped" : len(skip)}

    except ContentValidationException as e:
        report = generate_spreadsheet_error(sheet, e)
        if error_callback is not None:
            error_callback(report)
        raise e

def ingest_from_upload(upload):
    upload_dir = app.config.get("REAPPLICATION_UPLOAD_DIR") # FIXME: check what this will actually be called
    path = os.path.join(upload_dir, upload.local_filename)
    account = models.Account.pull(upload.owner)
    if account is None:
        raise CsvIngestException("Unable to ingest CVS for non-existant account")

    try:
        report = ingest_csv(path, account, email_error_closure(upload, account))
        upload.processed(report.get("reapplied"), report.get("skipped"))
        upload.save()
    except CsvValidationException as e:
        # this is where the structure of the csv itself is broken
        upload.failed(e.message)
        upload.save()
        return
    except ContentValidationException as e:
        upload.failed(e.message)
        upload.save()
        return
    except:
        upload.failed("An error was raised during processing - please contact an administrator")
        upload.save()
        return

def email_error_closure(upload, account):

    def email_error(report):
        to = [account.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - problems with your bulk reapplication"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                now = datetime.now().strftime("%Y%m%d")
                att = app_email.make_attachment("reapplication_errors_" + now + ".csv", "text/plain", report) # NOTE: file extension is now csv
                when = datetime.strptime(upload.created_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y")
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/bulk_reapp_error.txt",
                                    files=[att],
                                    when=when,
                                    account=account
                )
        except Exception as e:
            magic = str(uuid.uuid1())
            app.logger.error(magic + "\n" + repr(e))
            raise e

    return email_error

#################################################################
# code for creating the reapplication
#################################################################

def make_csv(path, reapps):
    cols = {}
    for r in reapps:
        assert isinstance(r, models.Suggestion) # for pycharm type inspection
        bj = r.bibjson()
        issn = bj.get_one_identifier(idtype=bj.P_ISSN)
        if issn is None:
            issn = bj.get_one_identifier(idtype=bj.E_ISSN)
        if issn is None:
            continue

        kvs = Suggestion2QuestionXwalk.suggestion2question(r)
        cols[issn] = kvs

    issns = cols.keys()
    issns.sort()

    sheet = ClCsv(path)

    qs = None
    for i in issns:
        if qs is None:
            qs = [q for q, _ in cols[i]]
            sheet.set_column("", qs)
        vs = [v for _, v in cols[i]]
        sheet.set_column(i, vs)

    sheet.save()

#################################################################
# Crosswalk between spreadsheet columns and Suggestions
#################################################################

class SuggestionXwalkException(Exception):
    pass

class Suggestion2QuestionXwalk(object):

    QTUP = [
        ("title",                               "1) Journal Title *"),
        ("url",                                 "2) URL *"),
        ("alternative_title",                   "3) Alternative Title"),
        ("pissn",                               "4) Journal ISSN (print version) MAY NOT BE EDITED"),
        ("eissn",                               "5) Journal ISSN (online version) MAY NOT BE EDITED"),
        ("publisher",                           "6) Publisher *"),
        ("society_institution",                 "7) Society or Institution"),
        ("platform",                            "8) Platform, Host or Aggregator"),
        ("contact_name",                        "9) Name of contact for this journal MAY NOT BE EDITED"),
        ("contact_email",                       "10) Contact's email address MAY NOT BE EDITED"),
        ("confirm_contact_email",               "11) Confirm contact's email address MAY NOT BE EDITED"),
        ("country",                             "12) In which country is the publisher of the journal based? *"),
        ("processing_charges",                  "13) Does the journal have article processing charges (APCs)? *"),
        ("processing_charges_amount",           "14) Amount **"),
        ("processing_charges_currency",         "15) Currency **"),
        ("submission_charges",                  "16) Does the journal have article submission charges? *"),
        ("submission_charges_amount",           "17) Amount **"),
        ("submission_charges_currency",         "18) Currency **"),
        ("articles_last_year",                  "19) How many research and review articles did the journal publish in the last calendar year? *"),
        ("articles_last_year_url",              "20) Enter the URL where this information can be found *"),
        ("waiver_policy",                       "21) Does the journal have a waiver policy (for developing country authors etc)? *"),
        ("waiver_policy_url",                   "22) Enter the URL where this information can be found **"),
        ("digital_archiving_policy",            "23) What digital archiving policy or program(s) does the journal belong to? *"),
        ("digital_archiving_policy_library",    "23a) If a national library, which one?"),
        ("digital_archiving_policy_other",      "23b) If Other, enter it here"),
        ("digital_archiving_policy_url",        "24) Enter the URL where this information can be found *"),
        ("crawl_permission",                    "25) Does the journal allow anyone to crawl the full-text of the journal? *"),
        ("article_identifiers",                 "26) Which permanent article identifiers does the journal use? *"),
        ("metadata_provision",                  "27) Does the journal provide, or intend to provide, article level metadata to DOAJ? *"),
        ("download_statistics",                 "28) Does the journal provide download statistics? *"),
        ("download_statistics_url",             "29) Enter the URL where this information can be found"),
        ("first_fulltext_oa_year",              "30) What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles? *"),
        ("fulltext_format",                     "31) Please indicate which formats of full text are available *"),
        ("keywords",                            "32) Add up to 6 keyword(s) that best describe the journal (comma delimited) *"),
        ("languages",                           "33) Select the language(s) that the Full Text of the articles is published in *"),
        ("editorial_board_url",                 "34) What is the URL for the Editorial Board page? *"),
        ("review_process",                      "35) Please select the review process for papers *"),
        ("review_process_url",                  "36) Enter the URL where this information can be found *"),
        ("aims_scope_url",                      "37) What is the URL for the journal's Aims & Scope *"),
        ("instructions_authors_url",            "38) What is the URL for the journal's instructions for authors? *"),
        ("plagiarism_screening",                "39) Does the journal have a policy of screening for plagiarism? *"),
        ("plagiarism_screening_url",            "40) Enter the URL where this information can be found **"),
        ("publication_time",                    "41) What is the average number of weeks between submission and publication? *"),
        ("oa_statement_url",                    "42) What is the URL for the journal's Open Access statement? *"),
        ("license_embedded",                    "43) Does the journal embed or display simple machine-readable CC licensing information in its articles? *"),
        ("license_embedded_url",                "44) Please provide a URL to an example page with embedded licensing information **"),
        ("license",                             "45) Enter which type of CC license the journal uses. If it is not a CC license, enter the license's name. Or enter None. *"),
        ("license_checkbox",                    "46) If the journal has a license which is not a CC license, which of the following does the content require?"),
        ("license_url",                         "47) Enter the URL on your site where your license terms are stated"),
        ("open_access",                         "48) Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles? *"),
        ("deposit_policy",                      "49) With which deposit policy directory does the journal have a registered deposit policy? *"),
        ("copyright",                           "50) Does the journal allow the author(s) to hold the copyright without restrictions? *"),
        ("copyright_url",                       "51) Enter the URL where this information can be found *"),
        ("publishing_rights",                   "52) Will the journal allow the author(s) to retain publishing rights without restrictions? *"),
        ("publishing_rights_url",               "53) Enter the URL where this information can be found *")
    ]

    DEGEN = {
        "article_identifiers_other" : "article_identifiers",
        "fulltext_format_other" : "fulltext_format",
        "license_other" : "license",
        "deposit_policy_other" : "deposit_policy",
        "copyright_other" : "copyright",
        "publishing_rights_other" : "publishing_rights"
    }

    @classmethod
    def q(cls, ident):
        if type(ident) == int:
            offset = 0
            if ident > 23:  # FIXME: explicit knowledge of question structure.  If structure changes, this needs to be fixed
                offset = 2
            return cls.QTUP[ident - 1 + offset][1]
        else:
            if ident in cls.DEGEN:
                ident = cls.DEGEN[ident]
            for k, q in cls.QTUP:
                if k == ident:
                    return q
        return None

    @classmethod
    def q2idx(cls, ident):
        offset = 0
        if type(ident) != int:
            idx = 1             # FIXME: this will break if the ident is not in the question list
            for k, q in cls.QTUP:
                if k == ident:
                    break
                idx += 1
            if idx > 23 and idx < 26:
                offset = idx - 23
                idx = 23        # FIXME: explicit knowledge of question structure.  If structure changes, this needs to be fixed
            ident = idx

        if ident > 23:
            offset = 2  # FIXME: explicit knowledge of question structure.  If structure changes, this needs to be fixed
        return ident + offset - 1

    @classmethod
    def a(cls, answers, ident):
        row = cls.q2idx(ident)
        return answers[row]

    @classmethod
    def question_list(cls):
        return [q for _, q in cls.QTUP]

    @classmethod
    def remove_disabled(cls, forminfo):
        """
        The role of this method is to remove any fields from the forminfo object that
        are not strictly allowed by the spreadsheet.  This function could sit in a variety
        of places, but we put it here to keep it next to the xwalk which knows about the
        structure of the forminfo dictionary
        :return: nothing - does operation on forminfo by reference
        """
        if "pissn" in forminfo:
            del forminfo["pissn"]
        if "eissn" in forminfo:
            del forminfo["eissn"]
        if "contact_name" in forminfo:
            del forminfo["contact_name"]
        if "contact_email" in forminfo:
            del forminfo["contact_email"]
        if "confirm_contact_email" in forminfo:
            del forminfo["confirm_contact_email"]

    @classmethod
    def suggestion2question(cls, suggestion):

        def other_list(main_field, other_field, other_value):
            aids = forminfo.get(main_field, [])
            if aids is None or aids == "" or aids == "None":
                aids = []
            aidother = forminfo.get(other_field)

            if other_value in aids:
                aids.remove(other_value)
            if aidother is not None and aidother != "" and aidother != "None":
                aids.append(aidother)
            return ", ".join(aids)

        def yes_no(val):
            return "Yes" if val else "No"

        def license_checkbox(val):
            opts = {}
            [opts.update({k : v}) for k,v  in choices.Choices.licence_checkbox()]
            nv = [opts.get(v) for v in val]
            return ", ".join(nv)

        # start by converting the object to the forminfo version
        # which is used by the application form in the first plage
        forminfo = SuggestionFormXWalk.obj2form(suggestion)

        kvs = []

        # create key/value pairs for the questions in order
        kvs.append((cls.q(1), forminfo.get("title")))
        kvs.append((cls.q(2), forminfo.get("url")))
        kvs.append((cls.q(3), forminfo.get("alternative_title")))
        kvs.append((cls.q(4), forminfo.get("pissn")))
        kvs.append((cls.q(5), forminfo.get("eissn")))
        kvs.append((cls.q(6), forminfo.get("publisher")))
        kvs.append((cls.q(7), forminfo.get("society_institution")))
        kvs.append((cls.q(8), forminfo.get("platform")))
        kvs.append((cls.q(9), forminfo.get("contact_name")))
        kvs.append((cls.q(10), forminfo.get("contact_email")))
        kvs.append((cls.q(11), forminfo.get("confirm_contact_email")))
        kvs.append((cls.q(12), forminfo.get("country")))
        kvs.append((cls.q(13), yes_no(forminfo.get("processing_charges"))))
        kvs.append((cls.q(14), forminfo.get("processing_charges_amount")))
        kvs.append((cls.q(15), forminfo.get("processing_charges_currency")))
        kvs.append((cls.q(16), yes_no(forminfo.get("submission_charges"))))
        kvs.append((cls.q(17), forminfo.get("submission_charges_amount")))
        kvs.append((cls.q(18), forminfo.get("submission_charges_currency")))
        kvs.append((cls.q(19), forminfo.get("articles_last_year")))
        kvs.append((cls.q(20), forminfo.get("articles_last_year_url")))
        kvs.append((cls.q(21), yes_no(forminfo.get("waiver_policy"))))
        kvs.append((cls.q(22), forminfo.get("waiver_policy_url")))

        dap = deepcopy(forminfo.get("digital_archiving_policy", []))
        lib = choices.Choices.digital_archiving_policy_val("library")
        oth = choices.Choices.digital_archiving_policy_val("other")
        if lib in dap: dap.remove(lib)
        if oth in dap: dap.remove(oth)
        kvs.append((cls.q(23), ", ".join(dap)))
        kvs.append((cls.q("digital_archiving_policy_library"), forminfo.get("digital_archiving_policy_library")))
        kvs.append((cls.q("digital_archiving_policy_other"), forminfo.get("digital_archiving_policy_other")))

        kvs.append((cls.q(24), forminfo.get("digital_archiving_policy_url")))
        kvs.append((cls.q(25), yes_no(forminfo.get("crawl_permission"))))

        article_identifiers = other_list("article_identifiers", "article_identifiers_other", choices.Choices.article_identifiers_val("other"))
        kvs.append((cls.q(26), article_identifiers))

        kvs.append((cls.q(27), yes_no(forminfo.get("metadata_provision"))))
        kvs.append((cls.q(28), yes_no(forminfo.get("download_statistics"))))
        kvs.append((cls.q(29), forminfo.get("download_statistics_url")))
        kvs.append((cls.q(30), forminfo.get("first_fulltext_oa_year")))

        fulltext_formats = other_list("fulltext_format", "fulltext_format_other", choices.Choices.fulltext_format_val("other"))
        kvs.append((cls.q(31), fulltext_formats))

        kvs.append((cls.q(32), ", ".join(forminfo.get("keywords", []))))
        kvs.append((cls.q(33), ", ".join(forminfo.get("languages", []))))
        kvs.append((cls.q(34), forminfo.get("editorial_board_url")))
        kvs.append((cls.q(35), forminfo.get("review_process")))
        kvs.append((cls.q(36), forminfo.get("review_process_url")))
        kvs.append((cls.q(37), forminfo.get("aims_scope_url")))
        kvs.append((cls.q(38), forminfo.get("instructions_authors_url")))
        kvs.append((cls.q(39), yes_no(forminfo.get("plagiarism_screening"))))
        kvs.append((cls.q(40), forminfo.get("plagiarism_screening_url")))
        kvs.append((cls.q(41), forminfo.get("publication_time")))
        kvs.append((cls.q(42), forminfo.get("oa_statement_url")))
        kvs.append((cls.q(43), yes_no(forminfo.get("license_embedded"))))
        kvs.append((cls.q(44), forminfo.get("license_embedded_url")))

        lic = forminfo.get("license")
        if lic == choices.Choices.licence_val("other"):
            lic = forminfo.get("license_other")
        kvs.append((cls.q(45), lic))

        kvs.append((cls.q(46), license_checkbox(forminfo.get("license_checkbox", []))))
        kvs.append((cls.q(47), forminfo.get("license_url")))
        kvs.append((cls.q(48), yes_no(forminfo.get("open_access"))))

        deposit_policies = other_list("deposit_policy", "deposit_policy_other", choices.Choices.deposit_policy_other_val("other"))
        kvs.append((cls.q(49), deposit_policies))

        cr = forminfo.get("copyright")
        if cr == choices.Choices.copyright_other_val("other"):
            cr = forminfo.get("copyright_other")
        kvs.append((cls.q(50), cr))

        kvs.append((cls.q(51), forminfo.get("copyright_url")))

        pr = forminfo.get("publishing_rights")
        if pr == choices.Choices.publishing_rights_other_val("other"):
            pr = forminfo.get("publishing_rights_other")
        kvs.append((cls.q(52), pr))

        kvs.append((cls.q(53), forminfo.get("publishing_rights_url")))

        return kvs

    @classmethod
    def question2form(cls, qs, force=False):
        expected = len(cls.question_list())
        if len(qs) < expected:
            raise SuggestionXwalkException("Crosswalk cannot complete - source column does not have enough rows")
        elif len(qs) > expected and not force:
            raise SuggestionXwalkException("Crosswalk cannot complete - source column has more data than there are questions.  To xwalk anyway, use the 'force' argument")

        def normal(val):
            if val is None:
                return None
            if type(val) == int:
                return val
            val = val.strip()
            val = re.sub(r'\s+', ' ', val)
            return val

        def yes_no(val):
            val = normal(val)
            if val is None: return None
            if val.lower() == "yes":
                return "True"
            elif val.lower() == "no":
                return "False"
            return val

        def country(val):
            val = normal(val)
            if val is None: return None

            cs = [(code, data.get("name").upper()) for code, data in datasets.countries_dict.items()]
            codes = [c for c, _ in cs]
            ns = {}
            [ns.update({n : c}) for c, n in cs]

            uv = val.upper()
            if uv in codes:
                return uv
            if uv in ns.keys():
                return ns[uv]

            return val

        def currency(val):
            val = normal(val)
            if val is None: return None

            cs = [(data.get("currency_alphabetic_code"), data.get("currency_name").upper()) for _, data in datasets.countries_dict.items()]
            codes = [c for c, _ in cs]
            ns = {}
            [ns.update({n : c}) for c, n in cs]

            uv = val.upper()
            if uv in codes:
                return uv
            if uv in ns.keys():
                return ns[uv]

            return val

        def languages(val):
            val = normal(val)
            if val is None: return None

            opts = [x.strip() for x in val.split(",")]

            codes = [c for c, _ in datasets.language_options]
            ns = {}
            [ns.update({n.upper() : c}) for c, n in datasets.language_options]

            norm = []
            for o in opts:
                uv = o.upper()
                if uv in codes:
                    norm.append(uv)
                elif uv in ns.keys():
                    norm.append(ns[uv])
                else:
                    norm.append(o)

            return list(OrderedDict.fromkeys(norm)) # deduplicate while preserving order

        def _rationalise_other(val, form_choices, other_val):
            val = normal(val)
            if val is None or val == "":
                return None

            opts = [aid.strip() for aid in val.split(",")]

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in form_choices]

            normopts = []
            otheropts = []
            for o in opts:
                ol = o.lower()
                if ol in cs and ol != other_val.lower():
                    normopts.append(cs[ol])
                elif ol != other_val.lower():
                    otheropts.append(o)

            if len(otheropts) > 0:
                normopts.append(other_val)

            return list(OrderedDict.fromkeys(normopts)), ", ".join(list(OrderedDict.fromkeys(otheropts)))

        def digital_archiving_policy(options, library, other):
            options = normal(options)
            library = normal(library)
            other = normal(other)

            opts = []
            if options is not None and options != "":
                opts = [dap.strip() for dap in options.split(",")]

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in choices.Choices.digital_archiving_policy()]

            lib = choices.Choices.digital_archiving_policy_val("library")
            oth = choices.Choices.digital_archiving_policy_val("other")
            extras = [lib.lower(), oth.lower()]

            normopts = []
            otheropts = []
            for o in opts:
                ol = o.lower()
                if ol in cs and not ol in extras:
                    if cs[ol] not in normopts:
                        normopts.append(cs[ol])
                elif not ol in extras:
                    if o not in otheropts:
                        otheropts.append(o)

            if other is not None and other != "":
                otheropts.append(other)

            # add "A national library" and "Other" (in that order) if necessary
            if library is not None and library != "":
                if lib not in normopts:
                    normopts.append(lib)
            if len(otheropts) > 0:
                if oth not in normopts:
                    normopts.append(oth)

            return normopts, library, ", ".join(otheropts)

        def article_identifiers(val):
            return _rationalise_other(val, choices.Choices.article_identifiers(), choices.Choices.article_identifiers_val("other"))

        def fulltext_format(val):
            return _rationalise_other(val, choices.Choices.fulltext_format(), choices.Choices.fulltext_format_val("other"))

        def deposit_policy(val):
            return _rationalise_other(val, choices.Choices.deposit_policy(), choices.Choices.deposit_policy_other_val("other"))

        def get_license(val):
            return _this_or_other(val, choices.Choices.licence(), choices.Choices.licence_val("other"))

        def copyright(val):
            return _this_or_other(val, choices.Choices.copyright(), choices.Choices.copyright_other_val("other"))

        def publishing_rights(val):
            return _this_or_other(val, choices.Choices.publishing_rights(), choices.Choices.publishing_rights_other_val("other"))

        def _this_or_other(val, form_options, other_val):
            val = normal(val)
            if val is None:
                return None

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in form_options]

            if val.lower() in cs:
                return cs[val.lower()], ""
            else:
                return other_val, val

        def review_process(val):
            val = normal(val)
            if val is None:
                return None

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in choices.Choices.review_process()]
            norm = cs[val.lower()] if val.lower() in cs else val

            return norm

        def license_aspects(val):
            val = normal(val)
            if val is None or val == "":
                return None

            opts = [x.strip() for x in val.split(",")]

            cs = {}
            ns = {}
            [(cs.update({c.upper() : c}), ns.update({n.upper() : c})) for c, n in choices.Choices.licence_checkbox()]

            normopts = []
            for o in opts:
                uv = o.upper()
                if uv in cs:
                    normopts.append(uv)
                elif uv in ns.keys():
                    normopts.append(ns[uv])
                else:
                    normopts.append(o)

            return list(OrderedDict.fromkeys(normopts))

        forminfo = {}

        forminfo["title"] = normal(cls.a(qs, 1))
        forminfo["url"] = normal(cls.a(qs, 2))
        forminfo["alternative_title"] = normal(cls.a(qs, 3))
        forminfo["pissn"] = normal(cls.a(qs, 4))
        forminfo["eissn"] = normal(cls.a(qs, 5))
        forminfo["publisher"] = normal(cls.a(qs, 6))
        forminfo["society_institution"] = normal(cls.a(qs, 7))
        forminfo["platform"] = normal(cls.a(qs, 8))
        forminfo["contact_name"] = normal(cls.a(qs, 9))
        forminfo["contact_email"] = normal(cls.a(qs, 10))
        forminfo["confirm_contact_email"] = normal(cls.a(qs, 11))
        forminfo["country"] = country(cls.a(qs, 12))
        forminfo["processing_charges"] = yes_no(cls.a(qs, 13))
        forminfo["processing_charges_amount"] = normal(cls.a(qs, 14))
        forminfo["processing_charges_currency"] = currency(cls.a(qs, 15))
        forminfo["submission_charges"] = yes_no(cls.a(qs, 16))
        forminfo["submission_charges_amount"] = normal(cls.a(qs, 17))
        forminfo["submission_charges_currency"] = currency(cls.a(qs, 18))
        forminfo["articles_last_year"] = normal(cls.a(qs, 19))
        forminfo["articles_last_year_url"] = normal(cls.a(qs, 20))
        forminfo["waiver_policy"] = yes_no(cls.a(qs, 21))
        forminfo["waiver_policy_url"] = normal(cls.a(qs, 22))

        dap, lib, oth = digital_archiving_policy(cls.a(qs, 23), cls.a(qs, "digital_archiving_policy_library"), cls.a(qs, "digital_archiving_policy_other"))
        if dap is not None and len(dap) > 0:
            forminfo["digital_archiving_policy"] = dap
            if lib is not None and lib != "":
                forminfo["digital_archiving_policy_library"] = lib
            if oth is not None and oth != "":
                forminfo["digital_archiving_policy_other"] = oth

        forminfo["digital_archiving_policy_url"] = normal(cls.a(qs, 24))
        forminfo["crawl_permission"] = yes_no(cls.a(qs, 25))

        aids, aidother = article_identifiers(cls.a(qs, 26))
        if aids is not None and len(aids) > 0:
            forminfo["article_identifiers"] = aids
            forminfo["article_identifiers_other"] = aidother

        forminfo["metadata_provision"] = yes_no(cls.a(qs, 27))
        forminfo["download_statistics"] = yes_no(cls.a(qs, 28))
        forminfo["download_statistics_url"] = normal(cls.a(qs, 29))
        forminfo["first_fulltext_oa_year"] = normal(cls.a(qs, 30))

        ftf, ftfother = fulltext_format(cls.a(qs, 31))
        if ftf is not None and len(ftf) > 0:
            forminfo["fulltext_format"] = ftf
            forminfo["fulltext_format_other"] = ftfother

        forminfo["keywords"] = [k.strip() for k in normal(cls.a(qs, 32)).split(",")]
        forminfo["languages"] = languages(cls.a(qs, 33))
        forminfo["editorial_board_url"] = normal(cls.a(qs, 34))
        forminfo["review_process"] = review_process(cls.a(qs, 35))
        forminfo["review_process_url"] = normal(cls.a(qs, 36))
        forminfo["aims_scope_url"] = normal(cls.a(qs, 37))
        forminfo["instructions_authors_url"] = normal(cls.a(qs, 38))
        forminfo["plagiarism_screening"] = yes_no(cls.a(qs, 39))
        forminfo["plagiarism_screening_url"] = normal(cls.a(qs, 40))
        forminfo["publication_time"] = normal(cls.a(qs, 41))
        forminfo["oa_statement_url"] = normal(cls.a(qs, 42))
        forminfo["license_embedded"] = yes_no(cls.a(qs, 43))
        forminfo["license_embedded_url"] = normal(cls.a(qs, 44))

        lic, licother = get_license(cls.a(qs, 45))
        forminfo["license"] = lic
        forminfo["license_other"] = licother

        la = license_aspects(cls.a(qs, 46))
        if la is not None and len(la) > 0:
            forminfo["license_checkbox"] = license_aspects(cls.a(qs, 46))

        forminfo["license_url"] = normal(cls.a(qs, 47))
        forminfo["open_access"] = yes_no(cls.a(qs, 48))

        dp, dpother = deposit_policy(cls.a(qs, 49))
        if dp is not None and len(dp) > 0:
            forminfo["deposit_policy"] = dp
            forminfo["deposit_policy_other"] = dpother

        cr, crother = copyright(cls.a(qs, 50))
        forminfo["copyright"] = cr
        forminfo["copyright_other"] = crother

        forminfo["copyright_url"] = normal(cls.a(qs, 51))

        pr, prother = publishing_rights(cls.a(qs, 52))
        forminfo["publishing_rights"] = pr
        forminfo["publishing_rights_other"] = prother

        forminfo["publishing_rights_url"] = normal(cls.a(qs, 53))

        return forminfo
