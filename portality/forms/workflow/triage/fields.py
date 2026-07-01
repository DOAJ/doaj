from formulaic.serialise.form.render import InvertedLabelInputControlHTML
from portality.core import app

from formulaic.coerce.coerce import Boolean, Unicode
from formulaic.core import Field, FieldCapability, Structure, SINGLE, OPTIONAL
from formulaic.serialise.form.controls import Radio, Textarea, Hidden, TextInput
from formulaic.serialise.form.core import FormFieldCapability, CompoundFieldCapability
from portality.forms.workflow.core import JinjaFieldRenderer, JinjaControlRenderer, GenericControl, GenericField, \
    GenericCompound
from portality.ui import templates

T = app.cms.workflow.triage.fields

#####################################################
## Common infrastructure/reused components

########
## Compliance check capability, field, and associated renderers

class RadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_CONTROL_RADIO

class TriageRadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_TRIAGE_CONTROL_RADIO

class TriageComplianceCheckFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_TRIAGE_FIELD_COMPLIANCE

class TriageCompound(GenericCompound):
    template = templates.WORKFLOW_TRIAGE_COMPOUND

class ComplianceCheckCapability(FormFieldCapability):
    label = "Compliance"

    check = None
    remember = None
    instructions = None
    resources = []
    application_info = []

    control_class = Radio
    control_render_class = TriageRadioRenderer
    render_class = TriageComplianceCheckFieldRenderer

class ComplianceCheckField(Field):
    coerce = [Unicode()]

#######
## Generic notes capability and field

class NoteCapability(FormFieldCapability):
    label = "Note"
    placeholder = "Add a note ..."
    repeatable_label = "Notes"
    repeatable_minimum = 1
    repeatable_initial = 1

    control_class = Textarea
    control_class_renderer = GenericControl
    render_class = GenericField

class GeneralNoteCapability(NoteCapability):
    label = "Notes (optional)"
    placeholder = "You can add any notes related to this question here..."

class NoteField(Field):
    coerce = [Unicode()]
    capabilities = (NoteCapability(),)

class GeneralNote(Field):
    coerce = [Unicode()]
    capabilities = (GeneralNoteCapability(),)

#####################################################
## Record ID (hidden field required for identification)

class RecordID(Field):
    class RecordIDCapability(FormFieldCapability):
        label = "Record ID"
        control_class = Hidden
        control_render_class = GenericControl

    name = "id"
    coerce = [Unicode()]
    capabilities = (RecordIDCapability(),)

#####################################################
## Ethics: Not Excluded

class EthicsNotExcluded(ComplianceCheckField):
    class EthicsNotExcludedCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.ethics_not_excluded.compliant},
            {"value": "n", "label": T.ethics_not_excluded.non_compliant},
            {"value": "l", "label": T.ethics_not_excluded.later}
        ]

        check = T.ethics_not_excluded.check
        instructions = T.ethics_not_excluded.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.ethics_not_excluded.resources
        ]
        if "remember" in T.ethics_not_excluded:
            remember = T.ethics_not_excluded.remember

    name = "ethics_not_excluded"
    capabilities = (EthicsNotExcludedCapability(),)

class EthicsNotExcludedNote(NoteField):
    name = "ethics_not_excluded_note"


class EthicsNotExcludedGroup(Structure):
    class EthicsNotExcludedGroupCapability(CompoundFieldCapability):
        label = T.ethics_not_excluded.label

        order = [
            "ethics_not_excluded",
            "ethics_not_excluded_note",
        ]

        subfields = {
            "check": "ethics_not_excluded",
            "note": "ethics_not_excluded_note",
        }

        render_class = TriageCompound

    name_ = "ethics_not_excluded_group"
    capabilities_ = (EthicsNotExcludedGroupCapability(),)

    ethics_not_excluded = EthicsNotExcluded(OPTIONAL, SINGLE)
    ethics_not_excluded_note = EthicsNotExcludedNote(OPTIONAL, SINGLE)

##########################################################


##########################################################
## Ethics: Non Standard Metrics

class EthicsNoNonStandardMetrics(ComplianceCheckField):
    class EthicsNoNonStandardMetricsCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.ethics_no_nonstandard_metrics.compliant},
            {"value": "n", "label": T.ethics_no_nonstandard_metrics.non_compliant},
            {"value": "l", "label": T.ethics_not_excluded.later}
        ]

        check = T.ethics_no_nonstandard_metrics.check
        instructions = T.ethics_no_nonstandard_metrics.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.ethics_no_nonstandard_metrics.resources
        ]

    name = "ethics_no_nonstandard_metrics"
    capabilities = (EthicsNoNonStandardMetricsCapability(),)


class EthicsNoNonStandardMetricsNote(NoteField):
    name = "ethics_no_nonstandard_metrics_note"


class EthicsNoNonStandardMetricsGroup(Structure):
    class EthicsNoNonStandardMetricsGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_nonstandard_metrics.label

        order = [
            "ethics_no_nonstandard_metrics",
            "ethics_no_nonstandard_metrics_note",
        ]

        subfields = {
            "check": "ethics_no_nonstandard_metrics",
            "note": "ethics_no_nonstandard_metrics_note",
        }

        render_class = TriageCompound

    name_ = "ethics_no_nonstandard_metrics_group"
    capabilities_ = (EthicsNoNonStandardMetricsGroupCapability(),)

    ethics_no_nonstandard_metrics = EthicsNoNonStandardMetrics(OPTIONAL, SINGLE)
    ethics_no_nonstandard_metrics_note = EthicsNoNonStandardMetricsNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No Fake Impact

class EthicsNoFakeImpact(ComplianceCheckField):
    class EthicsNoFakeImpactCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.ethics_no_fake_impact.compliant},
            {"value": "n", "label": T.ethics_no_fake_impact.non_compliant},
            {"value": "l", "label": T.ethics_not_excluded.later}
        ]

        check = T.ethics_no_fake_impact.check
        instructions = T.ethics_no_fake_impact.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.ethics_no_fake_impact.resources
        ]

    name = "ethics_no_fake_impact"
    capabilities = (EthicsNoFakeImpactCapability(),)


class EthicsNoFakeImpactNote(NoteField):
    name = "ethics_no_fake_impact_note"


class EthicsNoFakeImpactGroup(Structure):
    class EthicsNoFakeImpactGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_fake_impact.label

        order = [
            "ethics_no_fake_impact",
            "ethics_no_fake_impact_note",
        ]

        subfields = {
            "check": "ethics_no_fake_impact",
            "note": "ethics_no_fake_impact_note",
        }

        render_class = TriageCompound

    name_ = "ethics_no_fake_impact_group"
    capabilities_ = (EthicsNoFakeImpactGroupCapability(),)

    ethics_no_fake_impact = EthicsNoFakeImpact(OPTIONAL, SINGLE)
    ethics_no_fake_impact_note = EthicsNoFakeImpactNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No False DOAJ Claim

class EthicsNoFalseDOAJClaim(ComplianceCheckField):
    class EthicsNoFalseDOAJClaimCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.ethics_no_false_doaj_claim.compliant},
            {"value": "n", "label": T.ethics_no_false_doaj_claim.non_compliant},
            {"value": "l", "label": T.ethics_not_excluded.later}
        ]

        check = T.ethics_no_false_doaj_claim.check
        instructions = T.ethics_no_false_doaj_claim.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.ethics_no_false_doaj_claim.resources
        ]

    name = "ethics_no_false_doaj_claim"
    capabilities = (EthicsNoFalseDOAJClaimCapability(),)


class EthicsNoFalseDOAJClaimNote(Field):
    name = "ethics_no_false_doaj_claim_note"


class EthicsNoFalseDOAJClaimGroup(Structure):
    class EthicsNoFalseDOAJClaimGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_false_doaj_claim.label

        order = [
            "ethics_no_false_doaj_claim",
            "ethics_no_false_doaj_claim_note",
        ]

        subfields = {
            "check": "ethics_no_false_doaj_claim",
            "note": "ethics_no_false_doaj_claim_note",
        }

        render_class = TriageCompound

    name_ = "ethics_no_false_doaj_claim_group"
    capabilities_ = (EthicsNoFalseDOAJClaimGroupCapability(),)

    ethics_no_false_doaj_claim = EthicsNoFalseDOAJClaim(OPTIONAL, SINGLE)
    ethics_no_false_doaj_claim_note = EthicsNoFalseDOAJClaimNote(OPTIONAL, SINGLE)

###########################################################

##########################################################
## Ethics: No Susplicious Ties

class EthicsNoSuspiciousTies(ComplianceCheckField):
    class EthicsNoSuspiciousTiesCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.ethics_no_suspicious_ties.compliant},
            {"value": "n", "label": T.ethics_no_suspicious_ties.non_compliant},
            {"value": "l", "label": T.ethics_not_excluded.later}
        ]

        check = T.ethics_no_suspicious_ties.check
        instructions = T.ethics_no_suspicious_ties.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.ethics_no_suspicious_ties.resources
        ]

    name = "ethics_no_suspicious_ties"
    capabilities = (EthicsNoSuspiciousTiesCapability(),)


class EthicsNoSuspiciousTiesNote(Field):
    name = "ethics_no_suspicious_ties_note"


class EthicsNoSuspiciousTiesGroup(Structure):
    class EthicsNoSuspiciousTiesGroupCapability(CompoundFieldCapability):
        label = T.ethics_no_suspicious_ties.label

        order = [
            "ethics_no_suspicious_ties",
            "ethics_no_suspicious_ties_note",
        ]

        subfields = {
            "check": "ethics_no_suspicious_ties",
            "note": "ethics_no_suspicious_ties_note",
        }

        render_class = TriageCompound

    name_ = "ethics_no_suspicious_ties_group"
    capabilities_ = (EthicsNoSuspiciousTiesGroupCapability(),)

    ethics_no_suspicious_ties = EthicsNoSuspiciousTies(OPTIONAL, SINGLE)
    ethics_no_suspicious_ties_note = EthicsNoSuspiciousTiesNote(OPTIONAL, SINGLE)

###########################################################

###########################################################
## ISSN: At Least One Registered ISSN

class ISSNAtLeastOne(ComplianceCheckField):
    class ISSNAtLeastOneCapability(ComplianceCheckCapability):
        options = [
            {"value": "y", "label": T.issn_at_least_one.compliant, "type": "compliant"},
            {"value": "n", "label": T.issn_at_least_one.non_compliant, "type": "noncompliant"},
            {"value": "l", "label": T.issn_at_least_one.later, "type": "later"},
            {"value": "a", "label": T.issn_at_least_one.action},

        ]

        check = T.issn_at_least_one.check
        instructions = T.issn_at_least_one.instructions
        resources = [
            {
                "label": r.label,
                "url": r.url
            } for r in T.issn_at_least_one.resources
        ]

        application_info = [
            {
                "label": T.issn_at_least_one.eissn.label,
                "lookup": lambda application, wfc: application.bibjson().eissn
            },
            {
                "label": T.issn_at_least_one.pissn.label,
                "lookup": lambda application, wfc: application.bibjson().pissn
            }
        ]

    name = "issn_at_least_one"
    capabilities = (ISSNAtLeastOneCapability(),)


class ISSNAtLeastOneNote(GeneralNote):
    name = "issn_at_least_one_note"

class EISSN(Field):
    class EISSNCapability(FormFieldCapability):
        label = T.issn_at_least_one.eissn.label
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField

    name = "eissn"
    coerce = [Unicode()]
    capabilities = (EISSNCapability(),)

class PISSN(Field):
    class PISSNCapability(FormFieldCapability):
        label = T.issn_at_least_one.pissn.label
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField

    name = "pissn"
    coerce = [Unicode()]
    capabilities = (PISSNCapability(),)

class ISSNAdditionalFieldsGroup(Structure):
    class ISSNAdditionalFieldsGroupCapability(CompoundFieldCapability):
        name = "edited_issns"
        label  = ""

        order = ["eissn", "pissn"]

class ISSNAtLeastOneGroup(Structure):
    class ISSNAtLeastOneGroupCapability(CompoundFieldCapability):
        label = T.issn_at_least_one.label

        order = [
            "issn_at_least_one",
            "edited_issns",
            "eissn",
            "pissn",
            "issn_at_least_one_note"
        ]
        subfields = {
            "check": "issn_at_least_one",
            "note": "issn_at_least_one_note",
            "additional_info": "edited_issns"
        }

        render_class = TriageCompound

    name_ = "issn_at_least_one_group"
    capabilities_ = (ISSNAtLeastOneGroupCapability(),)
    issn_at_least_one = ISSNAtLeastOne(OPTIONAL, SINGLE)
    edited_issns = ISSNAdditionalFieldsGroup(OPTIONAL, SINGLE)
    eissn = EISSN(OPTIONAL, SINGLE)
    pissn = PISSN(OPTIONAL, SINGLE)
    issn_at_least_one_note = ISSNAtLeastOneNote(OPTIONAL, SINGLE)