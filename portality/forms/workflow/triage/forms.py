from formulaic.core import Structure, OPTIONAL, SINGLE
from portality.forms.workflow.core import WorkflowFormCapability, JinjaFormRenderer
from portality.forms.workflow.triage.fieldsets import EthicsCriteria
from portality.ui import templates

class TriageFormRenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_FORM_TRIAGE

class TriageForm(Structure):
    class TriageFormCapability(WorkflowFormCapability):
        order = [
            "ethics_criteria",
        ]
        render_class = TriageFormRenderer

    name_ = "triage"
    capabilities_ = (TriageFormCapability(),)

    ethics_criteria = EthicsCriteria(OPTIONAL, SINGLE)
