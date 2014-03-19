from datetime import datetime

from portality.models import Suggestion
from portality.view import forms
from portality.datasets import licenses


class SuggestionFormXWalk(object):

    @staticmethod
    def form2obj(form):
        suggestion = Suggestion()
        bibjson = suggestion.bibjson()

        bibjson.title = form.title.data
        bibjson.add_url(form.url.data, urltype='homepage')
        bibjson.alternative_title = form.alternative_title.data
        bibjson.add_identifier(bibjson.P_ISSN, form.pissn.data)
        bibjson.add_identifier(bibjson.E_ISSN, form.eissn.data)
        bibjson.publisher = form.publisher.data
        bibjson.institution = form.society_institution.data
        bibjson.provider = form.platform.data
        suggestion.add_contact(form.contact_name.data, form.contact_email.data)
        bibjson.country = form.country.data

        if forms.interpret_special(form.processing_charges.data):
            bibjson.set_apc(form.processing_charges_currency.data, form.processing_charges_amount.data)

        if forms.interpret_special(form.submission_charges.data):
            bibjson.set_submission_charges(form.submission_charges_currency.data, form.submission_charges_amount.data)

        suggestion.set_articles_last_year(form.articles_last_year.data, form.articles_last_year_url.data)

        if forms.interpret_special(form.waiver_policy.data):
            bibjson.add_url(form.waiver_policy_url.data, 'waiver_policy')

        # checkboxes
        archiving_policies = forms.interpret_special(form.digital_archiving_policy.data)
        archiving_policies = forms.interpret_other(archiving_policies, form.digital_archiving_policy_other.data)
        archiving_policies = forms.interpret_other(archiving_policies, form.digital_archiving_policy_library.data, forms.digital_archiving_policy_specific_library_value)
        bibjson.set_archiving_policy(archiving_policies, form.digital_archiving_policy_url.data)

        bibjson.allows_fulltext_indexing = forms.interpret_special(form.crawl_permission.data)  # just binary

        # checkboxes
        article_ids = forms.interpret_special(form.article_identifiers.data)
        bibjson.persistent_identifier_scheme = forms.interpret_other(article_ids, form.article_identifiers_other.data)

        suggestion.article_metadata = forms.interpret_special(form.metadata_provision.data)  # just binary

        bibjson.set_article_statistics(form.download_statistics_url.data, forms.interpret_special(form.download_statistics.data))

        bibjson.set_oa_start(year=form.first_fulltext_oa_year.data)

        # checkboxes
        bibjson.format = forms.interpret_other(form.fulltext_format.data, form.fulltext_format_other.data)

        bibjson.set_keywords(form.keywords.data)  # tag list field

        bibjson.set_language(form.languages.data)  # select multiple field - gives a list back

        bibjson.add_url(form.editorial_board_url.data, urltype='editorial_board')

        bibjson.set_editorial_review(form.review_process.data, form.review_process_url.data)

        bibjson.add_url(form.aims_scope_url.data, urltype='aims_scope')
        bibjson.add_url(form.instructions_authors_url.data, urltype='author_instructions')

        bibjson.set_plagiarism_detection(
            form.plagiarism_screening_url.data,
            has_detection=forms.interpret_special(form.plagiarism_screening.data)
        )

        bibjson.publication_time = form.publication_time.data

        bibjson.add_url(form.oa_statement_url.data, urltype='oa_statement')

        license_type = forms.interpret_other(form.license.data, form.license_other.data)
        if license_type in licenses:
            by = licenses[license_type]['BY']
            nc = licenses[license_type]['NC']
            nd = licenses[license_type]['ND']
            sa = licenses[license_type]['SA']
            license_title = licenses[license_type]['title']
        elif form.license_checkbox.data:
            by = True if 'by' in form.license_checkbox.data else False
            nc = True if 'nc' in form.license_checkbox.data else False
            nd = True if 'nd' in form.license_checkbox.data else False
            sa = True if 'sa' in form.license_checkbox.data else False
            license_title = license_type
        else:
            by = None; nc = None; nd = None; sa = None;
            license_title = license_type

        bibjson.set_license(
            license_title,
            license_type,
            url=form.license_url.data,
            open_access=forms.interpret_special(form.open_access.data),
            by=by, nc=nc, nd=nd, sa=sa,
            embedded=forms.interpret_special(form.license_embedded.data),
            embedded_example_url=form.license_embedded_url.data
        )

        # checkboxes
        deposit_policies = forms.interpret_special(form.deposit_policy.data)  # need empty list if it's just "None"
        bibjson.deposit_policy = forms.interpret_other(deposit_policies, form.deposit_policy_other.data) 

        bibjson.set_author_copyright(
            form.copyright_url.data,
            holds_copyright=forms.interpret_other(
                forms.interpret_special(form.copyright.data),
                form.copyright_other.data
            )
        )

        bibjson.set_author_publishing_rights(
            form.publishing_rights_url.data,
            holds_rights=forms.interpret_other(
                forms.interpret_special(form.publishing_rights.data),
                form.publishing_rights_other.data
            )
        )

        suggestion.set_suggester(form.suggester_name.data, form.suggester_email.data)
        suggestion.suggested_on = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        suggestion.set_application_status('pending')

        return suggestion