from formulaic.core import Structure, SINGLE, OPTIONAL
from portality.forms.workflow.core import WorkflowFieldsetCapability
from portality.forms.workflow.triage.fields import EthicsNotExcluded, EthicsNoNonStandardMetrics, \
    EthicsNotExcludedGroup, EthicsNoNonStandardMetricsGroup, EthicsNoFakeImpactGroup, EthicsNoFalseDOAJClaimGroup, \
    EthicsNoSuspiciousTiesGroup


class EthicsCriteria(Structure):
    class EthicsCriteriaCapability(WorkflowFieldsetCapability):
        label = "Ethics criteria"
        order = [
            "ethics_not_excluded_group",
            "ethics_no_nonstandard_metrics_group",
            "ethics_no_fake_impact_group",
            "ethics_no_false_doaj_claim_group",
            "ethics_no_suspicious_ties_group",
        ]

    name_ = "ethics_criteria"
    capabilities_ = (EthicsCriteriaCapability(),)

    ethics_not_excluded_group = EthicsNotExcludedGroup(OPTIONAL, SINGLE)
    ethics_no_nonstandard_metrics_group = EthicsNoNonStandardMetricsGroup(OPTIONAL, SINGLE)
    ethics_no_fake_impact_group = EthicsNoFakeImpactGroup(OPTIONAL, SINGLE)
    ethics_no_false_doaj_claim_group = EthicsNoFalseDOAJClaimGroup(OPTIONAL, SINGLE)
    ethics_no_suspicious_ties_group = EthicsNoSuspiciousTiesGroup(OPTIONAL, SINGLE)