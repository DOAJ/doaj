from flask import render_template

from formulaic.serialise.form.core import FormFieldCapability, FormCapability, FieldsetCapability
from formulaic.serialise.form.render import FormHTML, FieldHTML


class JinjaFormRenderer(FormHTML):
    template = None

    def draw(self, representation):
        html = render_template(self.template, form=representation)
        return html

class JinjaFieldRenderer(FieldHTML):
    template = None

    def draw(self, representation):
        html = render_template(self.template, field=representation)
        return html

class WorkflowFormFieldCapability(FormFieldCapability):
    check = None
    instructions = None
    resources = []

class WorkflowFieldsetCapability(FieldsetCapability):
    pass

class WorkflowFormCapability(FormCapability):
    render_class = JinjaFormRenderer
