from flask import render_template

from formulaic.serialise.form.controls import Radio
from formulaic.serialise.form.core import FormFieldCapability, FormCapability, FieldsetCapability, FormRepresentation, \
    FieldsetRepresentation, FieldRepresentation
from formulaic.serialise.form.render import FormHTML, FieldHTML, InvertedLabelInputControlHTML, ControlHTML, \
    FieldsetHTML, ElementListHMTL, CompoundHTML
from portality.ui import templates


##########################################
# Jinja template renderers

class JinjaFormRenderer(FormHTML):
    template = None

    def draw(self, form:FormRepresentation, *args, **kwargs):
        html = render_template(self.template, form=form, **kwargs)
        return html

class JinjaFieldsetRenderer(FieldsetHTML):
    template = None

    def draw(self, fieldset:FieldsetRepresentation, *args, **kwargs):
        html = render_template(self.template, fieldset=fieldset, **kwargs)
        return html

class JinjaElementListRenderer(ElementListHMTL):
    template = None

    def draw(self, element_list:ElementListHMTL, *args, **kwargs):
        html = render_template(self.template, element_list=element_list, **kwargs)
        return html

class JinjaCompoundRenderer(CompoundHTML):
    template = None

    def draw(self, compound:CompoundHTML, *args, **kwargs):
        html = render_template(self.template, compound=compound, **kwargs)
        return html

class JinjaFieldRenderer(FieldHTML):
    template = None

    def draw(self, field:FieldRepresentation, *args, **kwargs):
        html = render_template(self.template, field=field, **kwargs)
        return html

class JinjaControlRenderer(ControlHTML):
    template = None

    def draw(self, controls:list[dict], *args, **kwargs):
        html = render_template(self.template, controls=controls, **kwargs)
        return html

###################

class GenericFieldset(JinjaFieldsetRenderer):
    template = templates.WORKFLOW_TRIAGE_FIELDSET

class GenericCompound(JinjaCompoundRenderer):
    template = templates.WORKFLOW_GENERIC_COMPOUND

class GenericElementList(JinjaElementListRenderer):
    template = templates.WORKFLOW_GENERIC_ELEMENT_LIST

class GenericField(JinjaFieldRenderer):
    template = templates.WORKFLOW_GENERIC_FIELD

class GenericControl(JinjaControlRenderer):
    template = templates.WORKFLOW_GENERIC_CONTROL

####################

class GenericROCompoundFieldRenderer(JinjaCompoundRenderer):
    template = templates.WORKFLOW_RO_GENERIC_COMPOUND

class InlineROCompoundFieldRenderer(JinjaCompoundRenderer):
    template = templates.WORKFLOW_RO_INLINE_COMPOUND

class GenericROFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_RO_GENERIC_FIELD

class GenericRORadioRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_RO_RADIO_CONTROL

class GenericROControlRenderer(JinjaControlRenderer):
    template = templates.WORKFLOW_RO_GENERIC_CONTROL

class GenericROFieldsetRenderer(JinjaFieldsetRenderer):
    template = templates.WORKFLOW_RO_GENERIC_FIELDSET

class ListEntryROFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_RO_LIST_ENTRY_FIELD

class JustControlROFieldRenderer(JinjaFieldRenderer):
    template = templates.WORKFLOW_RO_JUST_CONTROL_FIELD