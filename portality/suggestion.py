from datetime import datetime
from flask import url_for, render_template, flash

from portality.models import Suggestion
from portality.view import forms
from portality.datasets import licenses
from portality.view.forms import other_val, digital_archiving_policy_specific_library_value
from werkzeug.utils import redirect


def suggestion_form(form, request, redirect_url_on_success, template_name, existing_suggestion=None, **kwargs):
    first_field_with_error = ''

    #import json
    #print json.dumps(form.data, indent=3)

    # the code below will output only submitted values which were truthy
    # useful for debugging the form itself without getting lost in the
    # 57-field object that gets created
    #print
    #print
    #for field in form:
    #    if field.data and field.data != 'None':
    #        print field.short_name, '::', field.data, ',', type(field.data)
    #print

    if request.method == 'POST':
        if form.validate():
            suggestion = SuggestionFormXWalk.form2obj(form)
            if not existing_suggestion:
                suggestion.suggested_on = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                suggestion.set_application_status('pending')
            else:
                suggestion.suggested_on = existing_suggestion.suggested_on
                suggestion.data['id'] = existing_suggestion.data['id']

            # the code below can be used to quickly debug objects which
            # fail to serialise as JSON - there should be none of those
            # in the suggestion!
            '''
            import json
            for thing in suggestion.data:
                try:
                    if thing == 'bibjson':
                        bibjson = suggestion.bibjson().bibjson
                        for thing2 in bibjson:
                            try:
                                print json.dumps(bibjson[thing2])
                            except TypeError as e:
                                print 'This is it:',thing2
                                print e
                                print
                                print json.dumps(bibjson[thing2])
                except TypeError as e:
                    print 'This is it:',thing
                    print e
                    print
            '''

            # the code below produces a dump of the object returned by
            # the crosswalk
            '''
            import json
            print
            print
            print 'Now all the data!'

            print json.dumps(suggestion.data, indent=3)
            '''

            suggestion.save()
            if existing_suggestion:
                flash('Application updated.', 'success')

            return redirect(redirect_url_on_success)
        else:
            for field in form:  # in order of definition of fields, so the order of rendering should be (manually) kept the same as the order of definition for this to work
                if field.errors:
                    first_field_with_error = field.short_name
                    break
    return render_template(
            template_name,
            form=form,
            first_field_with_error=first_field_with_error,
            q_numbers=xrange(1, 10000).__iter__(),  # a generator for the purpose of displaying numbered questions
            other_val=other_val,
            digital_archiving_policy_specific_library_value=digital_archiving_policy_specific_library_value,
            edit_suggestion_page=True,
            **kwargs
    )

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
        if getattr(form, 'application_status', None):
            suggestion.set_application_status(form.application_status.data)

        return suggestion


    @staticmethod
    def obj2form(obj):
        forminfo = {}
        bibjson = obj.bibjson()

        forminfo['title'] = bibjson.title
        forminfo['url'] = bibjson.get_single_url(urltype='homepage')
        forminfo['alternative_title'] = bibjson.alternative_title
        forminfo['pissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.P_ISSN))
        forminfo['eissn'] = listpop(bibjson.get_identifiers(idtype=bibjson.E_ISSN))
        forminfo['publisher'] = bibjson.publisher
        forminfo['society_institution'] = bibjson.institution
        forminfo['platform'] = bibjson.provider
        forminfo['contact_name'] = listpop(obj.contacts()).get('name')
        forminfo['contact_email'] = listpop(obj.contacts()).get('email')
        forminfo['confirm_contact_email'] = forminfo['contact_email']
        forminfo['country'] = bibjson.country

        apc = bibjson.apc
        if apc:
            forminfo['processing_charges'] = forms.reverse_interpret_special(True)
            forminfo['processing_charges_currency'] = apc.get('currency')
            forminfo['processing_charges_amount'] = apc.get('average_price')
        else:
            forminfo['processing_charges'] = forms.reverse_interpret_special(False)
        
        submission_charges = bibjson.submission_charges
        if submission_charges:
            forminfo['submission_charges'] = forms.reverse_interpret_special(True)
            forminfo['submission_charges_currency'] = submission_charges.get('currency')
            forminfo['submission_charges_amount'] = submission_charges.get('average_price')
        else:
            forminfo['submission_charges'] = forms.reverse_interpret_special(False)

        articles_last_year = obj.articles_last_year
        if articles_last_year:
            forminfo['articles_last_year'] = articles_last_year.get('count')
            forminfo['articles_last_year_url'] = articles_last_year.get('url')

        forminfo['waiver_policy_url'] = bibjson.get_single_url(urltype='waiver_policy')
        forminfo['waiver_policy'] = forminfo['waiver_policy_url'] == ''

        # checkboxes
        archiving_policies = forms.reverse_interpret_special(bibjson.archiving_policy.get('policy', []), field='digital_archiving_policy')
        archiving_policies, forminfo['digital_archiving_policy_library'] = \
            forms.reverse_interpret_other(archiving_policies, forms.digital_archiving_policy_choices_list, other_value=forms.digital_archiving_policy_specific_library_value)
        archiving_policies, forminfo['digital_archiving_policy_other'] = \
            forms.reverse_interpret_other(archiving_policies, forms.digital_archiving_policy_choices_list)

        forminfo['digital_archiving_policy'] = archiving_policies
        forminfo['digital_archiving_policy_url'] = bibjson.archiving_policy.get('url')

        forminfo['crawl_permission'] = forms.reverse_interpret_special(bibjson.allows_fulltext_indexing)

        # checkboxes
        article_ids = forms.reverse_interpret_special(bibjson.persistent_identifier_scheme)
        article_ids, forminfo['article_identifiers_other'] = \
            forms.reverse_interpret_other(article_ids, forms.article_identifiers_choices_list)

        forminfo['article_identifiers'] = article_ids

        forminfo['metadata_provision'] = forms.reverse_interpret_special(obj.article_metadata)


        forminfo['download_statistics'] = forms.reverse_interpret_special(bibjson.article_statistics.get('statistics'))
        forminfo['download_statistics_url'] = bibjson.article_statistics.get('url')

        forminfo['first_fulltext_oa_year'] = bibjson.oa_start.get('year')

        # checkboxes
        forminfo['fulltext_format'], forminfo['fulltext_format_other'] = \
            forms.reverse_interpret_other(bibjson.format, forms.fulltext_format_choices_list)

        forminfo['keywords'] = bibjson.keywords

        forminfo['languages'] = bibjson.language

        forminfo['editorial_board_url'] = bibjson.get_single_url('editorial_board')

        forminfo['review_process'] = bibjson.editorial_review.get('process')
        forminfo['review_process_url'] = bibjson.editorial_review.get('url')

        forminfo['aims_scope_url'] = bibjson.get_single_url('aims_scope')
        forminfo['instructions_authors_url'] = bibjson.get_single_url('author_instructions')

        forminfo['plagiarism_screening'] = forms.reverse_interpret_special(bibjson.plagiarism_detection.get('detection'))
        forminfo['plagiarism_screening_url'] = bibjson.plagiarism_detection.get('url')

        forminfo['publication_time'] = bibjson.publication_time

        forminfo['oa_statement_url'] = bibjson.get_single_url('oa_statement')

        license = bibjson.get_license()
        license = license if license else {}  # reinterpret the None val
        forminfo['license'], forminfo['license_other'] = forms.reverse_interpret_other(license.get('type'), forms.license_choices_list)

        if forminfo['license_other']:
            forminfo['license_checkbox'] = []
            if license.get('BY'): forminfo['license_checkbox'].append('by')
            if license.get('SA'): forminfo['license_checkbox'].append('sa')
            if license.get('NC'): forminfo['license_checkbox'].append('nc')
            if license.get('ND'): forminfo['license_checkbox'].append('nd')

        forminfo['license_url'] = license.get('url')
        forminfo['open_access'] = forms.reverse_interpret_special(license.get('open_access'))
        forminfo['license_embedded'] = forms.reverse_interpret_special(license.get('embedded'))
        forminfo['license_embedded_url'] = license.get('embedded_example_url')

        # checkboxes
        forminfo['deposit_policy'], forminfo['deposit_policy_other'] = \
            forms.reverse_interpret_other(forms.reverse_interpret_special(bibjson.deposit_policy), forms.deposit_policy_choices_list)

        forminfo['copyright'], forminfo['copyright_other'] = \
            forms.reverse_interpret_other(
                forms.reverse_interpret_special(bibjson.author_copyright.get('copyright')),
                forms.ternary_choices_list
            )
        forminfo['copyright_url'] = bibjson.author_copyright.get('url')

        forminfo['publishing_rights'], forminfo['publishing_rights_other'] = \
            forms.reverse_interpret_other(
                forms.reverse_interpret_special(bibjson.author_publishing_rights.get('publishing_rights')),
                forms.ternary_choices_list
            )
        forminfo['publishing_rights_url'] = bibjson.author_publishing_rights.get('url')

        forminfo['suggester_name'] = obj.suggester.get('name')
        forminfo['suggester_email'] = obj.suggester.get('email')
        forminfo['suggester_email_confirm'] = forminfo['suggester_email']

        forminfo['application_status'] = obj.application_status

        return forminfo


def listpop(l):
    return l[0] if l else ''