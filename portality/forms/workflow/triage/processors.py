from formulaic.serialise.form.core import FormSerialiser, FormDataParser
from portality.forms.workflow.crosswalk import TriageForm2WorkflowControl, WorkflowControl2TriageForm
from portality.forms.workflow.triage.forms import TriageForm, TriageSubmission
from portality.models import Application, WorkflowControl


class TriageFormProcessor:
    def __init__(self, source_application:Application, source_wfc:WorkflowControl, raw_formdata:dict=None):
        self._source_application = source_application
        self._source_wfc = source_wfc
        self._raw_formdata = raw_formdata

        self.form2obj_xwalk = TriageForm2WorkflowControl()
        self.obj2form_xwalk = WorkflowControl2TriageForm()
        self.serialiser = FormSerialiser()
        self.parser = FormDataParser()

        self._form_inst:TriageSubmission = None
        self._target_application:Application = None
        self._target_wfc:WorkflowControl = None

    @property
    def target_application(self):
        return self._target_application

    @property
    def target_workflow_control(self):
        return self._target_wfc

    def render_form(self):
        if self._source_wfc and self._source_application:
            if self._form_inst is None:
                self._form_inst = self.obj2form_xwalk.transform(self._source_wfc, self._source_application)
            form_html = self.serialiser.data_to_string(self._form_inst.data, self._form_inst.struct, application=self._source_application, wfc=self._source_wfc)
            return form_html
        elif self._source_wfc or self._source_application:
            raise ValueError("Must provide both source application and workflow control, or neither")
        else:
            form_html = self.serialiser.data_to_string({}, TriageSubmission.struct, application=Application(), wfc=WorkflowControl())
            return form_html

    def validate(self):
        pass

    def process_raw_form(self, account):
        if self._raw_formdata is None:
            raise ValueError("No raw form data to process")

        data = self.parser.representation_to_data(self._raw_formdata, TriageSubmission.struct)
        self._form_inst = TriageSubmission(data)

        partial_wfc, partial_application = self.form2obj_xwalk.transform(self._form_inst, account)
        self._target_application = self._patch_application(partial_application)
        self._target_wfc = self._patch_wfc(partial_wfc)

    def _patch_wfc(self, partial_wfc:WorkflowControl) -> WorkflowControl:
        pass

    def _patch_application(self, partial_application:Application) -> Application:
        pass

    def finalise(self, account):
        pass
