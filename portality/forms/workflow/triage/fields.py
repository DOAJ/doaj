from flask import render_template

from formulaic.error_codes import RegexDoesNotMatch, FieldsShouldBeDifferent, IsConditionallyRequired, DisallowedValue, \
    IsRequired
from formulaic.validate.form.validate import LimitToFormOptions
from formulaic.validate.validate import Regex, Different, RequiredIf, NoScriptTag, IsURL, RegexOnList, AllInvalid, \
    RequiredIfNot
from portality.core import app

from formulaic.coerce.coerce import Boolean, Unicode
from formulaic.core import Field, FieldCapability, Structure, SINGLE, OPTIONAL, REQUIRED, REPEATABLE
from formulaic.serialise.form.controls import Radio, Textarea, Hidden, TextInput, Checkbox, URLInput, Buttons
from formulaic.serialise.form.core import FormFieldCapability, CompoundFieldCapability, GenericFormStructureCapability
from portality.forms.workflow.core import JinjaFieldRenderer, JinjaControlRenderer, JinjaCompoundRenderer, GenericControl, GenericField, \
    GenericCompound
from portality.ui import templates

T = app.cms.workflow.triage.fields
ISSN = r'^\d{4}-\d{3}(\d|X|x){1}$'

#####################################################
## Common infrastructure/reused components

########
## Compliance check capability, field, and associated renderers

## Compound renderers

class TriageCompound(GenericCompound):
    template = templates.WORKFLOW_TRIAGE_COMPOUND

class ExceptionListRenderer(JinjaCompoundRenderer):
    template = templates.WORKFLOW_TRIAGE_EXCEPTIONS_LIST

## Field renderers

class DummyRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_TRIAGE_DUMMY

class TriageComplianceCheckFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_TRIAGE_FIELD_COMPLIANCE

## Control Renderers

class RadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_CONTROL_RADIO

class TriageRadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_TRIAGE_CONTROL_RADIO

class CheckboxRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_CONTROL_CHECKBOX

class TriageCheckboxRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_TRIAGE_CONTROL_CHECKBOX

class TriageCheckboxListRenderer(GenericCompound):
    template = templates.WORKFLOW_TRIAGE_CHECKBOX_QUESTION

class ButtonsRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_BUTTONS

#################################

class ComplianceCheckCapability(FormFieldCapability):
    role = "check"
    label = "Compliance"

    check = None
    remember = None
    instructions = None
    resources = []
    application_info = []

    control_class = Radio
    control_render_class = TriageRadioRenderer
    render_class = TriageComplianceCheckFieldRenderer

class ButtonsCapability(FormFieldCapability):
    role = "check"
    label = "Compliance"

    check = None
    remember = None
    instructions = None
    resources = []
    application_info = []

    control_class = Buttons
    control_render_class = ButtonsRenderer


class ComplianceCheckField(Field):
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]

class CheckboxQuestionCapability(CompoundFieldCapability):
    list_render_class = TriageCheckboxListRenderer
    render_class = TriageCheckboxListRenderer
    sr_only_legend = False

#######
## Generic notes capability and field
class NoteCapability(FormFieldCapability):
    role = "note"
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

class DummyNote(NoteCapability):
    render_class = DummyRenderer

class NoteField(Field):
    coerce = [Unicode()]

#######
## options preparation

def options_for(source):
    return [
        {"value": k, "label": t} for k, t in source.answers.items()
    ]

def exception_options_for(source):
    return [
        {"value": k, "label": t} for k, t in source.exceptions.items()
    ]

def resource_for(source):
    resources = []
    if "resources" not in source:
        return resources

    for r in source.resources:
        label = r.label
        if label is None:
            label = source.url
        if label is None:
            continue
        resources.append({
            "label": label,
            "url": r.url
        })
    return resources

class GeneralNote(Field):
    coerce = [Unicode()]
    capabilities = (GeneralNoteCapability(),)

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
        remember = S.remember
        resources = resource_for(S)

    name = "ethics_not_excluded"
    capabilities = (C(),)

class EthicsNotExcludedNote(NoteField):
    name = "ethics_not_excluded_note"
    capabilities = (GeneralNoteCapability(),)

class EthicsNotExcludedGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_not_excluded.label
        order = ["answer", "note"]
        render_class = TriageCompound

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
        remember = S.remember
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
        render_class = TriageCompound
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
        remember = S.remember
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
        render_class = TriageCompound
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
        render_class = TriageCompound
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
## Ethics: Submission to Publication time

class EthicsPubTime(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.ethics_submission_to_publication_time
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "ethics_submission_to_publication_time"
    capabilities = (C(),)

class EthicsPubTimeNote(NoteField):
    name = "ethics_no_false_doaj_claim_note"
    capabilities = (NoteCapability(),)

class EthicsPubTimeGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.ethics_submission_to_publication_time.label
        order = ["answer", "note"]
        render_class = TriageCompound
        error_messages = {}

    name_ = "ethics_submission_to_publication_time_group"
    capabilities_ = (C(),)

    answer = EthicsPubTime(OPTIONAL, SINGLE)
    note = EthicsPubTimeNote(OPTIONAL, SINGLE)

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
        render_class = TriageCompound
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

class DatabaseWithdrawnExceptions(Field):
    class C(FormFieldCapability):
        role = "special"
        label = T.database_withdrawn.edit.exceptions
        control_class = Checkbox
        multiple = True
        options = exception_options_for(T.database_withdrawn)
        control_render_class = CheckboxRenderer
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.database_withdrawn.validation.exceptions.disallowed_value,
        }

    name = "database_withdrawn_exceptions"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

### The main entry point to the Database: Withdrawn question

class DatabaseWithdrawnGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_withdrawn.label
        order = ["answer", "note", "exceptions"]
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.database_withdrawn.validation.group.is_conditionally_required
        }

    name_ = "database_withdrawn_group"
    capabilities_ = (C(),)

    answer = DatabaseWithdrawn(OPTIONAL, SINGLE)
    note = DatabaseWithdrawnNote(OPTIONAL, SINGLE)
    exceptions = DatabaseWithdrawnExceptions(OPTIONAL, REPEATABLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.database_withdrawn.non_compliant_answers # <- that is non compliant
                   )
    ]


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

class DatabaseEmbargoExceptions(Field):
    class C(FormFieldCapability):
        role = "special"
        label = T.database_embargo.edit.exceptions
        control_class = Checkbox
        multiple = True
        options = exception_options_for(T.database_embargo)
        control_render_class = CheckboxRenderer
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.database_embargo.validation.exceptions.disallowed_value,
        }

    name = "database_embargo_exceptions"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class DatabaseEmbargoGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_embargo.label
        order = ["answer", "note", "exceptions"]
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.database_embargo.validation.group.is_conditionally_required
        }

    name_ = "database_embargo_group"
    capabilities_ = (C(),)

    answer = DatabaseEmbargo(OPTIONAL, SINGLE)
    note = DatabaseEmbargoNote(OPTIONAL, SINGLE)
    exceptions = DatabaseEmbargoExceptions(OPTIONAL, REPEATABLE)

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
        render_class = TriageCompound

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.database_not_duplicate.validation.note.is_conditionally_required
        }
    name = "database_not_duplicate_note"
    capabilities = (NC(),)

class DatabaseNotDuplicateGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.database_not_duplicate.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "database_not_duplicate_group"
    capabilities_ = (C(),)

    answer = DatabaseNotDuplicate(OPTIONAL, SINGLE)
    note = DatabaseNotDuplicateNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.database_not_duplicate.non_compliant_answers)
    ]

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

class ISSNAtLeastOneNote(GeneralNote):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.database_embargo.validation.note.is_conditionally_required
        }
    name = "issn_at_least_one_note"
    capabilities = (NC(),)

class EISSN(Field):
    class C(FormFieldCapability):
        role = "special"
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
        role = "special"
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

class ISSNAdditionalFields(Structure):
    class C(CompoundFieldCapability):
        role = "special"
        label  = "ISSNs"
        order = ["eissn", "pissn"]
        error_messages = {
            FieldsShouldBeDifferent: T.issn_at_least_one.validation.group.fields_should_be_different
        }
        render_class = GenericCompound

    name_ = "edited_issns"
    capabilities_ = (C(),)

    eissn = EISSN(OPTIONAL, SINGLE)
    pissn = PISSN(OPTIONAL, SINGLE)

    validators_ = [
        Different(eissn, pissn)
    ]

class ISSNAtLeastOneGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.issn_at_least_one.label
        order = [
            "answer",
            "edited_issns",
            "note"
        ]
        action_group = ["edited_issns"]
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.issn_at_least_one.validation.group.is_conditionally_required,
        }

    name_ = "issn_at_least_one_group"
    capabilities_ = (C(),)

    answer = ISSNAtLeastOne(OPTIONAL, SINGLE)
    note = ISSNAtLeastOneNote(OPTIONAL, SINGLE)
    edited_issns = ISSNAdditionalFields(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note,  # <- this field is required if
                   answer,  # <- this field has one of the values
                   T.issn_at_least_one.non_compliant_answers # <- that is non compliant
                   )
    ]

###########################################################
## ISSN: Country Match

class ISSNCountryMatch(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.issn_country_match
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

        application_info = [
            {
                "label": S.info.country,
                "lookup": lambda application, wfc: application.bibjson().publisher_country_name()
            }
        ]

    name = "issn_country_match"
    capabilities = (C(),)

class ISSNCountryMatchNote(NoteField):
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.issn_country_match.validation.note.is_conditionally_required
        }
    name = "issn_country_match_note"
    capabilities = (NC(),)

class ISSNCountryMatchGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.issn_country_match.label
        order = [
            "answer",
            "note"
        ]
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.issn_country_match.validation.group.is_conditionally_required
        }

    name_ = "issn_country_match_group"
    capabilities_ = (C(),)

    answer = ISSNCountryMatch(OPTIONAL, SINGLE)
    note = ISSNCountryMatchNote(OPTIONAL, SINGLE)


###########################################################
## ISSN: Title Match

class ISSNTitleMatch(ComplianceCheckField):
    class C(ComplianceCheckCapability):
        S = T.issn_title_match
        options = options_for(S)
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

        application_info = [
            {
                "label": S.info.title,
                "lookup": lambda application, wfc: application.bibjson().title
            }
        ]

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
        role = "special"
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
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.issn_title_match.validation.group.is_conditionally_required
        }

    name_ = "issn_title_match_group"
    capabilities_ = (C(),)

    answer = ISSNTitleMatch(OPTIONAL, SINGLE)
    title = Title(REQUIRED, SINGLE)
    note = ISSNTitleMatchNote(OPTIONAL, SINGLE)

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
        role = "special"
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
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.issn_continuation.validation.group.is_conditionally_required
        }

    name_ = "issn_continuation_group"
    capabilities_ = (C(),)

    answer = ISSNContinuation(OPTIONAL, SINGLE)
    continues = Continues(OPTIONAL, SINGLE)
    note = ISSNContinuationNote(OPTIONAL, SINGLE)

    validators_ = [
        AllInvalid( # the application IS a continuation AND its preceeding journal is not in DOAJ
            RequiredIf(note,  # <- this field is required if
                       answer,  # <- this field has one of the values
                       T.issn_continuation.notes_required_answers  # <- that is compliant
                       ),
            RequiredIfNot(note, continues),
            error_code=IsConditionallyRequired
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
        render_class = TriageCompound

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.website_issn.validation.note.is_conditionally_required
        }
    name = "website_issn_note"
    capabilities = (NC(),)

class WebsiteISSNGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_issn.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "website_issn_group"
    capabilities_ = (C(),)

    answer = WebsiteISSN(OPTIONAL, SINGLE)
    note = WebsiteISSNNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.website_issn.non_compliant_answers)
    ]

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.website_url.validation.note.is_conditionally_required
        }
    name = "website_url_note"
    capabilities = (NC(),)

class WebsiteURLGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.website_url.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "website_url_group"
    capabilities_ = (C(),)

    answer = WebsiteURL(OPTIONAL, SINGLE)
    note = WebsiteURLNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.website_url.note_required_answers)
    ]

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
        role = "special"
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
        role = "special"
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
        role = "special"
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
        render_class = TriageCompound
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
                   "Publisher's own license"
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
        role = "special"
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
        role = "special"
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
        render_class = TriageCompound
        error_messages = {
            IsConditionallyRequired: T.website_copyright.validation.group.is_conditionally_required
        }

    name_ = "website_copyright_group"
    capabilities_ = (C(),)

    answer = WebsiteCopyright(OPTIONAL, SINGLE)
    copyright_author_retains = CopyrightAuthorRetains(REQUIRED, SINGLE)
    copyright_url = CopyrightURL(REQUIRED, SINGLE)
    note = WebsiteCopyrightNote(OPTIONAL, SINGLE)


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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.content_no_login.validation.note.is_conditionally_required
        }
    name = "content_no_login_note"
    capabilities = (NC(),)

class ContentNoLoginGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_no_login.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "content_no_login_group"
    capabilities_ = (C(),)

    answer = ContentNoLogin(OPTIONAL, SINGLE)
    note = ContentNoLoginNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.content_no_login.non_compliant_answers)
    ]

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.content_no_embargo.validation.note.is_conditionally_required
        }
    name = "content_no_embargo_note"
    capabilities = (NC(),)

class ContentNoEmbargoGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_no_embargo.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "content_no_embargo_group"
    capabilities_ = (C(),)

    answer = ContentNoEmbargo(OPTIONAL, SINGLE)
    note = ContentNoEmbargoNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.content_no_embargo.non_compliant_answers)
    ]

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.content_publish_enough.validation.note.is_conditionally_required
        }
    name = "content_publish_enough_note"
    capabilities = (NC(),)

class ContentPublishEnoughGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_publish_enough.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "content_publish_enough_group"
    capabilities_ = (C(),)

    answer = ContentPublishEnough(OPTIONAL, SINGLE)
    note = ContentPublishEnoughNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.content_publish_enough.non_compliant_answers)
    ]

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.content_unique_link.validation.note.is_conditionally_required
        }
    name = "content_unique_link_note"
    capabilities = (NC(),)

class ContentUniqueLinkGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_unique_link.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "content_unique_link_group"
    capabilities_ = (C(),)

    answer = ContentUniqueLink(OPTIONAL, SINGLE)
    note = ContentUniqueLinkNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.content_unique_link.non_compliant_answers)
    ]

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
    class NC(NoteCapability):
        error_messages = {
            IsConditionallyRequired: T.content_format.validation.note.is_conditionally_required
        }
    name = "content_format_note"
    capabilities = (NC(),)

class ContentFormatGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_format.label
        order = ["answer", "note"]
        render_class = TriageCompound

    name_ = "content_format_group"
    capabilities_ = (C(),)

    answer = ContentFormat(OPTIONAL, SINGLE)
    note = ContentFormatNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(note, answer, T.content_format.non_compliant_answers)
    ]

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

class ContentNewJournalExceptions(Field):
    class C(FormFieldCapability):
        role = "special"
        label = T.content_new_journal.edit.exceptions
        control_class = Checkbox
        multiple = True
        options = exception_options_for(T.content_new_journal)
        control_render_class = CheckboxRenderer
        render_class = GenericField
        error_messages = {
            DisallowedValue: T.content_new_journal.validation.exceptions.disallowed_value,
        }

    name = "new_journal_exceptions"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class ContentNewJournalGroup(Structure):
    class C(CompoundFieldCapability):
        label = T.content_new_journal.label
        order = ["answer", "note", "exceptions"]
        render_class = TriageCompound

    name_ = "content_new_journal_group"
    capabilities_ = (C(),)

    answer = ContentNewJournal(OPTIONAL, SINGLE)
    note = ContentNewJournalNote(OPTIONAL, SINGLE)
    exceptions = ContentNewJournalExceptions(OPTIONAL, REPEATABLE)

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
        render_class = TriageCompound

    name_ = "admin_metadata_review_group"
    capabilities_ = (C(),)

    answer = AdminMetadataReview(OPTIONAL, SINGLE)
    note = AdminMetadataReviewNote(OPTIONAL, SINGLE)

###########################################################
## Admin: Special Exceptions

class AdminSpecialException(ComplianceCheckField):
    class C(ButtonsCapability):
        S = T.admin_special_exception
        options = [
            {
                "class": "compliant",
                "label": T.admin_special_exception.answers.compliant,
                "onclick": "doaj.triage.continue()",
                "type": "button",
                "role": "compliant"
             },
            {
                "class": "non-compliant",
                "label": T.admin_special_exception.answers.non_compliant,
                "onclick": "doaj.triage.reject()",
                "type": "button",
                "role": "non_compliant"
            },

        ]
        check = S.check
        instructions = S.instructions
        resources = resource_for(S)

    name = "admin_special_exception"
    capabilities = (C(),)

class AdminSpecialExceptionNote(NoteField):
    name = "admin_special_exception_note"
    capabilities = (GeneralNoteCapability(),)

class SpecialExceptions(Field):
    class C(FormFieldCapability):
        role="options"
        label = T.admin_special_exception.edit.special_exceptions
        control_class = Checkbox
        multiple = True
        options = exception_options_for(T.admin_special_exception)
        control_render_class = TriageCheckboxRenderer
        error_messages = {
            DisallowedValue: T.admin_special_exception.validation.special_exceptions.disallowed_value,
        }

    name = "special_exceptions"
    coerce = [Unicode()]
    validators = [LimitToFormOptions()]
    capabilities = (C(),)

class SpecialExceptionOther(Field):
    class C(FormFieldCapability):
        role = "other"
        label = T.admin_special_exception.edit.other
        control_class = TextInput
        control_render_class = GenericControl
        render_class = GenericField
        error_messages = {
            IsConditionallyRequired: T.admin_special_exception.validation.special_exception_other.is_conditionally_required
        }

    name = "special_exception_other"
    coerce = [Unicode(trim_whitespace=True)]
    capabilities = (C(),)

class AdminSpecialExceptionGroup(Structure):
    class C(CheckboxQuestionCapability):
        label = T.admin_special_exception.label
        order = ["answer", "special_exceptions", "special_exception_other", "note"]
        ui = [
            {
                "conditional": {
                    "field": "special_exceptions",
                    "conditions": [
                        {
                            "field": "answer",
                            "any_of": [T.admin_special_exception.non_compliant_answers]
                        }
                    ]
                }
            },
            {
                "conditional": {
                    "field": "special_exception_other",
                    "conditions": [
                        {
                            "field": "answer",
                            "any_of": [T.admin_special_exception.non_compliant_answers]
                        },
                        {
                            "field": "special_exceptions",
                            "any_of": ["other"]
                        }
                    ]
                }
            }
        ]

    name_ = "admin_special_exception_group"
    capabilities_ = (C(),)
    sr_only_legend = True

    answer = AdminSpecialException(OPTIONAL, SINGLE)
    special_exceptions = SpecialExceptions(OPTIONAL, REPEATABLE)
    special_exception_other = SpecialExceptionOther(OPTIONAL, SINGLE)
    note = AdminSpecialExceptionNote(OPTIONAL, SINGLE)

    validators_ = [
        RequiredIf(special_exception_other,  # <- this field is required if
                    special_exceptions,  # <- this field has one of the values
                    ["other"]  # <- that is non compliant
                   )
    ]
