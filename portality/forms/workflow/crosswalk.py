from portality.forms.workflow.triage.forms import TriageSubmission
from portality.models import WorkflowControl, Note, Application


class WorkflowControl2TriageForm(object):
    def transform(self, wfc:WorkflowControl, application:Application) -> TriageSubmission:
        # Full form template for us to populate
        # result = {
        #     "id": wfc.id,
        #     "ethics_criteria": {
        #         "ethics_not_excluded_group": {
        #             "ethics_not_excluded": None,
        #             "ethics_not_excluded_note": None
        #         },
        #         "ethics_no_nonstandard_metrics_group": {
        #             "ethics_no_nonstandard_metrics": None,
        #             "ethics_no_nonstandard_metrics_note": None
        #         },
        #         "ethics_no_fake_impact_group":{
        #             "ethics_no_fake_impact": None,
        #             "ethics_no_fake_impact_note": None
        #         },
        #         "ethics_no_false_doaj_claim_group":{
        #             "ethics_no_false_doaj_claim": None,
        #             "ethics_no_false_doaj_claim_note": None
        #         },
        #         "ethics_no_suspicious_ties_group":{
        #             "ethics_no_suspicious_ties": None,
        #             "ethics_no_suspicious_ties_note": None
        #         }
        #     }
        # }

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

        # val = triage.ethics_not_excluded.compliant
        # if val is not None:
        #     form.set(f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded, "y" if val else "n")
        #
        # notes = triage.ethics_not_excluded.notes
        # for id, nobj in notes.items():
        #     # FIXME: we have a model which can handle multiple notes, and a form which cannot
        #     # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
        #     form.set(f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note, nobj.note)
        #


        # def ethics_field(fieldname):
        #     field = getattr(triage, fieldname)
        #     if field.compliant is not None:
        #         result["ethics_criteria"][fieldname + "_group"][fieldname] = "y" if field.compliant else "n"
        #     notes: dict[str, Note] = getattr(field, "notes")
        #     # FIXME: we have a model which can handle multiple notes, and a form which cannot
        #     # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
        #     for id, nobj in notes.items():
        #         result["ethics_criteria"][fieldname + "_group"][fieldname + "_note"] = nobj.note

        # ethics_field("ethics_not_excluded")
        # ethics_field("ethics_no_nonstandard_metrics")
        # ethics_field("ethics_no_fake_impact")
        # ethics_field("ethics_no_false_doaj_claim")
        # ethics_field("ethics_no_suspicious_ties")

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

        # ethics_not_excluded = form.get(f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded)
        # ethics_not_excluded_note = form.get(f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note)

        ethics_field_bool(t.ethics_not_excluded, f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded)
        ethics_field_note(t.ethics_not_excluded, f.ethics_criteria.ethics_not_excluded_group.ethics_not_excluded_note)

        # if ethics_not_excluded is not None:
        #     t.ethics_not_excluded.compliant = ethics_not_excluded == "y"
        #
        # if ethics_not_excluded_note is not None:
        #     t.ethics_not_excluded.add_note(
        #         Note(
        #             note=ethics_not_excluded_note,
        #             author_id=account.id,
        #             resource_type=WorkflowControl.__type__,
        #             resource_id=wfc.id
        #         )
        #     )

        return wfc, application

