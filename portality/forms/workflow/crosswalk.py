from portality.forms.workflow.triage.forms import TriageSubmission
from portality.models import WorkflowControl, Note, Application


class WorkflowControl2TriageForm(object):
    def transform(self, wfc:WorkflowControl, application:Application) -> TriageSubmission:
        triage = wfc.triage

        form = TriageSubmission()
        f = TriageSubmission.struct
        form.set(f.id, wfc.id)

        def ethics_field_bool(val, reference):
            if val is not None:
                form.set(reference, "y" if val else "n")

        def ethics_field_note(notes, reference):
            for id, nobj in notes.items():
                # FIXME: we have a model which can handle multiple notes, and a form which cannot
                # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
                form.set(reference, nobj.note)

        ethics_field_bool(
            triage.ethics_not_excluded.compliant,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded
        )
        ethics_field_note(
            triage.ethics_not_excluded.notes,
            f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note
        )

        ethics_field_bool(
            triage.ethics_no_nonstandard_metrics.compliant,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics
        )
        ethics_field_note(
            triage.ethics_no_nonstandard_metrics.notes,
            f.ethics_criteria.ethics_no_nonstandard_metrics_group.ethics_no_nonstandard_metrics_note
        )

        ethics_field_bool(
            triage.ethics_no_fake_impact.compliant,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact
        )
        ethics_field_note(
            triage.ethics_no_fake_impact.notes,
            f.ethics_criteria.ethics_no_fake_impact_group.ethics_no_fake_impact_note
        )

        ethics_field_bool(
            triage.ethics_no_false_doaj_claim.compliant,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim
        )
        ethics_field_note(
            triage.ethics_no_false_doaj_claim.notes,
            f.ethics_criteria.ethics_no_false_doaj_claim_group.ethics_no_false_doaj_claim_note
        )

        ethics_field_bool(
            triage.ethics_no_suspicious_ties.compliant,
            f.ethics_criteria.ethics_no_suspicious_ties_group.ethics_no_suspicious_ties
        )
        ethics_field_note(
            triage.ethics_no_suspicious_ties.notes,
            f.ethics_criteria.ethics_no_suspicious_ties_group.ethics_no_suspicious_ties_note
        )

        return form

class TriageForm2WorkflowControl(object):
    def transform(self, form:TriageSubmission, account) -> tuple[WorkflowControl, Application]:
        f = TriageSubmission.struct
        wfc = WorkflowControl()
        t = wfc.triage
        application = Application()

        def ethics_field_bool(complyable, reference):
            val = form.get(reference)
            if val is not None:
                complyable.compliant = val == "y"
            return None

        def ethics_field_note(notable, reference):
            nval = form.get(reference)
            if nval is not None:
                notable.add_note(Note(
                    note = nval,
                    author_id = account.id,
                    resource_type = WorkflowControl.__type__,
                    resource_id = wfc.id
                ))

        ethics_field_bool(t.ethics_not_excluded, f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded)
        ethics_field_note(t.ethics_not_excluded, f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note)

        return wfc, application

