from portality.models import WorkflowControl, Note


class WorkflowControl2TriageForm(object):
    def transform(self, wfc:WorkflowControl):
        # Full form template for us to populate
        result = {
            "id": wfc.id,
            "ethics_criteria": {
                "ethics_not_excluded_group": {
                    "ethics_not_excluded": None,
                    "ethics_not_excluded_note": None
                },
                "ethics_no_nonstandard_metrics_group": {
                    "ethics_no_nonstandard_metrics": None,
                    "ethics_no_nonstandard_metrics_note": None
                },
                "ethics_no_fake_impact_group":{
                    "ethics_no_fake_impact": None,
                    "ethics_no_fake_impact_note": None
                },
                "ethics_no_false_doaj_claim_group":{
                    "ethics_no_false_doaj_claim": None,
                    "ethics_no_false_doaj_claim_note": None
                },
                "ethics_no_suspicious_ties_group":{
                    "ethics_no_suspicious_ties": None,
                    "ethics_no_suspicious_ties_note": None
                }
            }
        }

        triage = wfc.triage

        def ethics_field(fieldname):
            field = getattr(triage, fieldname)
            if field.compliant is not None:
                result["ethics_criteria"][fieldname + "_group"][fieldname] = "y" if field.compliant else "n"
            notes: dict[str, Note] = getattr(field, "notes")
            # FIXME: we have a model which can handle multiple notes, and a form which cannot
            # FIXME: how do we handle the updating of referenced notes (do we need to remember their ids)?
            for id, nobj in notes.items():
                result["ethics_criteria"][fieldname + "_group"][fieldname + "_note"] = nobj.note

        ethics_field("ethics_not_excluded")
        ethics_field("ethics_no_nonstandard_metrics")
        ethics_field("ethics_no_fake_impact")
        ethics_field("ethics_no_false_doaj_claim")
        ethics_field("ethics_no_suspicious_ties")

        return result