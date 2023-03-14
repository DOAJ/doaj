from portality import models, lcc
from portality.crosswalks.journal_form import JournalGenericXWalk, JournalFormXWalk


class ApplicationFormXWalk(JournalGenericXWalk):
    """
    ~~ApplicationForm:Crosswalk->Application:Model~~
    ~~->Application:Form~~
    """
    _formFields2objectFields = {
        "alternative_title" : "bibjson.alternative_title",
        "apc_charges.apc_max" : "bibjson.apc.max.price",
        "apc_charges.apc_currency" : "bibjson.apc.max.currency",
        "apc_url" : "bibjson.apc.url",
        "preservation_service" : "bibjson.preservation.service",
        "preservation_service_other" : "bibjson.preservation.service",
        "preservation_service_library" : "bibjson.preservation.national_library",
        "preservation_service_url" : "bibjson.preservation.url",
        "copyright_author_retains" : "bibjson.copyright.author_retains",
        "copyright_url" : "bibjson.copyright.url",
        "publisher.publisher_country" : "bibjson.publisher.country",
        "deposit_policy" : "bibjson.deposit_policy.service",
        "deposit_policy_other" : "bibjson.deposit_policy.service",
        "review_process" : "bibjson.editorial.review_process",
        "review_process_other" : "bibjson.editorial.review_process",
        "review_url" : "bibjson.editorial.review_url",
        "pissn" : "bibjson.pissn",
        "eissn" : "bibjson.eissn",
        "institution.institution_name" : "bibjson.institution.name",
        "keywords" : "bibjson.keywords",
        "language" : "bibjson.language",
        "license_attributes" : (["bibjson.license.BY", "bibjson.license.NC", "bibjson.license.ND", "bibjson.license.SA"],
                                "bibjson.license[].BY, NC, ND and SA"),
        "license_display" : "bibjson.article.license_display",
        "license_display_example_url" : "bibjson.article.license_display_example_url",
        "boai" : "bibjson.boai",
        "license" : "bibjson.license.type",
        "license_terms_url" : "bibjson.license.url",
        "oa_start": "bibjson.oa_start",
        "oa_statement_url" : "bibjson.ref.oa_statement",
        "journal_url" : "bibjson.ref.journal",
        "aims_scope_url" : "bibjson.ref.aims_scope",
        "editorial_board_url" : "bibjon.editorial.board_url",
        "author_instructions_url" : "bibjson.ref.author_instructions",
        "waiver_url" : "bibjson.waiver.url",
        "persistent_identifiers" : "bibjson.pid_scheme.scheme",
        "persistent_identifiers_other" : "bibjson.pid_scheme.scheme",
        "plagiarism_detection" : "bibjson.plagiarism.detection",
        "plagiarism_url" : "bibjson.plagiarism.url",
        "publication_time_weeks" : "bibjson.publication_time_weeks",
        "other_charges_url" : "bibjson.other_charges_url",
        "title" : "bibjson.title",
        "institution.institution_country" : "bibjson.institution.country",
        "apc" : "bibjson.apc.has_apc",
        "has_other_charges" : "bibjson.other_charges.has_other_charges",
        "has_waiver" : "bibjson.waiver.has_waiver",
        "orcid_ids" : "bibjson.article.orcid",
        "open_citations" : "bibjson.article.i4oc_open_citations",
        "deposit_policy_url" : "bibjson.deposit_policy.url"
    }

    @classmethod
    def formField2objectField(cls, field):
        data = cls._formFields2objectFields.get(field, field)
        if isinstance(data, str):
            return data
        return data[1]

    @classmethod
    def formField2objectFields(cls, field):
        data = cls._formFields2objectFields.get(field, field)
        if isinstance(data, str):
            return [data]
        fields = data[0]
        if not isinstance(fields, list):
            return [fields]
        return fields

    @classmethod
    def form2obj(cls, form) -> models.Application:
        application = models.Application()
        bibjson = application.bibjson()

        cls.form2bibjson(form, bibjson)
        cls.form2admin(form, application)

        # admin stuff
        if getattr(form, 'application_status', None):
            application.set_application_status(form.application_status.data)

        return application

    @classmethod
    def obj2formdata(cls, obj):
        forminfo = cls.obj2form(obj)
        return cls.forminfo2multidict(forminfo)

    @classmethod
    def obj2form(cls, obj) -> dict:
        forminfo = {}
        bibjson = obj.bibjson()

        cls.bibjson2form(bibjson, forminfo)
        cls.admin2form(obj, forminfo)

        forminfo['application_status'] = obj.application_status

        return forminfo

    @classmethod
    def update_request_diff(cls, source):
        """
        ~~->Journal:Model~~
        ~~->JournalForm:Crosswalk~~
        ~~->UpdateRequest:Feature~~
        :param source:
        :return:
        """
        diff = None
        cj = None

        current_journal = source.current_journal
        if current_journal is not None:
            cj = models.Journal.pull(current_journal)
            if cj is not None:
                jform = JournalFormXWalk.obj2form(cj)
                if "notes" in jform:
                    del jform["notes"]
                aform = ApplicationFormXWalk.obj2form(source)
                if "notes" in aform:
                    del aform["notes"]
                diff = cls.form_diff(jform, aform)

        return diff, cj
