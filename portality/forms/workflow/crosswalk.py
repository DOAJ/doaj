from portality.forms.workflow.triage.forms import TriageSubmission
from portality.models import WorkflowControl, Note, Application
from portality.datasets import licenses as LICENSES
from portality.models.workflow import TriageField


class WorkflowControl2TriageForm(object):

    MAP = {
        "ethics_not_excluded": TriageSubmission.struct.ethics.not_excluded,
        "ethics_no_nonstandard_metrics": TriageSubmission.struct.ethics.no_nonstandard_metrics,
        "ethics_no_fake_impact": TriageSubmission.struct.ethics.no_fake_impact,
        "ethics_no_false_doaj_claim": TriageSubmission.struct.ethics.no_false_doaj_claim,
        "ethics_no_suspicious_ties": TriageSubmission.struct.ethics.no_suspicious_ties,
        "ethics_submission_to_publication_time": TriageSubmission.struct.ethics.publication_time,
        "database_withdrawn": TriageSubmission.struct.database.withdrawn,
        "database_embargo": TriageSubmission.struct.database.embargo,
        "database_not_listed": TriageSubmission.struct.database.not_listed,
        "database_not_duplicate": TriageSubmission.struct.database.not_duplicate,
        "issn_at_least_one": TriageSubmission.struct.issn.at_least_one,
        "issn_country_match": TriageSubmission.struct.issn.country_match,
        "issn_title_match": TriageSubmission.struct.issn.title_match,
        "issn_continuation": TriageSubmission.struct.issn.continuation,
        "website_working": TriageSubmission.struct.website.working,
        "website_issn": TriageSubmission.struct.website.issn,
        "website_url": TriageSubmission.struct.website.url,
        "website_license_policy": TriageSubmission.struct.website.license_policy,
        "website_copyright": TriageSubmission.struct.website.copyright,
        "content_no_login": TriageSubmission.struct.content.no_login,
        "content_no_embargo": TriageSubmission.struct.content.no_embargo,
        "content_publish_enough": TriageSubmission.struct.content.publish_enough,
        "content_unique_link": TriageSubmission.struct.content.unique_link,
        "content_format": TriageSubmission.struct.content.format,
        "content_new_journal": TriageSubmission.struct.content.new_journal,
        "admin_metadata_review": TriageSubmission.struct.metadata_review.metadata_review,
        "admin_special_exception": TriageSubmission.struct.special_exception.special_exception
    }

    def structure_map(self, triage_field_name: TriageField):
        return self.MAP.get(triage_field_name)

    def transform(self, wfc:WorkflowControl, application:Application) -> TriageSubmission:
        triage = wfc.triage
        bj = application.bibjson()

        form = TriageSubmission()
        f = TriageSubmission.struct

        def compliance_field_radio(triage_field, reference):
            if triage_field is None:
                return

            ans = triage_field.answer
            if ans is None:
                return

            form.set(reference.answer, ans)

        def compliance_field_note(triage_field, reference):
            if triage_field is None:
                return
            note = triage_field.note
            if note is None:
                return

            form.set(reference.note, note.note)

        def bool_2_y_n(reference, value):
            if value is None:
                return
            s = "y" if value else "n"
            form.set(reference, s)

        def list_2_str(reference, value, separator=", "):
            if value is None:
                return
            s = separator.join(value)
            form.set(reference, s)

        # Record ID
        form.set(f.id, wfc.id)

        ###################
        ## Ethics fields

        # Not excluded
        compliance_field_radio(triage.ethics_not_excluded, f.ethics.not_excluded)
        compliance_field_note(triage.ethics_not_excluded, f.ethics.not_excluded)

        # No Nonstandard Metrics
        compliance_field_radio(triage.ethics_no_nonstandard_metrics, f.ethics.no_nonstandard_metrics)
        compliance_field_note(triage.ethics_no_nonstandard_metrics, f.ethics.no_nonstandard_metrics)

        # No Fake Impact
        compliance_field_radio(triage.ethics_no_fake_impact, f.ethics.no_fake_impact)
        compliance_field_note(triage.ethics_no_fake_impact, f.ethics.no_fake_impact)

        # No False DOAJ claim
        compliance_field_radio(triage.ethics_no_false_doaj_claim, f.ethics.no_false_doaj_claim)
        compliance_field_note(triage.ethics_no_false_doaj_claim, f.ethics.no_false_doaj_claim)

        # No suspicious ties
        compliance_field_radio(triage.ethics_no_suspicious_ties, f.ethics.no_suspicious_ties)
        compliance_field_note(triage.ethics_no_suspicious_ties, f.ethics.no_suspicious_ties)

        # publication time
        compliance_field_radio(triage.ethics_submission_to_publication_time, f.ethics.publication_time)
        compliance_field_note(triage.ethics_submission_to_publication_time, f.ethics.publication_time)

        ############
        ## Database fields

        # Withdrawn
        compliance_field_radio(triage.database_withdrawn, f.database.withdrawn)
        compliance_field_note(triage.database_withdrawn, f.database.withdrawn)
        form.set(f.database.withdrawn.exceptions_group.exceptions, triage.database_withdrawn.special_exceptions)
        # form.set(f.database.withdrawn.exceptions_group.note, triage.database_withdrawn.exceptions_note)


        # Withdrawn: Ignore Embargo
        #compliance_field_radio(triage.database_withdrawn_exception_ignore_embargo, f.database.withdrawn_exception_ignore_embargo)
        #compliance_field_note(triage.database_withdrawn_exception_ignore_embargo, f.database.withdrawn_exception_ignore_embargo)

        # Withdrawn: Website Unavailable
        #compliance_field_radio(triage.database_withdrawn_exception_website_unavailable, f.database.withdrawn_exception_website_unavailable)
        #compliance_field_note(triage.database_withdrawn_exception_website_unavailable, f.database.withdrawn_exception_website_unavailable)

        # Withdrawn: Content
        #compliance_field_radio(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)
        #compliance_field_note(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)

        # Embargo
        compliance_field_radio(triage.database_embargo, f.database.embargo)
        compliance_field_note(triage.database_embargo, f.database.embargo)
        form.set(f.database.embargo.exceptions, triage.database_embargo.special_exceptions)

        # Embargo: ISSN
        # compliance_field_radio(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)
        # compliance_field_note(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)
        #
        # # Embargo: Maned
        # compliance_field_radio(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)
        # compliance_field_note(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)
        #
        # # Embargo: Website
        # compliance_field_radio(triage.database_embargo_exception_website, f.database.embargo_exception_website)
        # compliance_field_note(triage.database_embargo_exception_website, f.database.embargo_exception_website)
        #
        # # Embargo: Content
        # compliance_field_radio(triage.database_embargo_exception_content, f.database.embargo_exception_content)
        # compliance_field_note(triage.database_embargo_exception_content, f.database.embargo_exception_content)

        # Not Listed
        compliance_field_radio(triage.database_not_listed, f.database.not_listed)
        compliance_field_note(triage.database_not_listed, f.database.not_listed)

        # Not Duplicate
        compliance_field_radio(triage.database_not_duplicate, f.database.not_duplicate)
        compliance_field_note(triage.database_not_duplicate, f.database.not_duplicate)

        ############
        ## ISSN Fields

        # At least one registered
        compliance_field_radio(triage.issn_at_least_one, f.issn.at_least_one)
        compliance_field_note(triage.issn_at_least_one, f.issn.at_least_one)
        form.set(f.issn.at_least_one.edited_issns.eissn, bj.eissn)
        form.set(f.issn.at_least_one.edited_issns.pissn, bj.pissn)

        # Country match
        compliance_field_radio(triage.issn_country_match, f.issn.country_match)
        compliance_field_note(triage.issn_country_match, f.issn.country_match)

        # Title match
        compliance_field_radio(triage.issn_title_match, f.issn.title_match)
        compliance_field_note(triage.issn_title_match, f.issn.title_match)
        form.set(f.issn.title_match.action_group.title, bj.title)

        # Continuation
        compliance_field_radio(triage.issn_continuation, f.issn.continuation)
        compliance_field_note(triage.issn_continuation, f.issn.continuation)
        list_2_str(f.issn.continuation.action_group.continues, bj.replaces)

        ##########
        ## Website

        # Working
        compliance_field_radio(triage.website_working, f.website.working)
        compliance_field_note(triage.website_working, f.website.working)

        # ISSN
        compliance_field_radio(triage.website_issn, f.website.issn)
        compliance_field_note(triage.website_issn, f.website.issn)

        # URL
        compliance_field_radio(triage.website_url, f.website.url)
        compliance_field_note(triage.website_url, f.website.url)

        # License Policy
        compliance_field_radio(triage.website_license_policy, f.website.license_policy)
        compliance_field_note(triage.website_license_policy, f.website.license_policy)

        ltypes = []
        las = []
        for l in bj.licenses:
            ltypes.append(l.get("type"))
            if l.get("type") == "Publisher's own license":
                if l.get("BY"): las.append("BY")
                if l.get("SA"): las.append("SA")
                if l.get("NC"): las.append("NC")
                if l.get("ND"): las.append("ND")

        form.set(f.website.license_policy.license, ltypes)
        form.set(f.website.license_policy.license_attribute, las)
        form.set(f.website.license_policy.license_url, bj.license_terms_url)

        # Copyright
        compliance_field_radio(triage.website_copyright, f.website.copyright)
        compliance_field_note(triage.website_copyright, f.website.copyright)
        bool_2_y_n(f.website.copyright.copyright_author_retains, bj.author_retains_copyright)
        form.set(f.website.copyright.copyright_url, bj.copyright_url)

        #########
        ## Content

        # No Login
        compliance_field_radio(triage.content_no_login, f.content.no_login)
        compliance_field_note(triage.content_no_login, f.content.no_login)

        # No Embargo
        compliance_field_radio(triage.content_no_embargo, f.content.no_embargo)
        compliance_field_note(triage.content_no_embargo, f.content.no_embargo)

        # Publish Enough
        compliance_field_radio(triage.content_publish_enough, f.content.publish_enough)
        compliance_field_note(triage.content_publish_enough, f.content.publish_enough)

        # Unique Link
        compliance_field_radio(triage.content_unique_link, f.content.unique_link)
        compliance_field_note(triage.content_unique_link, f.content.unique_link)

        # Format
        compliance_field_radio(triage.content_format, f.content.format)
        compliance_field_note(triage.content_format, f.content.format)

        # New Journal
        compliance_field_radio(triage.content_new_journal, f.content.new_journal)
        compliance_field_note(triage.content_new_journal, f.content.new_journal)
        form.set(f.content.new_journal.exceptions, triage.content_new_journal.special_exceptions)

        ##############
        ## Admin

        # Metadata Review
        compliance_field_radio(triage.admin_metadata_review, f.metadata_review.metadata_review)
        compliance_field_note(triage.admin_metadata_review, f.metadata_review.metadata_review)

        # Special Exception
        compliance_field_radio(triage.admin_special_exception, f.special_exception.special_exception)
        compliance_field_note(triage.admin_special_exception, f.special_exception.special_exception)
        form.set(f.special_exception.special_exception.special_exceptions, triage.admin_special_exception.special_exceptions)
        form.set(f.special_exception.special_exception.special_exception_other, triage.admin_special_exception.special_exception_other)

        return form

class TriageForm2WorkflowControl(object):
    def transform(self, form:TriageSubmission, account) -> tuple[WorkflowControl, Application]:
        f = TriageSubmission.struct
        wfc = WorkflowControl()
        triage = wfc.triage
        application = Application()
        bj = application.bibjson()

        def compliance_field_radio(complyable, reference):
            val = form.get(reference.answer)
            if val is not None:
                complyable.answer = val

        def compliance_field_note(notable, reference):
            nval = form.get(reference.note)
            if nval is not None:
                notable.note = Note(
                    note = nval,
                    author_id = account.id,
                    resource_type = WorkflowControl.__type__,
                    resource_id = wfc.id
                )

        def str_2_list(form_field, separator=","):
            value = form.get(form_field)
            if not value:
                return None
            return [v.strip() for v in value.split(separator) if v.strip() != ""]

        # Record ID
        wfc.set_id(f.id)

        ###################
        ## Ethics fields

        # Not excluded
        compliance_field_radio(triage.ethics_not_excluded, f.ethics.not_excluded)
        compliance_field_note(triage.ethics_not_excluded, f.ethics.not_excluded)

        # No Nonstandard metrics
        compliance_field_radio(triage.ethics_no_nonstandard_metrics, f.ethics.no_nonstandard_metrics)
        compliance_field_note(triage.ethics_no_nonstandard_metrics, f.ethics.no_nonstandard_metrics)

        # No Fake Impact
        compliance_field_radio(triage.ethics_no_fake_impact, f.ethics.no_fake_impact)
        compliance_field_note(triage.ethics_no_fake_impact, f.ethics.no_fake_impact)

        # No false DOAJ claim
        compliance_field_radio(triage.ethics_no_false_doaj_claim, f.ethics.no_false_doaj_claim)
        compliance_field_note(triage.ethics_no_false_doaj_claim, f.ethics.no_false_doaj_claim)

        # No suspicious ties
        compliance_field_radio(triage.ethics_no_suspicious_ties, f.ethics.no_suspicious_ties)
        compliance_field_note(triage.ethics_no_suspicious_ties, f.ethics.no_suspicious_ties)

        # publication time
        compliance_field_radio(triage.ethics_submission_to_publication_time, f.ethics.publication_time)
        compliance_field_note(triage.ethics_submission_to_publication_time, f.ethics.publication_time)

        ############
        ## Database fields

        # Withdrawn
        compliance_field_radio(triage.database_withdrawn, f.database.withdrawn)
        compliance_field_note(triage.database_withdrawn, f.database.withdrawn)
        triage.database_withdrawn.special_exceptions = form.get(f.database.withdrawn.exceptions_group.exceptions)

        # Withdrawn: Ignore Embargo
        # compliance_field_radio(triage.database_withdrawn_exception_ignore_embargo,
        #                        f.database.withdrawn_exception_ignore_embargo)
        # compliance_field_note(triage.database_withdrawn_exception_ignore_embargo,
        #                       f.database.withdrawn_exception_ignore_embargo)
        #
        # # Withdrawn: Website Unavailable
        # compliance_field_radio(triage.database_withdrawn_exception_website_unavailable,
        #                        f.database.withdrawn_exception_website_unavailable)
        # compliance_field_note(triage.database_withdrawn_exception_website_unavailable,
        #                       f.database.withdrawn_exception_website_unavailable)
        #
        # # Withdrawn: Content
        # compliance_field_radio(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)
        # compliance_field_note(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)

        # Embargo
        compliance_field_radio(triage.database_embargo, f.database.embargo)
        compliance_field_note(triage.database_embargo, f.database.embargo)
        triage.database_embargo.special_exceptions = form.get(f.database.embargo.exceptions)

        # Embargo: ISSN
        # compliance_field_radio(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)
        # compliance_field_note(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)
        #
        # # Embargo: Maned
        # compliance_field_radio(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)
        # compliance_field_note(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)
        #
        # # Embargo: Website
        # compliance_field_radio(triage.database_embargo_exception_website, f.database.embargo_exception_website)
        # compliance_field_note(triage.database_embargo_exception_website, f.database.embargo_exception_website)
        #
        # # Embargo: Content
        # compliance_field_radio(triage.database_embargo_exception_content, f.database.embargo_exception_content)
        # compliance_field_note(triage.database_embargo_exception_content, f.database.embargo_exception_content)

        # Not Listed
        compliance_field_radio(triage.database_not_listed, f.database.not_listed)
        compliance_field_note(triage.database_not_listed, f.database.not_listed)

        # Not Duplicate
        compliance_field_radio(triage.database_not_duplicate, f.database.not_duplicate)
        compliance_field_note(triage.database_not_duplicate, f.database.not_duplicate)

        ################
        ## ISSN Fields

        # At least one registered
        compliance_field_radio(triage.issn_at_least_one, f.issn.at_least_one)
        compliance_field_note(triage.issn_at_least_one, f.issn.at_least_one)
        eissn = form.get(f.issn.at_least_one.edited_issns.eissn)
        bj.eissn = eissn
        pissn = form.get(f.issn.at_least_one.edited_issns.pissn)
        bj.pissn = pissn

        # Country match
        compliance_field_radio(triage.issn_country_match, f.issn.country_match)
        compliance_field_note(triage.issn_country_match, f.issn.country_match)

        # Title match
        compliance_field_radio(triage.issn_title_match, f.issn.title_match)
        compliance_field_note(triage.issn_title_match, f.issn.title_match)
        title = form.get(f.issn.title_match.action_group.title)
        bj.title = title

        # Continuation
        compliance_field_radio(triage.issn_continuation, f.issn.continuation)
        compliance_field_note(triage.issn_continuation, f.issn.continuation)
        issn_list = str_2_list(f.issn.continuation.action_group.continues)
        if issn_list:
            bj.replaces = issn_list
        else:
            del bj.replaces

        ##########
        ## Website

        # Working
        compliance_field_radio(triage.website_working, f.website.working)
        compliance_field_note(triage.website_working, f.website.working)

        # ISSN
        compliance_field_radio(triage.website_issn, f.website.issn)
        compliance_field_note(triage.website_issn, f.website.issn)

        # URL
        compliance_field_radio(triage.website_url, f.website.url)
        compliance_field_note(triage.website_url, f.website.url)

        # License Policy
        compliance_field_radio(triage.website_license_policy, f.website.license_policy)
        compliance_field_note(triage.website_license_policy, f.website.license_policy)

        lurl = form.get(f.website.license_policy.license_url)
        if lurl is not None:
            bj.license_terms_url = lurl

        licenses = form.get(f.website.license_policy.license)
        license_attributes = form.get(f.website.license_policy.license_attribute)
        if license_attributes is not None:
            for ltype in licenses:
                by, nc, nd, sa = None, None, None, None
                if ltype in LICENSES:
                    by = LICENSES[ltype]["BY"]
                    nc = LICENSES[ltype]["NC"]
                    nd = LICENSES[ltype]["ND"]
                    sa = LICENSES[ltype]["SA"]
                    lurl = LICENSES[ltype]["url"]
                elif license_attributes is not None and len(license_attributes) > 0:
                    by = True if 'BY' in license_attributes else False
                    nc = True if 'NC' in license_attributes else False
                    nd = True if 'ND' in license_attributes else False
                    sa = True if 'SA' in license_attributes else False
                bj.add_license(ltype, by=by, nc=nc, nd=nd, sa=sa, url=lurl)

        # Copyright
        compliance_field_radio(triage.website_copyright, f.website.copyright)
        compliance_field_note(triage.website_copyright, f.website.copyright)
        car = form.get(f.website.copyright.copyright_author_retains)
        bj.author_retains_copyright = car == "y"
        curl = form.get(f.website.copyright.copyright_url)
        bj.copyright_url = curl

        #########
        ## Content

        # No Login
        compliance_field_radio(triage.content_no_login, f.content.no_login)
        compliance_field_note(triage.content_no_login, f.content.no_login)

        # No Embargo
        compliance_field_radio(triage.content_no_embargo, f.content.no_embargo)
        compliance_field_note(triage.content_no_embargo, f.content.no_embargo)

        # Publish Enough
        compliance_field_radio(triage.content_publish_enough, f.content.publish_enough)
        compliance_field_note(triage.content_publish_enough, f.content.publish_enough)

        # Unique Link
        compliance_field_radio(triage.content_unique_link, f.content.unique_link)
        compliance_field_note(triage.content_unique_link, f.content.unique_link)

        # Format
        compliance_field_radio(triage.content_format, f.content.format)
        compliance_field_note(triage.content_format, f.content.format)

        # New Journal
        compliance_field_radio(triage.content_new_journal, f.content.new_journal)
        compliance_field_note(triage.content_new_journal, f.content.new_journal)
        triage.content_new_journal.special_exceptions = form.get(f.content.new_journal.exceptions)

        ##############
        ## Admin

        # Metadata Review
        compliance_field_radio(triage.admin_metadata_review, f.metadata_review.metadata_review)
        compliance_field_note(triage.admin_metadata_review, f.metadata_review.metadata_review)

        # Special Exception
        compliance_field_radio(triage.admin_special_exception, f.special_exception.special_exception)
        compliance_field_note(triage.admin_special_exception, f.special_exception.special_exception)
        special_exceptions = form.get(f.special_exception.special_exception.special_exceptions)
        special_exceptions_other = form.get(f.special_exception.special_exception.special_exception_other)
        triage.admin_special_exception.special_exceptions = special_exceptions
        triage.admin_special_exception.special_exception_other = special_exceptions_other

        return wfc, application

