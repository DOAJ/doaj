from formulaic.error_codes import RegexDoesNotMatch, FieldsShouldBeDifferent, IsConditionallyRequired, DisallowedValue, \
    IsRequired
from formulaic.validate.form.validate import LimitToFormOptions
from formulaic.validate.validate import Regex, Different, RequiredIf, NoScriptTag, IsURL, RegexOnList
from portality.core import app

from formulaic.coerce.coerce import Boolean, Unicode
from formulaic.core import Field, FieldCapability, Structure, SINGLE, OPTIONAL, REQUIRED, REPEATABLE
from formulaic.serialise.form.controls import Radio, Textarea, Hidden, TextInput, Checkbox, URLInput
from formulaic.serialise.form.core import FormFieldCapability, CompoundFieldCapability
from portality.forms.workflow.core import JinjaFieldRenderer, JinjaControlRenderer, GenericControl, GenericField, \
    GenericCompound
from portality.ui import templates

T = app.cms.workflow.triage.fields
ISSN = r'^\d{4}-\d{3}(\d|X|x){1}$'

#####################################################
## Common infrastructure/reused components

########
## Compliance check capability, field, and associated renderers

class RadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_CONTROL_RADIO

class CheckboxRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_CONTROL_CHECKBOX

class TriageComplianceCheckFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_TRIAGE_FIELD_COMPLIANCE

class ComplianceCheckCapability(FormFieldCapability):
    label = "Compliance"

    check = None
    instructions = None
    resources = []
    application_info = []

    control_class = Radio
    control_render_class = RadioRenderer
    render_class = TriageComplianceCheckFieldRenderer

class ComplianceCheckField(Field):
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]

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

class NoteField(Field):
    coerce = [Unicode()]

#######
## options preparation

def options_for(source):
    return [
        {"value": k, "label": t} for k, t in source.answers.items()
    ]

def resource_for(source):
    label = source.resource_label if "resource_label" in source else None
    if label is None:
        label = source.resource_url if "resource_url" in source else None
    if label is None:
        return []
    return [
        {
            "label": source.resource_label,
            "url": source.resource_url
        }
    ]

#####################################################
## Record ID (hidden field required for identification)

class RecordID(Field):
    class C(FormFieldCapability):
        label = "Record ID"
        control_class = Hidden
        control_render_class = GenericControl

    name = "id"
    coerce = [Unicode()]
    capabilities = (C(),)

#####################################################
## Ethics: Not Excluded

class EthicsNotExcluded(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_not_excluded
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_not_excluded"
    capabilities = (C(),)

class EthicsNotExcludedNote(NoteField):
    name = "ethics_not_excluded_note"
    capabilities = (NoteCapability(),)

class EthicsNotExcludedGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_not_excluded.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "ethics_not_excluded_group"
    capabilities_ = (C(),)

    answer = EthicsNotExcluded(OPTIONAL, SINGLE)
    note = EthicsNotExcludedNote(OPTIONAL, SINGLE)

##########################################################

##########################################################
## Ethics: Non Standard Metrics

class EthicsNoNonStandardMetrics(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_no_nonstandard_metrics
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_no_nonstandard_metrics"
    capabilities = (C(),)

class EthicsNoNonStandardMetricsNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.ethics_no_nonstandard_metrics.validation.note.is_conditionally_required
        }
    name = "ethics_no_nonstandard_metrics_note"
    capabilities = (NC(),)

class EthicsNoNonStandardMetricsGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_no_nonstandard_metrics.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.ethics_no_nonstandard_metrics.validation.group.is_conditionally_required
        }

    name_ = "ethics_no_nonstandard_metrics_group"
    capabilities_ = (C(),)

    answer = EthicsNoNonStandardMetrics(OPTIONAL, SINGLE)
    note = EthicsNoNonStandardMetricsNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, # <- this field is required if
                  answer,        # <- this field has one of the values
                  T.ethics_no_nonstandard_metrics.non_compliant_answers # <- that is non compliant
                  )
    ]

###########################################################

##########################################################
## Ethics: No Fake Impact

class EthicsNoFakeImpact(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_no_fake_impact
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_no_fake_impact"
    capabilities = (C(),)

class EthicsNoFakeImpactNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.ethics_no_fake_impact.validation.note.is_conditionally_required
        }
    name = "ethics_no_fake_impact_note"
    capabilities = (NC(),)

class EthicsNoFakeImpactGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_no_fake_impact.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.ethics_no_fake_impact.validation.group.is_conditionally_required
        }

    name_ = "ethics_no_fake_impact_group"
    capabilities_ = (C(),)

    answer = EthicsNoFakeImpact(OPTIONAL, SINGLE)
    note = EthicsNoFakeImpactNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.ethics_no_fake_impact.non_compliant_answers  # <- that is non compliant
                   )
    ]

###########################################################

##########################################################
## Ethics: No False DOAJ Claim

class EthicsNoFalseDOAJClaim(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_no_false_doaj_claim
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_no_false_doaj_claim"
    capabilities = (C(),)

class EthicsNoFalseDOAJClaimNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.ethics_no_false_doaj_claim.validation.note.is_conditionally_required
        }
    name = "ethics_no_false_doaj_claim_note"
    capabilities = (NC(),)

class EthicsNoFalseDOAJClaimGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_no_false_doaj_claim.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.ethics_no_false_doaj_claim.validation.group.is_conditionally_required
        }

    name_ = "ethics_no_false_doaj_claim_group"
    capabilities_ = (C(),)

    answer = EthicsNoFalseDOAJClaim(OPTIONAL, SINGLE)
    note = EthicsNoFalseDOAJClaimNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.ethics_no_fake_impact.non_compliant_answers  # <- that is non compliant
                   )
    ]

###########################################################

##########################################################
## Ethics: No Susplicious Ties

class EthicsNoSuspiciousTies(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_no_suspicious_ties
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_no_suspicious_ties"
    capabilities = (C(),)

class EthicsNoSuspiciousTiesNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.ethics_no_suspicious_ties.validation.note.is_conditionally_required
        }
    name = "ethics_no_suspicious_ties_note"
    capabilities = (NC(),)

class EthicsNoSuspiciousTiesGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_no_suspicious_ties.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.ethics_no_suspicious_ties.validation.group.is_conditionally_required
        }

    name_ = "ethics_no_suspicious_ties_group"
    capabilities_ = (C(),)

    answer = EthicsNoSuspiciousTies(OPTIONAL, SINGLE)
    note = EthicsNoSuspiciousTiesNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.ethics_no_suspicious_ties.non_compliant_answers + T.ethics_no_suspicious_ties.compliant_answers
                   # <- that is either compliant or non compliant
                   )
    ]

###########################################################

###########################################################
## DOAJ Database: Withdrawn

class DatabaseWithdrawn(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_withdrawn
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_withdrawn"
    capabilities = (C(),)

class DatabaseWithdrawnNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.database_withdrawn.validation.note.is_conditionally_required
        }
    name = "database_withdrawn_note"
    capabilities = (NC(),)

class DatabaseWithdrawnGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_withdrawn.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.database_withdrawn.validation.group.is_conditionally_required
        }

    name_ = "database_withdrawn_group"
    capabilities_ = (C(),)

    answer = DatabaseWithdrawn(OPTIONAL, SINGLE)
    note = DatabaseWithdrawnNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.database_withdrawn.non_compliant_answers + T.database_withdrawn.compliant_answers
                   # <- that is either compliant or non compliant
                   )
    ]


###########################################################
## DOAJ Database: Withdrawn: Exception: Ignore Embargo

class DatabaseWithdrawnIgnoreEmbargo(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_withdrawn_exception_ignore_embargo
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_withdrawn_exception_ignore_embargo"
    capabilities = (C(),)

class DatabaseWithdrawnIgnoreEmbargoNote(NoteField):
    name = "database_withdrawn_exception_ignore_embargo_note"
    capabilities = (NoteCapability(),)

class DatabaseWithdrawnIgnoreEmbargoGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_withdrawn_exception_ignore_embargo.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_withdrawn_exception_ignore_embargo_group"
    capabilities_ = (C(),)

    answer = DatabaseWithdrawnIgnoreEmbargo(OPTIONAL, SINGLE)
    note = DatabaseWithdrawnIgnoreEmbargoNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Withdrawn: Exception: Website Unavailable

class DatabaseWithdrawnWebsiteUnavailable(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_withdrawn_exception_website_unavailable
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_withdrawn_exception_website_unavailable"
    capabilities = (C(),)

class DatabaseWithdrawnWebsiteUnavailableNote(NoteField):
    name = "database_withdrawn_exception_website_unavailable_note"
    capabilities = (NoteCapability(),)

class DatabaseWithdrawnWebsiteUnavailableGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_withdrawn_exception_website_unavailable.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_withdrawn_exception_website_unavailable_group"
    capabilities_ = (C(),)

    answer = DatabaseWithdrawnWebsiteUnavailable(OPTIONAL, SINGLE)
    note = DatabaseWithdrawnWebsiteUnavailableNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Withdrawn: Exception: Content

class DatabaseWithdrawnContent(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_withdrawn_exception_content
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_withdrawn_exception_content"
    capabilities = (C(),)

class DatabaseWithdrawnContentNote(NoteField):
    name = "database_withdrawn_exception_content_note"
    capabilities = (NoteCapability(),)

class DatabaseWithdrawnContentGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_withdrawn_exception_content.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_withdrawn_exception_content_group"
    capabilities_ = (C(),)

    answer = DatabaseWithdrawnContent(OPTIONAL, SINGLE)
    note = DatabaseWithdrawnContentNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Embargo

class DatabaseEmbargo(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_embargo
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_embargo"
    capabilities = (C(),)

class DatabaseEmbargoNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.database_embargo.validation.note.is_conditionally_required
        }

    name = "database_embargo_note"
    capabilities = (NC(),)

class DatabaseEmbargoGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo.label
        order = ["answer", "note"]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.database_embargo.validation.group.is_conditionally_required
        }

    name_ = "database_embargo_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargo(OPTIONAL, SINGLE)
    note = DatabaseEmbargoNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.database_embargo.non_compliant_answers + T.database_embargo.compliant_answers # <- that is either compliant or non compliant
                   )
    ]

###########################################################
## DOAJ Database: Withdrawn: Exception: ISSN

class DatabaseEmbargoISSN(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_embargo_exception_issn
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_embargo_exception_issn"
    capabilities = (C(),)

class DatabaseEmbargoISSNNote(NoteField):
    name = "database_embargo_exception_issn_note"
    capabilities = (NoteCapability(),)

class DatabaseEmbargoISSNGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo_exception_issn.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_embargo_exception_issn_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargoISSN(OPTIONAL, SINGLE)
    note = DatabaseEmbargoISSNNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Withdrawn: Exception: Maned Note

class DatabaseEmbargoManed(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_embargo_exception_maned
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_embargo_exception_note"
    capabilities = (C(),)

class DatabaseEmbargoManedNote(NoteField):
    name = "database_embargo_exception_maned_note"
    capabilities = (NoteCapability(),)

class DatabaseEmbargoManedGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo_exception_maned.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_embargo_exception_maned_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargoManed(OPTIONAL, SINGLE)
    note = DatabaseEmbargoManedNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Withdrawn: Exception: Website

class DatabaseEmbargoWebsite(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_embargo_exception_website
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_embargo_exception_website"
    capabilities = (C(),)

class DatabaseEmbargoWebsiteNote(NoteField):
    name = "database_embargo_exception_website_note"
    capabilities = (NoteCapability(),)

class DatabaseEmbargoWebsiteGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo_exception_website.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_embargo_exception_website_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargoWebsite(OPTIONAL, SINGLE)
    note = DatabaseEmbargoWebsiteNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Embargo: Exception: Journal Content

class DatabaseEmbargoContent(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_embargo_exception_content
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_embargo_exception_content"
    capabilities = (C(),)

class DatabaseEmbargoContentNote(NoteField):
    name = "database_embargo_exception_content_note"
    capabilities = (NoteCapability(),)

class DatabaseEmbargoContentGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo_exception_content.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_embargo_exception_content_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargoContent(OPTIONAL, SINGLE)
    note = DatabaseEmbargoContentNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Not Listed

class DatabaseNotListed(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_not_listed
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_not_listed"
    capabilities = (C(),)

class DatabaseNotListedNote(NoteField):
    name = "database_not_listed_note"
    capabilities = (NoteCapability(),)

class DatabaseNotListedGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_not_listed.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_not_listed_group"
    capabilities_ = (C(),)

    answer = DatabaseNotListed(OPTIONAL, SINGLE)
    note = DatabaseNotListedNote(OPTIONAL, SINGLE)

###########################################################
## DOAJ Database: Not Duplicate

class DatabaseNotDuplicate(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.database_not_duplicate
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "database_not_duplicate"
    capabilities = (C(),)

class DatabaseNotDuplicateNote(NoteField):
    name = "database_not_duplicate_note"
    capabilities = (NoteCapability(),)

class DatabaseNotDuplicateGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_not_duplicate.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "database_not_duplicate_group"
    capabilities_ = (C(),)

    answer = DatabaseNotDuplicate(OPTIONAL, SINGLE)
    note = DatabaseNotDuplicateNote(OPTIONAL, SINGLE)

###########################################################
## ISSN: At Least One Registered ISSN

class ISSNAtLeastOne(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.issn_at_least_one
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

        application_info = [
            {
                "label": S.info.eissn,
                "lookup": lambda application, wfc: application.bibjson().eissn
            },
            {
                "label": S.info.pissn,
                "lookup": lambda application, wfc: application.bibjson().pissn
            }
        ]

    name = "issn_at_least_one"
    capabilities = (C(),)

class ISSNAtLeastOneNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.database_embargo.validation.note.is_conditionally_required
        }
    name = "issn_at_least_one_note"
    capabilities = (NC(),)

class EISSN(Field):
    class C(FormFieldCapability):
        label = T.issn_at_least_one.edit.eissn
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            RegexDoesNotMatch: T.issn_at_least_one.validation.eissn.regex_not_match,
            FieldsShouldBeDifferent: T.issn_at_least_one.validation.eissn.fields_should_be_different
        }

    name = "eissn"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [Regex(ISSN)]

class PISSN(Field):
    class C(FormFieldCapability):
        label = T.issn_at_least_one.edit.pissn
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            RegexDoesNotMatch: T.issn_at_least_one.validation.pissn.regex_not_match,
            FieldsShouldBeDifferent: T.issn_at_least_one.validation.pissn.fields_should_be_different
        }

    name = "pissn"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [Regex(ISSN)]

class ISSNAtLeastOneGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.issn_at_least_one.label
        order = [
            "answer",
            "eissn",
            "pissn",
            "note"
        ]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.issn_at_least_one.validation.group.is_conditionally_required,
            FieldsShouldBeDifferent: T.issn_at_least_one.validation.group.fields_should_be_different
        }

    name_ = "issn_at_least_one_group"
    capabilities_ = (C(),)

    answer = ISSNAtLeastOne(OPTIONAL, SINGLE)
    eissn = EISSN(OPTIONAL, SINGLE)
    pissn = PISSN(OPTIONAL, SINGLE)
    note = ISSNAtLeastOneNote(OPTIONAL, SINGLE)

    validators_ = [
        Different(eissn, pissn),
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.issn_at_least_one.non_compliant_answers # <- that is non compliant
                   )
    ]

###########################################################
## ISSN: Title Match

class ISSNTitleMatch(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.issn_title_match
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "issn_title_match"
    capabilities = (C(),)

class ISSNTitleMatchNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.issn_title_match.validation.note.is_conditionally_required
        }
    name = "issn_title_match_note"
    capabilities = (NC(),)

class Title(Field):
    class C(FormFieldCapability):
        label = T.issn_title_match.edit.title
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.issn_title_match.validation.title.disallowed_value,
            IsRequired: T.issn_title_match.validation.title.is_required
        }

    name = "eissn"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [NoScriptTag()]

class ISSNTitleMatchGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.issn_title_match.label
        order = [
            "answer",
            "title",
            "note"
        ]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.issn_title_match.validation.group.is_conditionally_required
        }

    name_ = "issn_title_match_group"
    capabilities_ = (C(),)

    answer = ISSNTitleMatch(OPTIONAL, SINGLE)
    title = Title(REQUIRED, SINGLE)
    note = ISSNTitleMatchNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.issn_title_match.non_compliant_answers  # <- that is non compliant
                   )
    ]

###########################################################
## ISSN: Continuations

class ISSNContinuation(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.issn_continuation
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "issn_continuation"
    capabilities = (C(),)

class ISSNContinuationNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.issn_continuation.validation.note.is_conditionally_required
        }
    name = "issn_continuation_note"
    capabilities = (NC(),)

class Continues(Field):
    class C(FormFieldCapability):
        label = T.issn_continuation.edit.continues
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            RegexDoesNotMatch: T.issn_continuation.validation.continues.regex_not_match
        }

    name = "continues"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [RegexOnList(ISSN)]

class ISSNContinuationGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.issn_continuation.label
        order = [
            "answer",
            "continues",
            "note"
        ]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.issn_continuation.validation.group.is_conditionally_required
        }

    name_ = "issn_continuation_group"
    capabilities_ = (C(),)

    answer = ISSNContinuation(OPTIONAL, SINGLE)
    continues = Continues(OPTIONAL, SINGLE)
    note = ISSNContinuationNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.issn_continuation.non_compliant_answers  # <- that is non compliant
                   )
    ]

###########################################################
## Website: Working

class WebsiteWorking(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.website_working
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "website_working"
    capabilities = (C(),)

class WebsiteWorkingNote(NoteField):
    name = "website_working_note"
    capabilities = (NoteCapability(),)

class WebsiteWorkingGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_working.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "website_working_group"
    capabilities_ = (C(),)

    answer = WebsiteWorking(OPTIONAL, SINGLE)
    note = WebsiteWorkingNote(OPTIONAL, SINGLE)

###########################################################
## Website: ISSN

class WebsiteISSN(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.website_issn
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "website_issn"
    capabilities = (C(),)

class WebsiteISSNNote(NoteField):
    name = "website_issn_note"
    capabilities = (NoteCapability(),)

class WebsiteISSNGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_issn.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "website_issn_group"
    capabilities_ = (C(),)

    answer = WebsiteISSN(OPTIONAL, SINGLE)
    note = WebsiteISSNNote(OPTIONAL, SINGLE)

###########################################################
## Website: URL

class WebsiteURL(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.website_url
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "website_url"
    capabilities = (C(),)

class WebsiteURLNote(NoteField):
    name = "website_url_note"
    capabilities = (NoteCapability(),)

class WebsiteURLGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_url.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "website_url_group"
    capabilities_ = (C(),)

    answer = WebsiteURL(OPTIONAL, SINGLE)
    note = WebsiteURLNote(OPTIONAL, SINGLE)    # Note is required in all cases on this question

###########################################################
## Website: License Policy

class WebsiteLicensePolicy(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.website_license_policy
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "website_license_policy"
    capabilities = (C(),)

class WebsiteLicensePolicyNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.website_license_policy.validation.note.is_conditionally_required
        }
    name = "website_license_policy_note"
    capabilities = (NC(),)

class License(Field):
    class C(FormFieldCapability):
        label = T.website_license_policy.edit.license
        control_class = Checkbox
        multiple = True
        options = [
            {"label": "CC BY", "value": "CC BY"},
            {"label": "CC BY-SA", "value": "CC BY-SA"},
            {"label": "CC BY-ND", "value": "CC BY-ND"},
            {"label": "CC BY-NC", "value": "CC BY-NC"},
            {"label": "CC BY-NC-SA", "value": "CC BY-NC-SA"},
            {"label": "CC BY-NC-ND", "value": "CC BY-NC-ND"},
            {"label": "CC0", "value": "CC0"},
            {"label": "Public domain", "value": "Public domain"},
            {"label": "Publisher's own license", "value": "Publisher's own license"}
        ]
        control_render_class = CheckboxRenderer
        render_class = GenericField
        error_messages = {
            IsRequired: T.website_license_policy.validation.license.is_required,
            DisallowedValue: T.website_license_policy.validation.license.disallowed_value,
        }

    name = "license"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class LicenseAttribute(Field):
    class C(FormFieldCapability):
        label = T.website_license_policy.edit.license_attribute
        control_class = Checkbox
        multiple = True
        options = [
            {"label": "Attribution", "value": "BY"},
            {"label": "Share Alike", "value": "SA"},
            {"label": "No Derivatives", "value": "ND"},
            {"label": "No Commercial Usage", "value": "NC"}
        ]
        control_render_class = CheckboxRenderer
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.website_license_policy.validation.license_attribute.disallowed_value,
            IsConditionallyRequired: T.website_license_policy.validation.license_attribute.is_conditionally_required
        }

    name = "license_attribute"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class LicenseURL(Field):
    class C(FormFieldCapability):
        label = T.website_license_policy.edit.license_url
        control_class = URLInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            IsRequired: T.website_license_policy.validation.license_url.is_required,
            DisallowedValue: T.website_license_policy.validation.license_url.disallowed_value
        }

    name = "continues"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [IsURL()]

class WebsiteLicensePolicyGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_license_policy.label
        order = [
            "answer",
            "license",
            "license_attribute",
            "license_url",
            "note"
        ]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.website_license_policy.validation.group.is_conditionally_required
        }

    name_ = "website_license_policy_group"
    capabilities_ = (C(),)

    answer = WebsiteLicensePolicy(OPTIONAL, SINGLE)
    license = License(REQUIRED, REPEATABLE)
    license_attribute = LicenseAttribute(OPTIONAL, REPEATABLE)
    license_url = LicenseURL(REQUIRED, SINGLE)
    note = WebsiteLicensePolicyNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(license_attribute,  # <- this field is required if
                   license,  # <- this field has one of the values
                   "Publisher's own license"  # <- that is non compliant
                   ),
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.website_license_policy.compliant_answers + T.website_license_policy.non_compliant_answers # <- that is one of the compliant or non compliant answers
                   )

    ]

###########################################################
## Website: Copyright Policy

class WebsiteCopyright(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.website_copyright
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "website_copyright"
    capabilities = (C(),)

class WebsiteCopyrightNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.website_copyright.validation.note.is_conditionally_required
        }
    name = "website_copyright_note"
    capabilities = (NC(),)

class CopyrightAuthorRetains(Field):
    class C(FormFieldCapability):
        label = T.website_copyright.edit.copyright_author_retains
        control_class = Radio
        options = [
            {"label": "Yes", "value": "y"},
            {"label": "No", "value": "n"}
        ]
        control_render_class = RadioRenderer
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.website_copyright.validation.copyright_author_retains.disallowed_value,
            IsRequired: T.website_copyright.validation.copyright_author_retains.is_required
        }

    name = "copyright_author_retains"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class CopyrightURL(Field):
    class C(FormFieldCapability):
        label = T.website_copyright.edit.copyright_url
        control_class = URLInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            IsRequired: T.website_copyright.validation.copyright_url.is_required,
            DisallowedValue: T.website_copyright.validation.copyright_url.disallowed_value
        }

    name = "copyright_url"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)
    validators = [IsURL()]

class WebsiteCopyrightGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_copyright.label
        order = [
            "answer",
            "copyright_author_retains",
            "copyright_url",
            "note"
        ]
        render_class = GenericCompound
        error_messages = {
            IsConditionallyRequired: T.website_copyright.validation.group.is_conditionally_required
        }

    name_ = "website_copyright_group"
    capabilities_ = (C(),)

    answer = WebsiteCopyright(OPTIONAL, SINGLE)
    copyright_author_retains = CopyrightAuthorRetains(REQUIRED, SINGLE)
    copyright_url = CopyrightURL(REQUIRED, SINGLE)
    note = WebsiteCopyrightNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.website_copyright.compliant_answers + T.website_copyright.non_compliant_answers  # <- that is one of the compliant or non compliant answers
                   )
    ]

###########################################################
## Content: No Login

class ContentNoLogin(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_no_login
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_no_login"
    capabilities = (C(),)

class ContentNoLoginNote(NoteField):
    name = "content_no_login_note"
    capabilities = (NoteCapability(),)

class ContentNoLoginGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_no_login.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_no_login_group"
    capabilities_ = (C(),)

    answer = ContentNoLogin(OPTIONAL, SINGLE)
    note = ContentNoLoginNote(OPTIONAL, SINGLE)

###########################################################
## Content: No Embargo

class ContentNoEmbargo(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_no_embargo
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_no_embargo"
    capabilities = (C(),)

class ContentNoEmbargoNote(NoteField):
    name = "content_no_embargo_note"
    capabilities = (NoteCapability(),)

class ContentNoEmbargoGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_no_embargo.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_no_embargo_group"
    capabilities_ = (C(),)

    answer = ContentNoEmbargo(OPTIONAL, SINGLE)
    note = ContentNoEmbargoNote(OPTIONAL, SINGLE)

###########################################################
## Content: Publish Enough

class ContentPublishEnough(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_publish_enough
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_publish_enough"
    capabilities = (C(),)

class ContentPublishEnoughNote(NoteField):
    name = "content_publish_enough_note"
    capabilities = (NoteCapability(),)

class ContentPublishEnoughGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_publish_enough.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_publish_enough_group"
    capabilities_ = (C(),)

    answer = ContentPublishEnough(OPTIONAL, SINGLE)
    note = ContentPublishEnoughNote(OPTIONAL, SINGLE)

###########################################################
## Content: Unique Link

class ContentUniqueLink(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_unique_link
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_unique_link"
    capabilities = (C(),)

class ContentUniqueLinkNote(NoteField):
    name = "content_unique_link_note"
    capabilities = (NoteCapability(),)

class ContentUniqueLinkGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_unique_link.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_unique_link_group"
    capabilities_ = (C(),)

    answer = ContentUniqueLink(OPTIONAL, SINGLE)
    note = ContentUniqueLinkNote(OPTIONAL, SINGLE)

###########################################################
## Content: Format

class ContentFormat(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_format
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_format"
    capabilities = (C(),)

class ContentFormatNote(NoteField):
    name = "content_format_note"
    capabilities = (NoteCapability(),)

class ContentFormatGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_format.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_format_group"
    capabilities_ = (C(),)

    answer = ContentFormat(OPTIONAL, SINGLE)
    note = ContentFormatNote(OPTIONAL, SINGLE)

###########################################################
## Content: Format

class ContentNewJournal(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.content_new_journal
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "content_new_journal"
    capabilities = (C(),)

class ContentNewJournalNote(NoteField):
    name = "content_new_journal_note"
    capabilities = (NoteCapability(),)

class ContentNewJournalGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_new_journal.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "content_new_journal_group"
    capabilities_ = (C(),)

    answer = ContentNewJournal(OPTIONAL, SINGLE)
    note = ContentNewJournalNote(OPTIONAL, SINGLE)

###########################################################
## Admin: Metadata Review

class AdminMetadataReview(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.admin_metadata_review
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "admin_metadata_review"
    capabilities = (C(),)

class AdminMetadataReviewNote(NoteField):
    name = "admin_metadata_review_note"
    capabilities = (NoteCapability(),)

class AdminMetadataReviewGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.admin_metadata_review.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "admin_metadata_review_group"
    capabilities_ = (C(),)

    answer = AdminMetadataReview(OPTIONAL, SINGLE)
    note = AdminMetadataReviewNote(OPTIONAL, SINGLE)

###########################################################
## Admin: Special Exceptions

class AdminSpecialException(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.admin_special_exception
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "admin_special_exception"
    capabilities = (C(),)

class AdminSpecialExceptionNote(NoteField):
    name = "admin_special_exception_note"
    capabilities = (NoteCapability(),)

class AdminSpecialExceptionGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.admin_special_exception.label
        order = ["answer", "note"]
        render_class = GenericCompound

    name_ = "admin_special_exception_group"
    capabilities_ = (C(),)

    answer = AdminSpecialException(OPTIONAL, SINGLE)
    note = AdminSpecialExceptionNote(OPTIONAL, SINGLE)

