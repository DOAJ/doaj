from formulaic.serialise.form.render import InvertedLabelInputControlHTML
from portality.core import app

from formulaic.coerce.coerce import Boolean, Unicode
from formulaic.core import Field, FieldCapability, Structure, SINGLE, OPTIONAL
from formulaic.serialise.form.controls import Radio, Textarea
from formulaic.serialise.form.core import FormFieldCapability, CompoundFieldCapability
from portality.forms.workflow.core import WorkflowFormFieldCapability, JinjaFieldRenderer
from portality.ui import templates

T = app.cms.workflow.triage.fields

class NoteCapability(FormFieldCapability):
    label = "Note"
    placeholder = "Add a note ..."
    repeatable_label = "Notes"
    repeatable_minimum = 1
    repeatable_initial = 1

    control_class = Textarea

class WorkflowFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_FORM_FIELD_TRIAGE

#####################################################
## Ethics: Not Excluded

class EthicsNotExcluded(Field):
    class EthicsNotExcludedCapability(WorkflowFormFieldCapability):
        label = "Compliance"

        options = [
            {"value": "y", "label": T.ethics_not_excluded.compliant},
            {"value": "n", "label": T.ethics_not_excluded.non_compliant}
        ]
        control_class = Radio
        control_render_class = InvertedLabelInputControlHTML
        render_class = WorkflowFieldRenderer

        check = T.ethics_not_excluded.check
        instructions = T.ethics_not_excluded.instructions
        resources = [
            {
                "label": T.ethics_not_excluded.resource_label,
                "url": T.ethics_not_excluded.resource_url
            }
        ]

    name = "ethics_not_excluded"
    coerce = [Boolean()]
    capabilities = (EthicsNotExcludedCapability(),)


class EthicsNotExcludedNote(Field):
    name = "ethics_not_excluded_note"
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)


class EthicsNotExcludedGroup(Structure):
    class EthicsNotExcludedGroupCapability(CompoundFieldCapability):
        label = T.ethics_not_excluded.label

        order = [
            "ethics_not_excluded",
            "ethics_not_excluded_note",
        ]

    name_ = "ethics_not_excluded_group"
    capabilities_ = (EthicsNotExcludedGroupCapability(),)

    ethics_not_excluded = EthicsNotExcluded(OPTIONAL, SINGLE)
    ethics_not_excluded_note = EthicsNotExcludedNote(OPTIONAL, SINGLE)

##########################################################


##########################################################
## Ethics: Non Standard Metrics

class EthicsNoNonStandardMetrics(Field):
    class EthicsNoNonStandardMetricsCapability(WorkflowFormFieldCapability):
        label = "Compliance"

        options = [
            {"value": "y",
             "label": T.ethics_no_nonstandard_metrics.compliant},
            {"value": "n",
             "label": T.ethics_no_nonstandard_metrics.non_compliant}
        ]
        control_class = Radio
        control_render_class = InvertedLabelInputControlHTML
        render_class = WorkflowFieldRenderer

        check = T.ethics_no_nonstandard_metrics.check
        instructions = T.ethics_no_nonstandard_metrics.instructions
        resources = [
            {
                "label": T.ethics_no_nonstandard_metrics.resource_label,
                "url": T.ethics_no_nonstandard_metrics.resource_url
            }
        ]

    name = "ethics_no_nonstandard_metrics"
    coerce = [Boolean()]
    capabilities = (EthicsNoNonStandardMetricsCapability(),)


class EthicsNoNonStandardMetricsNote(Field):
    name = "ethics_no_nonstandard_metrics_note"
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)


class EthicsNoNonStandardMetricsGroup(Structure):
    class EthicsNoNonStandardMetricsGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_nonstandard_metrics.label

        order = [
            "ethics_no_nonstandard_metrics",
            "ethics_no_nonstandard_metrics_note",
        ]

    name_ = "ethics_no_nonstandard_metrics_group"
    capabilities_ = (EthicsNoNonStandardMetricsGroupCapability(),)

    ethics_no_nonstandard_metrics = EthicsNoNonStandardMetrics(OPTIONAL, SINGLE)
    ethics_no_nonstandard_metrics_note = EthicsNoNonStandardMetricsNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No Fake Impact

class EthicsNoFakeImpact(Field):
    class EthicsNoFakeImpactCapability(WorkflowFormFieldCapability):
        label = "Compliance"

        options = [
            {"value": "y",
             "label": T.ethics_no_fake_impact.compliant},
            {"value": "n",
             "label": T.ethics_no_fake_impact.non_compliant}
        ]
        control_class = Radio
        control_render_class = InvertedLabelInputControlHTML
        render_class = WorkflowFieldRenderer

        check = T.ethics_no_fake_impact.check
        instructions = T.ethics_no_fake_impact.instructions
        resources = [
            {
                "label": T.ethics_no_fake_impact.resource_label,
                "url": T.ethics_no_fake_impact.resource_url
            }
        ]

    name = "ethics_no_fake_impact"
    coerce = [Boolean()]
    capabilities = (EthicsNoFakeImpactCapability(),)


class EthicsNoFakeImpactNote(Field):
    name = "ethics_no_fake_impact_note"
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)


class EthicsNoFakeImpactGroup(Structure):
    class EthicsNoFakeImpactGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_fake_impact.label

        order = [
            "ethics_no_fake_impact",
            "ethics_no_fake_impact_note",
        ]

    name_ = "ethics_no_fake_impact_group"
    capabilities_ = (EthicsNoFakeImpactGroupCapability(),)

    ethics_no_fake_impact = EthicsNoNonStandardMetrics(OPTIONAL, SINGLE)
    ethics_no_fake_impact_note = EthicsNoNonStandardMetricsNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No False DOAJ Claim

class EthicsNoFalseDOAJClaim(Field):
    class EthicsNoFalseDOAJClaimCapability(WorkflowFormFieldCapability):
        label = "Compliance"

        options = [
            {"value": "y",
             "label": T.ethics_no_false_doaj_claim.compliant},
            {"value": "n",
             "label": T.ethics_no_false_doaj_claim.non_compliant}
        ]
        control_class = Radio
        control_render_class = InvertedLabelInputControlHTML
        render_class = WorkflowFieldRenderer

        check = T.ethics_no_false_doaj_claim.check
        instructions = T.ethics_no_false_doaj_claim.instructions
        resources = [
            {
                "label": T.ethics_no_false_doaj_claim.resource_label,
                "url": T.ethics_no_false_doaj_claim.resource_url
            }
        ]

    name = "ethics_no_false_doaj_claim"
    coerce = [Boolean()]
    capabilities = (EthicsNoFalseDOAJClaimCapability(),)


class EthicsNoFalseDOAJClaimNote(Field):
    name = "ethics_no_false_doaj_claim"
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)


class EthicsNoFalseDOAJClaimGroup(Structure):
    class EthicsNoFalseDOAJClaimGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_false_doaj_claim.label

        order = [
            "ethics_no_false_doaj_claim",
            "ethics_no_false_doaj_claim_note",
        ]

    name_ = "ethics_no_false_doaj_claim"
    capabilities_ = (EthicsNoFalseDOAJClaimGroupCapability(),)

    ethics_no_false_doaj_claim = EthicsNoFalseDOAJClaim(OPTIONAL, SINGLE)
    ethics_no_false_doaj_claim_note = EthicsNoFalseDOAJClaimNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No Susplicious Ties

class EthicsNoSuspiciousTies(Field):
    class EthicsNoSuspiciousTiesCapability(WorkflowFormFieldCapability):
        label = "Compliance"

        options = [
            {"value": "y",
             "label": T.ethics_no_suspicious_ties.compliant},
            {"value": "n",
             "label": T.ethics_no_suspicious_ties.non_compliant}
        ]
        control_class = Radio
        control_render_class = InvertedLabelInputControlHTML
        render_class = WorkflowFieldRenderer

        check = T.ethics_no_suspicious_ties.check
        instructions = T.ethics_no_suspicious_ties.instructions
        resources = [
            {
                "label": T.ethics_no_suspicious_ties.resource_label,
                "url": T.ethics_no_suspicious_ties.resource_url
            }
        ]

    name = "ethics_no_suspicious_ties"
    coerce = [Boolean()]
    capabilities = (EthicsNoSuspiciousTiesCapability(),)


class EthicsNoSuspiciousTiesNote(Field):
    name = "ethics_no_suspicious_ties"
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)


class EthicsNoSuspiciousTiesGroup(Structure):
    class EthicsNoSuspiciousTiesGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_suspicious_ties.label

        order = [
            "ethics_no_suspicious_ties",
            "ethics_no_suspicious_ties_note",
        ]

    name_ = "ethics_no_suspicious_ties"
    capabilities_ = (EthicsNoSuspiciousTiesGroupCapability(),)

    ethics_no_suspicious_ties = EthicsNoSuspiciousTies(OPTIONAL, SINGLE)
    ethics_no_suspicious_ties_note = EthicsNoSuspiciousTiesNote(OPTIONAL, SINGLE)

###########################################################

