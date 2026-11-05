from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.workflow.submission.forms import SubmissionRO, SubmissionROForm
from portality.models import WorkflowControl, Application
from portality.datasets import get_currency_code

class WorkflowControl2SubmissionForm(object):

    # MAP = {
    #     "ethics_not_excluded": TriageSubmission.struct.ethics.not_excluded,
    #     "ethics_no_nonstandard_metrics": TriageSubmission.struct.ethics.no_nonstandard_metrics,
    #     "ethics_no_fake_impact": TriageSubmission.struct.ethics.no_fake_impact,
    #     "ethics_no_false_doaj_claim": TriageSubmission.struct.ethics.no_false_doaj_claim,
    #     "ethics_no_suspicious_ties": TriageSubmission.struct.ethics.no_suspicious_ties,
    #     "ethics_submission_to_publication_time": TriageSubmission.struct.ethics.publication_time,
    #     "database_withdrawn": TriageSubmission.struct.database.withdrawn,
    #     "database_embargo": TriageSubmission.struct.database.embargo,
    #     "database_not_listed": TriageSubmission.struct.database.not_listed,
    #     "database_not_duplicate": TriageSubmission.struct.database.not_duplicate,
    #     "issn_at_least_one": TriageSubmission.struct.issn.at_least_one,
    #     "issn_country_match": TriageSubmission.struct.issn.country_match,
    #     "issn_title_match": TriageSubmission.struct.issn.title_match,
    #     "issn_continuation": TriageSubmission.struct.issn.continuation,
    #     "website_working": TriageSubmission.struct.website.working,
    #     "website_issn": TriageSubmission.struct.website.issn,
    #     "website_url": TriageSubmission.struct.website.url,
    #     "website_license_policy": TriageSubmission.struct.website.license_policy,
    #     "website_copyright": TriageSubmission.struct.website.copyright,
    #     "content_no_login": TriageSubmission.struct.content.no_login,
    #     "content_no_embargo": TriageSubmission.struct.content.no_embargo,
    #     "content_publish_enough": TriageSubmission.struct.content.publish_enough,
    #     "content_unique_link": TriageSubmission.struct.content.unique_link,
    #     "content_format": TriageSubmission.struct.content.format,
    #     "content_new_journal": TriageSubmission.struct.content.new_journal,
    #     "admin_metadata_review": TriageSubmission.struct.metadata_review.metadata_review,
    #     "admin_special_exception": TriageSubmission.struct.special_exception.special_exception
    # }

    # def structure_map(self, triage_field_name: TriageField):
    #     return self.MAP.get(triage_field_name)

    def transform(self, wfc:WorkflowControl, application:Application) -> SubmissionRO:
        # Use the existing form crosswalk to get the public forminfo
        forminfo = ApplicationFormXWalk.obj2form(application)

        # now convert that into the new form
        form = SubmissionRO()
        f:SubmissionROForm = SubmissionRO.struct

        form.set(f.about_the_journal.about.title, forminfo.get("title"))
        form.set(f.about_the_journal.about.alternative_title, forminfo.get("alternative_title"))
        form.set(f.about_the_journal.publisher.publisher_name, forminfo.get("publisher_name"))
        form.set(f.about_the_journal.publisher.publisher_country, forminfo.get("publisher_country"))
        form.set(f.about_the_journal.about.pissn, forminfo.get("pissn"))
        form.set(f.about_the_journal.about.eissn, forminfo.get("eissn"))
        form.set(f.about_the_journal.institution.institution_name, forminfo.get("institution_name"))
        form.set(f.about_the_journal.institution.institution_country, forminfo.get("institution_country"))
        form.set(f.about_the_journal.about.keywords, forminfo.get("keywords"))
        form.set(f.about_the_journal.about.language, forminfo.get("language"))
        form.set(f.about_the_journal.about.journal_url, forminfo.get("journal_url"))

        form.set(f.oa_compliance.basic_compliance.boai, forminfo.get("boai"))
        form.set(f.oa_compliance.basic_compliance.oa_start, forminfo.get("oa_start"))
        form.set(f.oa_compliance.basic_compliance.oa_statement_url, forminfo.get("oa_statement_url"))

        form.set(f.business_model.apc.has_apc, forminfo.get("has_apc"))
        form.set(f.business_model.apc.apc_charges, forminfo.get("apc_charges"))
        form.set(f.business_model.apc.apc_url, forminfo.get("apc_url"))
        form.set(f.business_model.apc_waivers.has_waiver, forminfo.get("has_waiver"))
        form.set(f.business_model.apc_waivers.waiver_url, forminfo.get("waiver_url"))
        form.set(f.business_model.other_fees.has_other_charges, forminfo.get("has_other_charges"))
        form.set(f.business_model.other_fees.other_charges_url, forminfo.get("other_charges_url"))

        form.set(f.best_practices.archiving_policy.preservation_service, forminfo.get("preservation_service"))
        form.set(f.best_practices.archiving_policy.preservation_service_other, forminfo.get("preservation_service_other"))
        form.set(f.best_practices.archiving_policy.preservation_service_library, forminfo.get("preservation_service_library"))
        form.set(f.best_practices.archiving_policy.preservation_service_url, forminfo.get("preservation_service_url"))
        form.set(f.best_practices.unique_identifiers.persistent_identifiers, forminfo.get("persistent_identifiers"))
        form.set(f.best_practices.unique_identifiers.persistent_identifiers_other, forminfo.get("persistent_identifiers_other"))
        form.set(f.best_practices.plagiarism_detection.plagiarism_detection, forminfo.get("plagiarism_detection"))
        form.set(f.best_practices.plagiarism_detection.plagiarism_url, forminfo.get("plagiarism_url"))

        form.set(f.copyright_licensing.copyright.author_retains_copyright, forminfo.get("copyright_author_retains"))
        form.set(f.copyright_licensing.copyright.copyright_url, forminfo.get("copyright_url"))
        form.set(f.copyright_licensing.licensing.license, forminfo.get("license"))
        form.set(f.copyright_licensing.licensing.license_attributes, forminfo.get("license_attributes"))
        form.set(f.copyright_licensing.embedded_licensing.license_display, forminfo.get("license_display"))
        form.set(f.copyright_licensing.embedded_licensing.license_display_example_url, forminfo.get("license_display_example_url"))
        form.set(f.copyright_licensing.licensing.license_terms_url, forminfo.get("license_terms_url"))

        form.set(f.best_practices.repository_policy.deposit_policy, forminfo.get("deposit_policy"))
        form.set(f.best_practices.repository_policy.deposit_policy_other, forminfo.get("deposit_policy_other"))
        form.set(f.best_practices.repository_policy.deposit_policy_url, forminfo.get("deposit_policy_url"))

        form.set(f.editorial.peer_review.review_process, forminfo.get("review_process"))
        form.set(f.editorial.peer_review.review_process_other, forminfo.get("review_process_other"))
        form.set(f.editorial.peer_review.review_url, forminfo.get("review_url"))
        form.set(f.editorial.editorial.aims_scope_url, forminfo.get("aims_scope_url"))
        form.set(f.editorial.editorial.editorial_board_url, forminfo.get("editorial_board_url"))
        form.set(f.editorial.editorial.author_instructions_url, forminfo.get("author_instructions_url"))
        form.set(f.editorial.editorial.publication_time_weeks, forminfo.get("publication_time_weeks"))

        return form