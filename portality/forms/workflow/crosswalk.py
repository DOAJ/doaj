from portality.forms.workflow.triage.forms import TriageSubmission
from portality.models import WorkflowControl, Note, Application


class WorkflowControl2TriageForm(object):
    def transform(self, wfc:WorkflowControl, application:Application) -> TriageSubmission:
        triage = wfc.triage
        bj = application.bibjson()

        form = TriageSubmission()
        f = TriageSubmission.struct
        form.set(f.id, wfc.id)

        def compliance_field_radio(val, reference):
            if val is not None:
                form.set(reference, val)

        def compliance_field_note(notes, reference):
            for id, nobj in notes.items():
                # FIXME: we have a model which can handle multiple notes, and a form which cannot
                # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
                form.set(reference, nobj.note)

        ###################
        ## Ethics fields

        # Not excluded
        compliance_field_radio(
            triage.ethics_not_excluded.answer,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded
        )
        compliance_field_note(
            triage.ethics_not_excluded.notes,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note
        )

        # No Nonstandard Metrics
        compliance_field_radio(
            triage.ethics_no_nonstandard_metrics.answer,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics
        )
        compliance_field_note(
            triage.ethics_no_nonstandard_metrics.notes,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics_note
        )

        # No Fake Impact
        compliance_field_radio(
            triage.ethics_no_fake_impact.answer,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact
        )
        compliance_field_note(
            triage.ethics_no_fake_impact.notes,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact_note
        )

        # No False DOAJ claim
        compliance_field_radio(
            triage.ethics_no_false_doaj_claim.answer,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim
        )
        compliance_field_note(
            triage.ethics_no_false_doaj_claim.notes,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim_note
        )

        # No suspicious ties
        compliance_field_radio(
            triage.ethics_no_suspicious_ties.answer,
            f.ethics_criteria.ethics_no_suspicious_ties_group.ethics_no_suspicious_ties
        )
        compliance_field_note(
            triage.ethics_no_suspicious_ties.notes,
            f.ethics_criteria.ethics_no_suspicious_ties_group.ethics_no_suspicious_ties_note
        )

        ############
        ## ISSN Fields

        # At least one registered
        compliance_field_radio(
            triage.issn_at_least_one.answer,
            f.issn.issn_at_least_one_group.issn_at_least_one
        )
        compliance_field_note(
            triage.issn_at_least_one.notes,
            f.issn.issn_at_least_one_group.issn_at_least_one_note
        )
        form.set(f.issn.issn_at_least_one_group.eissn, bj.eissn)
        form.set(f.issn.issn_at_least_one_group.pissn, bj.pissn)

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

