from formulaic.core import Structure, SINGLE, OPTIONAL
from formulaic.serialise.form.core import FieldsetCapability
from portality.forms.workflow.core import GenericFieldset
from portality.forms.workflow.triage.fields import EthicsNotExcludedGroup, EthicsNoNonStandardMetricsGroup, \
    EthicsNoFakeImpactGroup, EthicsNoFalseDOAJClaimGroup, \
    EthicsNoSuspiciousTiesGroup, ISSNAtLeastOne, ISSNAtLeastOneGroup


class EthicsCriteria(Structure):
    class EthicsCriteriaCapability(FieldsetCapability):
        label = "Ethics criteria"
        order = [
            "ethics_not_excluded_group",
            "ethics_no_nonstandard_metrics_group",
            "ethics_no_fake_impact_group",
            "ethics_no_false_doaj_claim_group",
            "ethics_no_suspicious_ties_group",
        ]

        render_class = GenericFieldset

    name_ = "ethics_criteria"
    capabilities_ = (EthicsCriteriaCapability(),)

    ethics_not_excluded_group = EthicsNotExcludedGroup(OPTIONAL, SINGLE)
    ethics_no_nonstandard_metrics_group = EthicsNoNonStandardMetricsGroup(OPTIONAL, SINGLE)
    ethics_no_fake_impact_group = EthicsNoFakeImpactGroup(OPTIONAL, SINGLE)
    ethics_no_false_doaj_claim_group = EthicsNoFalseDOAJClaimGroup(OPTIONAL, SINGLE)
    ethics_no_suspicious_ties_group = EthicsNoSuspiciousTiesGroup(OPTIONAL, SINGLE)


class ISSN(Structure):
    class ISSNCapability(FieldsetCapability):
        label = "ISSN"
        order = [
            "issn_at_least_one_group"
        ]
        render_class = GenericFieldset

    name_ = "issn"
    capabilities_ = (ISSNCapability(),)

    issn_at_least_one_group = ISSNAtLeastOneGroup(OPTIONAL, SINGLE)