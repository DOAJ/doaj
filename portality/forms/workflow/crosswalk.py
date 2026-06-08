from portality.models import WorkflowControl


class WorkflowControl2TriageForm(object):
    def transform(self, wfc:WorkflowControl):
        result = {}
        result['id'] = wfc.id
        result['whatever'] = None
        return result