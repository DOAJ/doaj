from formulaic.serialise.form.core import FormFieldCapability, FormCapability, FieldsetCapability


class WorkflowFormFieldCapability(FormFieldCapability):
    check = None
    instructions = None
    resources = None

class WorkflowFieldsetCapability(FieldsetCapability):
    pass

class WorkflowFormCapability(FormCapability):
    pass