from formulaic.core import Structure, SINGLE, OPTIONAL
from portality.forms.workflow.core import WorkflowFieldsetCapability
from portality.forms.workflow.triage.fields import EthicsNotExcluded


class EthicsCriteria(Structure):
    class EthicsCriteriaCapability(WorkflowFieldsetCapability):
        label = "Ethics criteria"
        order = [

        ]

    name_ = "ethics_criteria"
    capabilities_ = (EthicsCriteriaCapability,)

    ethics_not_excluded = EthicsNotExcluded(OPTIONAL, SINGLE)