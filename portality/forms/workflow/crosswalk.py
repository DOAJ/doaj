from portality.forms.workflow.triage.forms import TriageSubmission
from portality.models import WorkflowControl, Note, Application


class WorkflowControl2TriageForm(object):
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

            # for id, nobj in notes.items():
            #     if nobj is None:    # This shouldn't happen, but in development it certainly can
            #         continue
            #     # FIXME: we have a model which can handle multiple notes, and a form which cannot
            #     # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
            #     form.set(reference, nobj.note)

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

        ############
        ## Database fields

        # Withdrawn
        compliance_field_radio(triage.database_withdrawn, f.database.withdrawn)
        compliance_field_note(triage.database_withdrawn, f.database.withdrawn)

        # Withdrawn: Ignore Embargo
        compliance_field_radio(triage.database_withdrawn_exception_ignore_embargo, f.database.withdrawn_exception_ignore_embargo)
        compliance_field_note(triage.database_withdrawn_exception_ignore_embargo, f.database.withdrawn_exception_ignore_embargo)

        # Withdrawn: Website Unavailable
        compliance_field_radio(triage.database_withdrawn_exception_website_unavailable, f.database.withdrawn_exception_website_unavailable)
        compliance_field_note(triage.database_withdrawn_exception_website_unavailable, f.database.withdrawn_exception_website_unavailable)

        # Withdrawn: Content
        compliance_field_radio(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)
        compliance_field_note(triage.database_withdrawn_exception_content, f.database.withdrawn_exception_content)

        # Embargo
        compliance_field_radio(triage.database_embargo, f.database.embargo)
        compliance_field_note(triage.database_embargo, f.database.embargo)

        # Embargo: ISSN
        compliance_field_radio(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)
        compliance_field_note(triage.database_embargo_exception_issn, f.database.embargo_exception_issn)

        # Embargo: Maned
        compliance_field_radio(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)
        compliance_field_note(triage.database_embargo_exception_maned, f.database.embargo_exception_maned)

        # Embargo: Website
        compliance_field_radio(triage.database_embargo_exception_website, f.database.embargo_exception_website)
        compliance_field_note(triage.database_embargo_exception_website, f.database.embargo_exception_website)

        # Embargo: Content
        compliance_field_radio(triage.database_embargo_exception_content, f.database.embargo_exception_content)
        compliance_field_note(triage.database_embargo_exception_content, f.database.embargo_exception_content)

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
        form.set(f.issn.at_least_one.eissn, bj.eissn)
        form.set(f.issn.at_least_one.pissn, bj.pissn)

        # Title match
        compliance_field_radio(triage.issn_title_match, f.issn.title_match)
        compliance_field_note(triage.issn_title_match, f.issn.title_match)
        form.set(f.issn.title_match.title, bj.title)

        # Continuation
        compliance_field_radio(triage.issn_continuation, f.issn.continuation)
        compliance_field_note(triage.issn_continuation, f.issn.continuation)
        list_2_str(f.issn.continuation.continues, bj.replaces)

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

        ##############
        ## Admin

        # Metadata Review
        compliance_field_radio(triage.admin_metadata_review, f.admin.metadata_review)
        compliance_field_note(triage.admin_metadata_review, f.admin.metadata_review)

        # Special Exception
        compliance_field_radio(triage.admin_special_exception, f.admin.special_exception)
        compliance_field_note(triage.admin_special_exception, f.admin.special_exception)

        return form

class TriageForm2WorkflowControl(object):
    def transform(self, form:TriageSubmission, account) -> tuple[WorkflowControl, Application]:
        f = TriageSubmission.struct
        wfc = WorkflowControl()
        t = wfc.triage
        application = Application()

        def compliance_field_answer(complyable, reference):
            val = form.get(reference)
            if val is not None:
                complyable.answer = val

        def compliance_field_note(notable, reference):
            nval = form.get(reference)
            if nval is not None:
                notable.add_note(Note(
                    note = nval,
                    author_id = account.id,
                    resource_type = WorkflowControl.__type__,
                    resource_id = wfc.id
                ))

        ###################
        ## Ethics fields

        # Not excluded
        compliance_field_answer(
            t.ethics_not_excluded,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded
        )
        compliance_field_note(
            t.ethics_not_excluded,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note
        )

        # No Nonstandard metrics
        compliance_field_answer(
            t.ethics_no_nonstandard_metrics,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics
        )
        compliance_field_note(
            t.ethics_no_nonstandard_metrics,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics_note
        )

        # No Fake Impact
        compliance_field_answer(
            t.ethics_no_fake_impact,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact
        )
        compliance_field_note(
            t.ethics_no_fake_impact,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact_note
        )

        # No false DOAJ claim
        compliance_field_answer(
            t.ethics_no_false_doaj_claim,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim
        )
        compliance_field_note(
            t.ethics_no_false_doaj_claim,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim_note
        )

        # No suspicious ties
        compliance_field_answer(
            t.ethics_no_suspicious_ties,
            f.ethics_criteria.ethics_no_suspicious_ties_group.ethics_no_suspicious_ties
        )

        ################
        ## ISSN Fields

        compliance_field_answer(
            t.issn_at_least_one,
            f.issn.issn_at_least_one_group.issn_at_least_one
        )
        compliance_field_note(
            t.issn_at_least_one,
            f.issn.issn_at_least_one_group.issn_at_least_one_note
        )
        eissn = form.get(f.issn.issn_at_least_one_group.eissn)
        application.bibjson().eissn = eissn
        pissn = form.get(f.issn.issn_at_least_one_group.pissn)
        application.bibjson().pissn = pissn

        return wfc, application

