from portality.clcsv import ClCsv
from portality import models, datasets
from portality.core import app
import os, re
from portality.formcontext.xwalk import SuggestionFormXWalk
from portality.formcontext import formcontext, choices
from copy import deepcopy
from werkzeug.datastructures import MultiDict

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

        # remove the "disabled" fields from the form info
        Suggestion2QuestionXwalk.remove_disabled(forminfo)

        # convert to a multidict
        form_data = MultiDict(forminfo)

        # lookup the suggestion upon which this application is based
        suggs = models.Suggestion.find_by_issn(issn)
        if suggs is None or len(suggs) == 0:
            raise CsvValidationException("Unable to locate a ReApplication with the issn " + issn + "; spreadsheet is invalid")
        if len(suggs) > 1:
            raise CsvValidationException("Unable to locate a unique ReApplication with the issn " + issn + "; please contact an administrator")
        s = suggs[0]

        fc = formcontext.ApplicationFormFactory.get_form_context("csv", source=s, form_data=form_data)
        if not fc.validate():
            failed[issn] = fc
        else:
            succeeded.append(fc)
    if len(failed) > 0:
        raise ContentValidationException("One or more records in the CSV failed to validate", errors=failed)
    return succeeded

def generate_spreadsheet_error(sheet, exception):
    pass

#################################################################
# Workflow functions for ingesting a spreadsheet
#################################################################

def ingest_csv(path, account):
    sheet = open_csv(path)
    validate_csv_structure(sheet, account)
    try:
        fcs = validate_csv_contents(sheet)

        # if an exception is not thrown, we are clear to begin the process of import
        for fc in fcs:
            fc.finalise()
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
    # The questions (in order) that we are xwalking to
    QUESTIONS = [
        "1) Journal Title",
        "2) URL",
        "3) Alternative Title",
        "4) Journal ISSN (print version)",
        "5) Journal ISSN (online version)",
        "6) Publisher",
        "7) Society or Institution",
        "8) Platform, Host or Aggregator",
        "9) Name of contact for this journal",
        "10) Contact's email address",
        "11) Confirm contact's email address",
        "12) In which country is the publisher of the journal based?",
        "13) Does the journal have article processing charges (APCs)?",
        "14) Amount",
        "15) Currency",
        "16) Does the journal have article submission charges?",
        "17) Amount",
        "18) Currency",
        "19) How many research and review articles did the journal publish in the last calendar year?",
        "20) Enter the URL where this information can be found",
        "21) Does the journal have a waiver policy (for developing country authors etc)?",
        "22) Enter the URL where this information can be found",
        "23) What digital archiving policy does the journal use?",
        "24) Enter the URL where this information can be found",
        "25) Does the journal allow anyone to crawl the full-text of the journal?",
        "26) Which article identifiers does the journal use?",
        "27) Does the journal provide, or intend to provide, article level metadata to DOAJ?",
        "28) Does the journal provide download statistics?",
        "29) Enter the URL where this information can be found",
        "30) What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles? (Full Text may be provided as PDFs. Does not apply for new journals.)",
        "31) Please indicate which formats of full text are available",
        "32) Add keyword(s) that best describe the journal (comma delimited)",
        "33) Select the language(s) that the Full Text of the articles is published in",
        "34) What is the URL for the Editorial Board page?",
        "35) Please select the review process for papers",
        "36) Enter the URL where this information can be found",
        "37) What is the URL for the journal's Aims & Scope",
        "38) What is the URL for the journal's instructions for authors?",
        "39) Does the journal have a policy of screening for plagiarism?",
        "40) Enter the URL where this information can be found",
        "41) What is the average number of weeks between submission and publication?",
        "42) What is the URL for the journal's Open Access statement?",
        "43) Does the journal embed or display simple machine-readable CC licensing information in its articles?",
        "44) Please provide a URL to an example page with embedded licensing information",
        "45) Does the journal allow reuse and remixing of its content, in accordance with a CC license?",
        "46) Which of the following does the content require? (Tick all that apply.)",
        "47) Enter the URL on your site where your license terms are stated",
        "48) Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles?",
        "49) With which deposit policy directory does the journal have a registered deposit policy?",
        "50) Does the journal allow the author(s) to hold the copyright without restrictions?",
        "51) Enter the URL where this information can be found",
        "52) Will the journal allow the author(s) to retain publishing rights without restrictions?",
        "53) Enter the URL where this information can be found"
    ]

    SUPPLEMENTARY_QUESTIONS = {
        23 : {
            "library" : "If a national library, which one?",
            "other" : "If Other, enter it here"
        },
        #26 : {
        #    "other" : "If Other, enter it here"
        #},
        #31 : {
        #    "other" : "If Other, enter it here"
        #},
        #45 : {
        #    "other" : "If Other, enter it here"
        #},
        #49 : {
        #    "other" : "If Other, enter it here"
        #},
        #50 : {
        #    "other" : "If Other, enter it here"
        #},
        #52 : {
        #    "other" : "If Other, enter it here"
        #}
    }

    @classmethod
    def q(cls, num, supp=None):
        if supp is None:
            return cls.QUESTIONS[num - 1]
        else:
            return cls.SUPPLEMENTARY_QUESTIONS[num][supp]

    @classmethod
    def a(cls, answers, num, supp=None):
        # first we need to calculate the number of supplementary questions lower than num
        have_supps = cls.SUPPLEMENTARY_QUESTIONS.keys()                                         # start with the questions with supplementary questions
        lower = [len(cls.SUPPLEMENTARY_QUESTIONS[x].keys()) for x in have_supps if x < num]     # filter those that are lower than num, and then count the keys in each dict
        offset = sum(lower)                                                                     # sum the count of all the keys

        # calculate the offset in the event that we're asked for a supplementary question
        supp_offset = 0
        if supp is not None:
            sqs = cls.SUPPLEMENTARY_QUESTIONS[num].keys()        # list the supplementary options
            if len(sqs) == 1:                                    # if there's only one key, we just increment by 1
                supp_offset = 1
            elif len(sqs) == 2:                                  # if there are two keys, we deal with the special case
                if supp == "other":
                    supp_offset = 2
                elif supp == "library":
                    supp_offset = 1


        # the index of an answer in the array is the question - 1 (because array is indexed from 0) + the number of supplementary
        # questions lower than num + any offset for a supplementary question on this number
        idx = (num - 1) + offset + supp_offset

        if idx > len(answers):
            raise SuggestionXwalkException("Crosswalk cannot complete - source column does not have enough rows")

        return answers[idx]

    @classmethod
    def question_list(cls):
        # start with the base list of questions
        ql = deepcopy(cls.QUESTIONS)

        # now get the supplementary question keys in reverse order
        sups = cls.SUPPLEMENTARY_QUESTIONS.keys()
        sups.sort(reverse=True)

        # for each of the questions which has supplementary information
        # insert the additional questions
        for q in sups:
            additional = cls.SUPPLEMENTARY_QUESTIONS[q].keys()
            if len(additional) == 1:
                toinsert = cls.SUPPLEMENTARY_QUESTIONS[q][additional[0]]
                ql.insert(q, toinsert)
            elif len(additional) == 2:
                # other second (so we insert it first!)
                toinsert = cls.SUPPLEMENTARY_QUESTIONS[q]["other"]
                ql.insert(q, toinsert)

                # library first (so we insert it last!)
                toinsert = cls.SUPPLEMENTARY_QUESTIONS[q]["library"]
                ql.insert(q, toinsert)

        return ql

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

        # start by converting the object to the forminfo version
        # which is used by the application form in the first plage
        forminfo = SuggestionFormXWalk.obj2form(suggestion)

        kvs = []

        # do the conversion for some which have to have human readable values
        waiver_policy = "Yes" if forminfo.get("waiver_policy") else "No"
        submission_charges = "Yes" if forminfo.get("submission_charges") else "No"
        processing_charges = "Yes" if forminfo.get("processing_charges") else "No"
        crawl_permission = "Yes" if forminfo.get("crawl_permission") is not None else "No"
        article_identifiers = ", ".join(forminfo.get("article_identifiers", [])) if ", ".join(forminfo.get("article_identifiers", [])) not in [None, "None"] else ""
        metadata_provision = "Yes" if forminfo.get("metadata_provision") is not None else "No"
        download_statistics = "Yes" if forminfo.get("download_statistics") is not None else "No"
        plagiarism_screening = "Yes" if forminfo.get("plagiarism_screening") is not None else "No"
        license_embedded = "Yes" if forminfo.get("license_embedded") is not None else "No"
        open_access = "Yes" if forminfo.get("open_access") is not None else "No"
        deposit_policy = ", ".join(forminfo.get("deposit_policy", [])) if ", ".join(forminfo.get("deposit_policy", [])) not in [None, "None"] else ""
        copyright_other = forminfo.get("copyright_other") if forminfo.get("copyright_other") not in [None, "None"] else ""
        publishing_rights_other = forminfo.get("publishing_rights_other") if forminfo.get("publishing_rights_other") not in [None, "None"] else ""


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
        kvs.append((cls.q(13), processing_charges))
        kvs.append((cls.q(14), forminfo.get("processing_charges_amount")))
        kvs.append((cls.q(15), forminfo.get("processing_charges_currency")))
        kvs.append((cls.q(16), submission_charges))
        kvs.append((cls.q(17), forminfo.get("submission_charges_amount")))
        kvs.append((cls.q(18), forminfo.get("submission_charges_currency")))
        kvs.append((cls.q(19), forminfo.get("articles_last_year")))
        kvs.append((cls.q(20), forminfo.get("articles_last_year_url")))
        kvs.append((cls.q(21), waiver_policy))
        kvs.append((cls.q(22), forminfo.get("waiver_policy_url")))

        dap = deepcopy(forminfo.get("digital_archiving_policy", []))
        lib = choices.Choices.digital_archiving_policy_val("library")
        oth = choices.Choices.digital_archiving_policy_val("other")
        if lib in dap: dap.remove(lib)
        if oth in dap: dap.remove(oth)
        kvs.append((cls.q(23), ", ".join(dap)))
        kvs.append((cls.q(23, "library"), forminfo.get("digital_archiving_policy_library")))
        kvs.append((cls.q(23, "other"), forminfo.get("digital_archiving_policy_other")))

        kvs.append((cls.q(24), forminfo.get("digital_archiving_policy_url")))
        kvs.append((cls.q(25), crawl_permission))

        article_identifiers = other_list("article_identifiers", "article_identifiers_other", choices.Choices.article_identifiers_val("other"))
        kvs.append((cls.q(26), article_identifiers))
        # kvs.append((cls.q(26, "other"), forminfo.get("article_identifiers_other")))

        kvs.append((cls.q(27), metadata_provision))
        kvs.append((cls.q(28), download_statistics))
        kvs.append((cls.q(29), forminfo.get("download_statistics_url")))
        kvs.append((cls.q(30), forminfo.get("first_fulltext_oa_year")))

        fulltext_formats = other_list("fulltext_format", "fulltext_format_other", choices.Choices.fulltext_format_val("other"))
        kvs.append((cls.q(31), fulltext_formats))
        # kvs.append((cls.q(31, "other"), forminfo.get("fulltext_format_other")))

        kvs.append((cls.q(32), ", ".join(forminfo.get("keywords", []))))
        kvs.append((cls.q(33), ", ".join(forminfo.get("languages", []))))
        kvs.append((cls.q(34), forminfo.get("editorial_board_url")))
        kvs.append((cls.q(35), forminfo.get("review_process")))
        kvs.append((cls.q(36), forminfo.get("review_process_url")))
        kvs.append((cls.q(37), forminfo.get("aims_scope_url")))
        kvs.append((cls.q(38), forminfo.get("instructions_authors_url")))
        kvs.append((cls.q(39), plagiarism_screening))
        kvs.append((cls.q(40), forminfo.get("plagiarism_screening_url")))
        kvs.append((cls.q(41), forminfo.get("publication_time")))
        kvs.append((cls.q(42), forminfo.get("oa_statement_url")))
        kvs.append((cls.q(43), license_embedded))
        kvs.append((cls.q(44), forminfo.get("license_embedded_url")))

        lic = forminfo.get("license")
        if lic == choices.Choices.licence_val("other"):
            lic = forminfo.get("license_other")
        kvs.append((cls.q(45), lic))
        # kvs.append((cls.q(45, "other"), forminfo.get("license_other")))

        kvs.append((cls.q(46), ", ".join(forminfo.get("license_checkbox", []))))
        kvs.append((cls.q(47), forminfo.get("license_url")))
        kvs.append((cls.q(48), open_access))

        deposit_policies = other_list("deposit_policy", "deposit_policy_other", choices.Choices.deposit_policy_other_val("other"))
        kvs.append((cls.q(49), deposit_policies))
        # kvs.append((cls.q(49, "other"), forminfo.get("deposit_policy_other")))

        cr = forminfo.get("copyright")
        if cr == choices.Choices.copyright_other_val("other"):
            cr = forminfo.get("copyright_other")
        kvs.append((cls.q(50), cr))
        # kvs.append((cls.q(50, "other"), copyright_other))

        kvs.append((cls.q(51), forminfo.get("copyright_url")))

        pr = forminfo.get("publishing_rights")
        if pr == choices.Choices.publishing_rights_other_val("other"):
            pr = forminfo.get("publishing_rights_other")
        kvs.append((cls.q(52), pr))
        # kvs.append((cls.q(52, "other"), publishing_rights_other))

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

            return norm

        def _rationalise_other(val, form_choices, other_val):
            val = normal(val)
            if val is None:
                return None

            opts = [aid.strip() for aid in val.split(",")]

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in form_choices]

            normopts = []
            otheropts = []
            for o in opts:
                if o.lower() in cs:
                    normopts.append(cs[o.lower()])
                else:
                    otheropts.append(o)

            if len(otheropts) > 0:
                normopts.append(other_val)

            return normopts, ", ".join(otheropts)

        def digital_archiving_policy(options, library, other):
            options = normal(options)
            library = normal(library)
            other = normal(other)

            if options is None:
                return None

            opts = [dap.strip() for dap in options.split(",")]

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in choices.Choices.digital_archiving_policy()]
            normopts = [cs[o.lower()] if o.lower() in cs else o for o in opts]

            lib = choices.Choices.digital_archiving_policy_val("library")
            oth = choices.Choices.digital_archiving_policy_val("other")
            if library is not None and library != "":
                if lib not in normopts:
                    normopts.append(lib)
            if other is not None and other != "":
                if oth not in normopts:
                    normopts.append(oth)

            return normopts, library, other

        def article_identifiers(val):
            return _rationalise_other(val, choices.Choices.article_identifiers(), choices.Choices.article_identifiers_val("other"))

        def fulltext_format(val):
            return _rationalise_other(val, choices.Choices.fulltext_format(), choices.Choices.fulltext_format_val("other"))

        def deposit_policy(val):
            return _rationalise_other(val, choices.Choices.deposit_policy(), choices.Choices.deposit_policy_other_val("other"))

        def get_license(val):
            return _this_or_other(val, choices.Choices.licence(), choices.Choices.licence_val("other"))
            """
            val = normal(val)
            if val is None:
                return None

            cs = {}
            [cs.update({c.lower() : c}) for c, _ in choices.Choices.licence()]

            if val.lower() in cs:
                return cs[val.lower()], ""
            else:
                return choices.Choices.licence_val("other"), val
            """

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
            if val is None:
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

            return normopts

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

        dap, lib, oth = digital_archiving_policy(cls.a(qs, 23), cls.a(qs, 23, "library"), cls.a(qs, 23, "other"))
        forminfo["digital_archiving_policy"] = dap
        forminfo["digital_archiving_policy_library"] = lib
        forminfo["digital_archiving_policy_other"] = oth

        forminfo["digital_archiving_policy_url"] = normal(cls.a(qs, 24))
        forminfo["crawl_permission"] = yes_no(cls.a(qs, 25))

        aids, aidother = article_identifiers(cls.a(qs, 26))
        forminfo["article_identifiers"] = aids
        forminfo["article_identifiers_other"] = aidother

        forminfo["metadata_provision"] = yes_no(cls.a(qs, 27))
        forminfo["download_statistics"] = yes_no(cls.a(qs, 28))
        forminfo["download_statistics_url"] = normal(cls.a(qs, 29))
        forminfo["first_fulltext_oa_year"] = normal(cls.a(qs, 30))

        ftf, ftfother = fulltext_format(cls.a(qs, 31))
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

        forminfo["license_checkbox"] = license_aspects(cls.a(qs, 46))
        forminfo["license_url"] = normal(cls.a(qs, 47))
        forminfo["open_access"] = yes_no(cls.a(qs, 48))

        dp, dpother = deposit_policy(cls.a(qs, 49))
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
