from copy import deepcopy
from portality import datasets
from portality.formcontext import choices
from portality.crosswalks.journal_form import JournalFormXWalk


class JournalXwalkException(Exception):
    pass


class Journal2QuestionXwalk(object):

    QTUP = [
        ("alternative_title", "Alternative title"),
        ("apc_charges.apc_max", "APC amount"),
        ("apc_url", "APC information URL"),
        ("preservation_service", "Preservations Services"),
        ("preservation_service_library", "Preservation Service: national library"),
        ("preservation_service_url", "Preservation information URL"),
        ("copyright_author_retains", "Author holds copyright without restrictions"),
        ("copyright_url", "Copyright information URL"),
        ("publisher.publisher_country", "Country of publisher"),
        ("deposit_policy", "Deposit policy directory"),
        ("review_process", "Review process"),
        ("review_url", "Review process information URL"),
        ("pissn", "Journal ISSN (print version)"),
        ("eissn", "Journal EISSN (online version)"),
        ("institution.institution_name", "Society or institution"),
        ("keywords", "Keywords"),
        ("language", "Full text language"),
        ("license_attributes", "License attributes"),
        ("license_display", "Machine-readable CC licensing information embedded or displayed in articles"),
        ("license_display_example_url", "URL to an example page with embedded licensing information"),
        ("boai", "Does this journal allow unrestricted reuse in compliance with BOAI?"),
        ("license", "Journal license"),
        ("license_terms_url", "URL for license terms"),
        ("oa_statement_url", "URL for journal's Open Access statement"),
        ("journal_url", "Journal URL"),
        ("aims_scope_url", "URL for journal's aims & scope"),
        ("editorial_board_url", "URL for the Editorial Board page"),
        ("author_instructions_url", "URL for journal's instructions for authors"),
        ("waiver_url", "Waiver policy information URL"),
        ("persistent_identifiers", "Permanent article identifiers"),
        ("plagiarism_detection", "Journal plagiarism screening policy"),
        ("plagiarism_url", "Plagiarism information URL"),
        ("publication_time_weeks", "Average number of weeks between submission and publication"),
        ("publisher.publisher_name", "Publisher"),
        ("other_charges_url", "Other submission charges information URL"),
        ("title", "Journal title"),
        ("institution.institution_country", "Country of society or institution"),
        ("apc", "APC"),
        ("has_other_charges", "Has other submission charges"),
        ("has_waiver", "Journal waiver policy (for developing country authors etc)"),
        ("orcid_ids", "Article metadata includes ORCIDs"),
        ("open_citations", "Journal complies with I4OC standards for open citations"),
        ("deposit_policy_url", "URL for deposit policy")
    ]

    DEGEN = {
        "preservation_service_other" : "preservation_service",
        "deposit_policy_other": "deposit_policy",
        "review_process_other" : "review_process",
        "persistent_identifiers_other" : "persistent_identifiers"
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
    def question_list(cls):
        return [q for _, q in cls.QTUP]

    @classmethod
    def journal2question(cls, journal):

        def yes_no_or_blank(val):
            return "Yes" if val in [True, "True", "Yes", "true", "yes", "y"] else "No" if val is not None else ""

        def other_list(main_field, other_field, other_value):
            aids = forminfo.get(main_field, [])
            if aids is None or aids == "" or aids == "None":
                aids = []

            # if the xwalk has returned a single-list element like ["None"]
            # we want to strip that "None" for the purpose of the CSV
            if "none" in aids:
                aids.remove("none")

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
        kvs.append((cls.q("journal_url"), forminfo.get("journal_url")))
        kvs.append((cls.q("alternative_title"), forminfo.get("alternative_title")))
        kvs.append((cls.q("pissn"), forminfo.get("pissn")))
        kvs.append((cls.q("eissn"), forminfo.get("eissn")))
        kvs.append((cls.q("publisher.publisher_name"), forminfo.get("publisher", {}).get("publisher_name")))
        kvs.append((cls.q("publisher.publisher_country"), datasets.get_country_name(forminfo.get("publisher", {}).get("publisher_country"))))
        kvs.append((cls.q("institution.institution_name"), forminfo.get("institution", {}).get("institution_name")))
        kvs.append((cls.q("institution.institution_country"), datasets.get_country_name(forminfo.get("institution", {}).get("institution_country"))))
        kvs.append((cls.q("apc"), yes_no_or_blank(forminfo.get("apc"))))
        kvs.append((cls.q("apc_url"), forminfo.get("apc_url")))

        apcs = []
        for apc_charge in forminfo.get("apc_charges", []):
            apcs.append(str(apc_charge.get("apc_max")) + " " + apc_charge.get("apc_currency"))
        kvs.append((cls.q("apc_charges.apc_max"), "; ".join(apcs)))

        kvs.append((cls.q("has_other_charges"), yes_no_or_blank(forminfo.get("has_other_charges"))))
        kvs.append((cls.q("other_charges_url"), forminfo.get("other_charges_url")))
        kvs.append((cls.q("has_waiver"), yes_no_or_blank(forminfo.get("has_waiver"))))
        kvs.append((cls.q("waiver_url"), forminfo.get("waiver_url")))

        dap = deepcopy(forminfo.get("preservation_service", []))
        if "national_library" in dap: dap.remove("national_library")
        if "other" in dap:
            dap.remove("other")
            dap.append(forminfo.get("preservation_service_other"))
        if "none" in dap: dap.remove("none")
        kvs.append((cls.q("preservation_service"), ", ".join(dap)))

        kvs.append((cls.q("preservation_service_library"), "; ".join(forminfo.get("preservation_service_library", []))))
        kvs.append((cls.q("preservation_service_url"), forminfo.get("preservation_service_url")))

        article_identifiers = other_list("persistent_identifiers", "persistent_identifiers_other", "other")
        kvs.append((cls.q("persistent_identifiers"), article_identifiers))

        kvs.append((cls.q("keywords"), ", ".join(forminfo.get("keywords", []))))
        kvs.append((cls.q("language"), languages(forminfo.get("language", []))))
        kvs.append((cls.q("editorial_board_url"), forminfo.get("editorial_board_url")))

        review_process = other_list("review_process", "review_process_other", "other")
        kvs.append((cls.q("review_process"), review_process))

        kvs.append((cls.q("review_url"), forminfo.get("review_url")))
        kvs.append((cls.q("aims_scope_url"), forminfo.get("aims_scope_url")))
        kvs.append((cls.q("author_instructions_url"), forminfo.get("author_instructions_url")))
        kvs.append((cls.q("plagiarism_detection"), yes_no_or_blank(forminfo.get("plagiarism_detection"))))
        kvs.append((cls.q("plagiarism_url"), forminfo.get("plagiarism_url")))
        kvs.append((cls.q("publication_time_weeks"), str(forminfo.get("publication_time_weeks"))))
        kvs.append((cls.q("oa_statement_url"), forminfo.get("oa_statement_url")))

        kvs.append((cls.q("license_display"), ", ".join(forminfo.get("license_display"))))
        kvs.append((cls.q("license_display_example_url"), forminfo.get("license_display_example_url")))

        lic = ", ".join(forminfo.get("license", []))
        kvs.append((cls.q("license"), lic))

        kvs.append((cls.q("license_attributes"), license_checkbox(forminfo.get("license_attributes", []))))
        kvs.append((cls.q("license_terms_url"), forminfo.get("license_terms_url")))
        kvs.append((cls.q("boai"), yes_or_blank(forminfo.get("boai"))))

        deposit_policies = other_list("deposit_policy", "deposit_policy_other", "other")
        kvs.append((cls.q("deposit_policy"), deposit_policies))
        kvs.append((cls.q("deposit_policy_url"), forminfo.get("deposit_policy_url")))
        kvs.append((cls.q("copyright_author_retains"), yes_no_or_blank(forminfo.get("copyright_author_retains"))))
        kvs.append((cls.q("copyright_url"), forminfo.get("copyright_url")))
        kvs.append((cls.q("orcid_ids"), yes_no_or_blank(forminfo.get("orcid_ids"))))
        kvs.append((cls.q("open_citations"), yes_no_or_blank(forminfo.get("open_citations"))))

        return kvs