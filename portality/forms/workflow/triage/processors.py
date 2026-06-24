from formulaic import engine
from formulaic.serialise.form.core import FormSerialiser, FormDataParser
from portality.core import app
from portality.forms.workflow.crosswalk import TriageForm2WorkflowControl, WorkflowControl2TriageForm
from portality.forms.workflow.triage.forms import TriageForm, TriageSubmission
from portality.models import Application, WorkflowControl
from formulaic.core import DataProcessingResult


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
        self._validation_report:DataProcessingResult = None

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
            form_html = self.serialiser.data_to_string(
                                self._form_inst.data,
                                self._form_inst.struct,
                                application=self._source_application,
                                wfc=self._source_wfc,
                                errors=self._validation_report)
            return form_html
        elif self._source_wfc or self._source_application:
            raise ValueError("Must provide both source application and workflow control, or neither")
        else:
            form_html = self.serialiser.data_to_string({}, TriageSubmission.struct, application=Application(), wfc=WorkflowControl())
            return form_html

    def validate(self):
        if self._raw_formdata is None:
            raise ValueError("No raw form data to process")

        data = self.parser.representation_to_data(self._raw_formdata, TriageSubmission.struct)
        self._form_inst = TriageSubmission(data)
        self._validation_report = engine.validate(data, TriageSubmission.struct)
        if self._validation_report.is_valid:
            return True
        return False

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

    def _rationalise_answers(self, wfc:WorkflowControl):
        t = wfc.triage
        R = app.cms.workflow.triage.fields

        def set_compliance(complyable, rule_source):
            if complyable.answer in rule_source.compliant_answers:
                complyable.compliant = True
            elif complyable.answer in rule_source.non_compliant_answers:
                complyable.compliant = False
            else:
                complyable.compliant = None

        # First compute all the compliance booleans from the supplied answers
        set_compliance(t.ethics_not_excluded, R.ethics_not_excluded)
        set_compliance(t.ethics_no_nonstandard_metrics, R.ethics_no_nonstandard_metrics)
        set_compliance(t.ethics_no_fake_impact, R.ethics_no_fake_impact)
        set_compliance(t.ethics_no_false_doaj_claim, R.ethics_no_false_doaj_claim)
        set_compliance(t.ethics_no_suspicious_ties, R.ethics_no_suspicious_ties)
        set_compliance(t.issn_at_least_one, R.issn_at_least_one)

        def set_severity(complyable, rule_source):
            if rule_source.severity_value and not complyable.compliant:
                complyable.severity_value = rule_source.severity_value

        # Next apply severity values (only to ethics criteria)
        set_severity(t.ethics_not_excluded, R.ethics_not_excluded)
        set_severity(t.ethics_no_nonstandard_metrics, R.ethics_no_nonstandard_metrics)
        set_severity(t.ethics_no_fake_impact, R.ethics_no_fake_impact)
        set_severity(t.ethics_no_false_doaj_claim, R.ethics_no_false_doaj_claim)
        set_severity(t.ethics_no_suspicious_ties, R.ethics_no_suspicious_ties)

        # TODO: exceptions

    def finalise(self, account):
        self._rationalise_answers(self._target_wfc)
        # TODO: workflow binding
