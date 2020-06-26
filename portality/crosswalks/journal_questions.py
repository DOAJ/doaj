from copy import deepcopy
from portality import datasets
from portality.formcontext import choices
from crosswalks.journal_form import JournalFormXWalk


class JournalXwalkException(Exception):
    pass


class Journal2QuestionXwalk(object):

    QTUP = [
        ("title",                               "Journal title"),
        ("url",                                 "Journal URL"),
        ("alternative_title",                   "Alternative title"),
        ("pissn",                               "Journal ISSN (print version)"),
        ("eissn",                               "Journal EISSN (online version)"),
        ("publisher",                           "Publisher"),
        ("society_institution",                 "Society or institution"),
        ("platform",                            "Platform, host or aggregator"),
        ("country",                             "Country of publisher"),
        ("processing_charges",                  "Journal article processing charges (APCs)"),
        ("processing_charges_url",              "APC information URL"),
        ("processing_charges_amount",           "APC amount"),
        ("processing_charges_currency",         "Currency"),
        ("submission_charges",                  "Journal article submission fee"),
        ("submission_charges_url",              "Submission fee URL"),
        ("submission_charges_amount",           "Submission fee amount"),
        ("submission_charges_currency",         "Submission fee currency"),
        # these fields are available on the application but not the journal
        #("articles_last_year",                  "Number of articles published in the last calendar year"),
        #("articles_last_year_url",              "Number of articles information URL"),
        ("waiver_policy",                       "Journal waiver policy (for developing country authors etc)"),
        ("waiver_policy_url",                   "Waiver policy information URL"),
        ("digital_archiving_policy",            "Digital archiving policy or program(s)"),
        ("digital_archiving_policy_library",    "Archiving: national library"),
        ("digital_archiving_policy_other",      "Archiving: other"),
        ("digital_archiving_policy_url",        "Archiving infomation URL"),
        ("crawl_permission",                    "Journal full-text crawl permission"),
        ("article_identifiers",                 "Permanent article identifiers"),
        ("metadata_provision",                  "Article level metadata in DOAJ"),
        ("download_statistics",                 "Journal provides download statistics"),
        ("download_statistics_url",             "Download statistics information URL"),
        ("first_fulltext_oa_year",              "First calendar year journal provided online Open Access content"),
        ("fulltext_format",                     "Full text formats"),
        ("keywords",                            "Keywords"),
        ("languages",                           "Full text language"),
        ("editorial_board_url",                 "URL for the Editorial Board page"),
        ("review_process",                      "Review process"),
        ("review_process_url",                  "Review process information URL"),
        ("aims_scope_url",                      "URL for journal's aims & scope"),
        ("instructions_authors_url",            "URL for journal's instructions for authors"),
        ("plagiarism_screening",                "Journal plagiarism screening policy"),
        ("plagiarism_screening_url",            "Plagiarism information URL"),
        ("publication_time",                    "Average number of weeks between submission and publication"),
        ("oa_statement_url",                    "URL for journal's Open Access statement"),
        ("license_embedded",                    "Machine-readable CC licensing information embedded or displayed in articles"),
        ("license_embedded_url",                "URL to an example page with embedded licensing information"),
        ("license",                             "Journal license"),
        ("license_checkbox",                    "License attributes"),
        ("license_url",                         "URL for license terms"),
        ("open_access",                         "Does this journal allow unrestricted reuse in compliance with BOAI?"),
        ("deposit_policy",                      "Deposit policy directory"),
        ("copyright",                           "Author holds copyright without restrictions"),
        ("copyright_url",                       "Copyright information URL"),
        ("publishing_rights",                   "Author holds publishing rights without restrictions"),
        ("publishing_rights_url",               "Publishing rights information URL")
    ]

    DEGEN = {
        "article_identifiers_other": "article_identifiers",
        "fulltext_format_other": "fulltext_format",
        "license_other": "license",
        "deposit_policy_other": "deposit_policy"
    }

    @classmethod
    def q(cls, ident):
        if ident in cls.DEGEN:
            ident = cls.DEGEN[ident]
        for k, q in cls.QTUP:
            if k == ident:
                return q
        return None

    @classmethod
    def q2idx(cls, ident):
        if ident in cls.DEGEN:
            ident = cls.DEGEN[ident]
        i = 0
        for k, q in cls.QTUP:
            if k == ident:
                return i
            i += 1
        return -1

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
    def journal2question(cls, journal):

        def other_list(main_field, other_field, other_value):
            aids = forminfo.get(main_field, [])
            if aids is None or aids == "" or aids == "None":
                aids = []

            # if the xwalk has returned a single-list element like ["None"]
            # we want to strip that "None" for the purpose of the CSV
            if choices.Choices.NONE in aids:
                aids.remove(choices.Choices.NONE)

            aidother = forminfo.get(other_field)

            if other_value in aids:
                aids.remove(other_value)
            if aidother is not None and aidother != "" and aidother != "None":
                aids.append(aidother)
            return ", ".join(aids)

        def yes_or_blank(val):
            return "Yes" if val in [True, "True", "Yes", "true", "yes"] else ''

        def license_checkbox(val):
            opts = {}
            [opts.update({k : v}) for k,v  in choices.Choices.licence_checkbox()]
            nv = [opts.get(v) for v in val]
            return ", ".join(nv)

        def languages(vals):
            keep = []
            codes = [c.lower() for c, _ in datasets.language_options]
            names = [n.lower() for _, n in datasets.language_options]
            for v in vals:
                if v.lower() in codes:
                    keep.append(datasets.name_for_lang(v))
                elif v.lower() in names:
                    keep.append(v)
            return ", ".join(keep)

        # start by converting the object to the forminfo version
        forminfo = JournalFormXWalk.obj2form(journal)

        kvs = []

        # create key/value pairs for the questions in order
        kvs.append((cls.q("title"), forminfo.get("title")))
        kvs.append((cls.q("url"), forminfo.get("url")))
        kvs.append((cls.q("alternative_title"), forminfo.get("alternative_title")))
        kvs.append((cls.q("pissn"), forminfo.get("pissn")))
        kvs.append((cls.q("eissn"), forminfo.get("eissn")))
        kvs.append((cls.q("publisher"), forminfo.get("publisher")))
        kvs.append((cls.q("society_institution"), forminfo.get("society_institution")))
        kvs.append((cls.q("platform"), forminfo.get("platform")))
        kvs.append((cls.q("country"), datasets.get_country_name(forminfo.get("country"))))
        # Get the APC info from journal index, since this includes [yes / no / no information] rather than true / false
        kvs.append((cls.q("processing_charges"), journal.data.get("index", {}).get("has_apc")))
        kvs.append((cls.q("processing_charges_url"), forminfo.get("processing_charges_url")))
        kvs.append((cls.q("processing_charges_amount"), forminfo.get("processing_charges_amount")))
        kvs.append((cls.q("processing_charges_currency"), datasets.get_currency_name(forminfo.get("processing_charges_currency"))))
        kvs.append((cls.q("submission_charges"), yes_or_blank(forminfo.get("submission_charges"))))
        kvs.append((cls.q("submission_charges_url"), forminfo.get("submission_charges_url")))
        kvs.append((cls.q("submission_charges_amount"), forminfo.get("submission_charges_amount")))
        kvs.append((cls.q("submission_charges_currency"), datasets.get_currency_name(forminfo.get("submission_charges_currency"))))
        # these fields are present in the application but not the journal
        #kvs.append((cls.q("articles_last_year"), forminfo.get("articles_last_year", "")))
        #kvs.append((cls.q("articles_last_year_url"), forminfo.get("articles_last_year_url", "")))
        kvs.append((cls.q("waiver_policy"), yes_or_blank(forminfo.get("waiver_policy"))))
        kvs.append((cls.q("waiver_policy_url"), forminfo.get("waiver_policy_url")))

        dap = deepcopy(forminfo.get("digital_archiving_policy", []))
        lib = choices.Choices.digital_archiving_policy_val("library")
        oth = choices.Choices.digital_archiving_policy_val("other")
        if lib in dap: dap.remove(lib)
        if oth in dap: dap.remove(oth)
        if choices.Choices.digital_archiving_policy_val('none') in dap:
            dap.remove(choices.Choices.digital_archiving_policy_val('none'))
        kvs.append((cls.q("digital_archiving_policy"), ", ".join(dap)))
        kvs.append((cls.q("digital_archiving_policy_library"), forminfo.get("digital_archiving_policy_library")))
        kvs.append((cls.q("digital_archiving_policy_other"), forminfo.get("digital_archiving_policy_other")))

        kvs.append((cls.q("digital_archiving_policy_url"), forminfo.get("digital_archiving_policy_url")))
        kvs.append((cls.q("crawl_permission"), yes_or_blank(forminfo.get("crawl_permission"))))

        article_identifiers = other_list("article_identifiers", "article_identifiers_other", choices.Choices.article_identifiers_val("other"))
        kvs.append((cls.q("article_identifiers"), article_identifiers))

        kvs.append((cls.q("download_statistics"), yes_or_blank(forminfo.get("download_statistics"))))
        kvs.append((cls.q("download_statistics_url"), forminfo.get("download_statistics_url")))
        kvs.append((cls.q("first_fulltext_oa_year"), forminfo.get("first_fulltext_oa_year")))

        fulltext_formats = other_list("fulltext_format", "fulltext_format_other", choices.Choices.fulltext_format_val("other"))
        kvs.append((cls.q("fulltext_format"), fulltext_formats))

        kvs.append((cls.q("keywords"), ", ".join(forminfo.get("keywords", []))))
        kvs.append((cls.q("languages"), languages(forminfo.get("languages", []))))
        kvs.append((cls.q("editorial_board_url"), forminfo.get("editorial_board_url")))
        kvs.append((cls.q("review_process"), forminfo.get("review_process", '')))
        kvs.append((cls.q("review_process_url"), forminfo.get("review_process_url")))
        kvs.append((cls.q("aims_scope_url"), forminfo.get("aims_scope_url")))
        kvs.append((cls.q("instructions_authors_url"), forminfo.get("instructions_authors_url")))
        kvs.append((cls.q("plagiarism_screening"), yes_or_blank(forminfo.get("plagiarism_screening"))))
        kvs.append((cls.q("plagiarism_screening_url"), forminfo.get("plagiarism_screening_url")))
        kvs.append((cls.q("publication_time"), forminfo.get("publication_time")))
        kvs.append((cls.q("oa_statement_url"), forminfo.get("oa_statement_url")))
        kvs.append((cls.q("license_embedded"), yes_or_blank(forminfo.get("license_embedded"))))
        kvs.append((cls.q("license_embedded_url"), forminfo.get("license_embedded_url")))

        lic = forminfo.get("license")
        if lic == choices.Choices.licence_val("other"):
            lic = forminfo.get("license_other")
        kvs.append((cls.q("license"), lic))

        kvs.append((cls.q("license_checkbox"), license_checkbox(forminfo.get("license_checkbox", []))))
        kvs.append((cls.q("license_url"), forminfo.get("license_url")))
        kvs.append((cls.q("open_access"), yes_or_blank(forminfo.get("open_access"))))

        deposit_policies = other_list("deposit_policy", "deposit_policy_other", choices.Choices.deposit_policy_other_val("other"))
        kvs.append((cls.q("deposit_policy"), deposit_policies))

        cr = forminfo.get("copyright")
        kvs.append((cls.q("copyright"), cr))

        kvs.append((cls.q("copyright_url"), forminfo.get("copyright_url")))

        pr = forminfo.get("publishing_rights")
        kvs.append((cls.q("publishing_rights"), pr))

        kvs.append((cls.q("publishing_rights_url"), forminfo.get("publishing_rights_url")))

        return kvs