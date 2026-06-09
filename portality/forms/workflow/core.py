from flask import render_template

from formulaic.serialise.form.controls import Radio
from formulaic.serialise.form.core import FormFieldCapability, FormCapability, FieldsetCapability
from formulaic.serialise.form.render import FormHTML, FieldHTML, InvertedLabelInputControlHTML


class JinjaFormRenderer(FormHTML):
    template = None

    def draw(self, representation, **kwargs):
        html = render_template(self.template, form=representation, **kwargs)
        return html

class JinjaFieldRenderer(FieldHTML):
    template = None

    def draw(self, representation, **kwargs):
        html = render_template(self.template, field=representation, **kwargs)
        return html

class ComplianceCheckFieldCapability(FormFieldCapability):
    label = "Compliance"

    check = None
    instructions = None
    resources = []

    control_class = Radio
    control_render_class = InvertedLabelInputControlHTML

class WorkflowFieldsetCapability(FieldsetCapability):
    pass

class WorkflowFormCapability(FormCapability):
    render_class = JinjaFormRenderer
