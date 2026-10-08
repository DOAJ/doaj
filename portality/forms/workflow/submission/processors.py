from formulaic.serialise.form.core import FormDataParser, FormSerialiser
from portality.forms.workflow.submission.crosswalk import WorkflowControl2SubmissionForm
from portality.forms.workflow.submission.forms import SubmissionRO
from portality.models import Application, WorkflowControl


class OriginalROFormProcessor(object):
    def __init__(self, source_application:Application, source_wfc:WorkflowControl, raw_formdata:dict=None):
        self._source_application = source_application
        self._source_wfc = source_wfc
        self._raw_formdata = raw_formdata

        self.form2obj_xwalk = None # Not needed
        self.obj2form_xwalk = WorkflowControl2SubmissionForm()
        self.serialiser = FormSerialiser()
        self.parser = FormDataParser()

        self._form_inst:SubmissionRO = None
        self._target_application:Application = None
        self._target_wfc:WorkflowControl = None

        if self._raw_formdata is not None:
            self.rawform2forminstance()

        elif self._source_application and self._source_wfc:
            self.source2forminstance()

        else:
            self.blank_form()

    ################################
    ## accessors

    @property
    def source_application(self):
        return self._source_application

    @property
    def source_workflow_control(self):
        return self._source_wfc

    @property
    def target_application(self):
        return self._target_application

    @property
    def target_workflow_control(self):
        return self._target_wfc

    @property
    def form_instance(self):
        return self._form_inst

    @form_instance.setter
    def form_instance(self, inst):
        self._form_inst = inst

    ################################
    ## Data transformations

    def rawform2forminstance(self):
        if self._raw_formdata is None:
            raise ValueError("No raw form data to process")

        data = self.parser.representation_to_data(self._raw_formdata, SubmissionRO.struct)
        self.form_instance = SubmissionRO(data)

    def source2forminstance(self):
        if not (self._source_wfc and self._source_application):
            raise ValueError("Must provide both source application and workflow control")

        self.form_instance = self.obj2form_xwalk.transform(self._source_wfc, self._source_application)

    def blank_form(self):
        self.form_instance = SubmissionRO()

    def render_form(self):
        form_html = self.serialiser.data_to_string(
            self.form_instance.data,
            self.form_instance.struct,
            application=self._source_application,
            wfc=self._source_wfc
        )
        return form_html