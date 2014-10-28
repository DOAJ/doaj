from portality import models
from portality.formcontext.xwalk import SuggestionFormXWalk
from portality.clcsv import ClCsv
from copy import deepcopy

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
        26 : {
            "other" : "If Other, enter it here"
        },
        31 : {
            "other" : "If Other, enter it here"
        },
        45 : {
            "other" : "If Other, enter it here"
        },
        49 : {
            "other" : "If Other, enter it here"
        },
        50 : {
            "other" : "If Other, enter it here"
        },
        52 : {
            "other" : "If Other, enter it here"
        }
    }

    @classmethod
    def q(cls, num, supp=None):
        if supp is None:
            return cls.QUESTIONS[num - 1]
        else:
            return cls.SUPPLEMENTARY_QUESTIONS[num][supp]

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
    def suggestion2question(cls, suggestion):
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
        kvs.append((cls.q(23), ", ".join(forminfo.get("digital_archiving_policy", []))))
        kvs.append((cls.q(23, "library"), forminfo.get("digital_archiving_policy_library")))
        kvs.append((cls.q(23, "other"), forminfo.get("digital_archiving_policy_other")))
        kvs.append((cls.q(24), forminfo.get("digital_archiving_policy_url")))
        kvs.append((cls.q(25), crawl_permission))
        kvs.append((cls.q(26), article_identifiers))
        kvs.append((cls.q(26, "other"), forminfo.get("article_identifiers_other")))
        kvs.append((cls.q(27), metadata_provision))
        kvs.append((cls.q(28), download_statistics))
        kvs.append((cls.q(29), forminfo.get("download_statistics_url")))
        kvs.append((cls.q(30), forminfo.get("first_fulltext_oa_year")))
        kvs.append((cls.q(31), ", ".join(forminfo.get("fulltext_format", []))))
        kvs.append((cls.q(31, "other"), forminfo.get("fulltext_format_other")))
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
        kvs.append((cls.q(45), forminfo.get("license")))
        kvs.append((cls.q(45, "other"), forminfo.get("license_other")))
        kvs.append((cls.q(46), ", ".join(forminfo.get("license_checkbox", []))))
        kvs.append((cls.q(47), forminfo.get("license_url")))
        kvs.append((cls.q(48), open_access))
        kvs.append((cls.q(49), deposit_policy))
        kvs.append((cls.q(49, "other"), forminfo.get("deposit_policy_other")))
        kvs.append((cls.q(50), forminfo.get("copyright")))
        kvs.append((cls.q(50, "other"), copyright_other))
        kvs.append((cls.q(51), forminfo.get("copyright_url")))
        kvs.append((cls.q(52), forminfo.get("publishing_rights")))
        kvs.append((cls.q(52, "other"), publishing_rights_other))
        kvs.append((cls.q(53), forminfo.get("publishing_rights_url")))

        return kvs
