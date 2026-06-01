from formulaic.core import Structure, OPTIONAL, SINGLE
from portality.forms.workflow.core import WorkflowFormCapability
from portality.forms.workflow.triage.fieldsets import EthicsCriteria


class TriageForm(Structure):
    class TriageFormCapability(WorkflowFormCapability):
        order = [
            "ethics_criteria",
        ]

    name_ = "triage"
    capabilities_ = (TriageFormCapability,)

    ethics_criteria = EthicsCriteria(OPTIONAL, SINGLE)