from formulaic.core import Structure, OPTIONAL, SINGLE
from formulaic.objects import FormulaicObject
from formulaic.serialise.form.core import FormCapability
from portality.forms.workflow.core import JinjaFormRenderer
from portality.forms.workflow.triage.fields import RecordID
from portality.forms.workflow.triage.fieldsets import EthicsCriteria, ISSN
from portality.ui import templates

class TriageFormRenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_FORM

class TriageForm(Structure):
    class TriageFormCapability(FormCapability):
        order = [
            "id",
            "issn",
            "ethics_criteria",
        ]
        render_class = TriageFormRenderer

    name_ = "triage"
    capabilities_ = (TriageFormCapability(),)

    id = RecordID(OPTIONAL, SINGLE)
    ethics_criteria = EthicsCriteria(OPTIONAL, SINGLE)
    issn = ISSN(OPTIONAL, SINGLE)

class TriageSubmission(FormulaicObject):
    struct = TriageForm()
    apply_structure_on_init = False
    check_required_on_init = False