from copy import deepcopy

from formulaic.serialise.form.core import FormSerialiser, FormDataParser, GenericFormStructureCapability, \
    FormFieldCapability
from portality.bll import DOAJ
from portality.bll.services.workflow.core import ApplicationEdit
from portality.core import app
from portality.forms.workflow.crosswalk import TriageForm2WorkflowControl, WorkflowControl2TriageForm
from portality.forms.workflow.triage.fields import SpecialExceptions
from portality.forms.workflow.triage.forms import TriageForm, TriageSubmission
from portality.models import Application, WorkflowControl
from formulaic.core import DataProcessingResult, ErrorCode, Structure, Field
from portality.models.workflow import TriageField, SpecialExceptionTriageField


# class TriageReadOnlyProcessor:
#     def __init__(self, source_application:Application, source_wfc:WorkflowControl):
#         self._source_application = source_application
#         self._source_wfc = source_wfc
#
#         self.obj2form_xwalk = WorkflowControl2TriageForm()
#         self.serialiser = FormSerialiser(context_id = "triage-ro")
#
#         self._form_inst:TriageSubmission = None
#
#         if self._source_application and self._source_wfc:
#             self.source2forminstance()
#
#     ################################
#     ## accessors
#
#     @property
#     def source_application(self):
#         return self._source_application
#
#     @property
#     def source_workflow_control(self):
#         return self._source_wfc
#
#     @property
#     def form_instance(self):
#         return self._form_inst
#
#     @form_instance.setter
#     def form_instance(self, inst):
#         self._form_inst = inst
#
#     ################################
#     ## Data transformations
#
#     def source2forminstance(self):
#         if not (self._source_wfc and self._source_application):
#             raise ValueError("Must provide both source application and workflow control")
#
#         self.form_instance = self.obj2form_xwalk.transform(self._source_wfc, self._source_application)
#
#     ##########################
#     ## Form serialisation
#
#     def render_form(self):
#         form_html = self.serialiser.data_to_string(
#             self.form_instance.data,
#             self.form_instance.struct,
#             application=self._source_application,
#             wfc=self._source_wfc,
#             errors=self.form_instance.validation_result
#         )
#         return form_html

class TriageFormProcessor:
    def __init__(self, source_application:Application, source_wfc:WorkflowControl, raw_formdata:dict=None):
        self._source_application = source_application
        self._source_wfc = source_wfc
        self._raw_formdata = raw_formdata

        self.form2obj_xwalk = TriageForm2WorkflowControl()
        self.obj2form_xwalk = WorkflowControl2TriageForm()
        self.serialiser = FormSerialiser(context_id = "triage-form")
        self.parser = FormDataParser()

        self._form_inst:TriageSubmission = None
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

        data = self.parser.representation_to_data(self._raw_formdata, TriageSubmission.struct)
        self.form_instance = TriageSubmission(data)

    def source2forminstance(self):
        if not (self._source_wfc and self._source_application):
            raise ValueError("Must provide both source application and workflow control")

        self.form_instance = self.obj2form_xwalk.transform(self._source_wfc, self._source_application)

    def forminstance2target(self, account):
        partial_wfc, partial_application = self.form2obj_xwalk.transform(self._form_inst, account)
        self._target_application = self._patch_application(partial_application)
        self._target_wfc = self._patch_wfc(partial_wfc)
        self._rationalise_answers(self._target_wfc)
        self._calculate_recommendation(self._target_wfc)

    def blank_form(self):
        self.form_instance = TriageSubmission()

    ################################
    ## Form submission methods

    def pre_validate(self):
        pass

    def validate(self):
        if self.form_instance is None:
            raise ValueError("No form instance to validate")

        self.pre_validate()
        return self.form_instance.validate()

    def finalise(self, account):
        self.forminstance2target(account)

        wfSvc = DOAJ.workflowService()
        state = wfSvc.state_for_workflow_control(self._target_wfc, self._target_application)
        if state is None:
            raise ValueError(f"No valid workflow state found for workflow control with id '{self._target_wfc.id}'")

        # May raise an AuthoriseExeption
        new_state = state.do(ApplicationEdit(account))

        self._target_application.save()
        self._target_wfc.save()

    ################################
    ## Internal processing methods

    def _patch_wfc(self, partial_wfc:WorkflowControl) -> WorkflowControl:
        target = WorkflowControl(**deepcopy(self._source_wfc.data))

        # this patcher completely overwrites the triage portion of the workflowcontrol
        # if the updates are more partial than that, then we need to accommodate

        # transfer the triage object entirely
        target.triage = partial_wfc.triage

        # transfer any notes the workflow control object knows about
        target.cache_notes(partial_wfc.cached_notes)

        return target

    def _patch_application(self, partial_application:Application) -> Application:
        target = Application(**deepcopy(self._source_application.data))
        tbj = target.bibjson()
        sbj = partial_application.bibjson()

        # this patcher assumes all the metadata have been provided by the partial.
        # If it's possible a partial won't have that info, then we need to update this to
        # accommodate

        # EISSN/PISSN
        tbj.eissn = sbj.eissn
        tbj.pissn = sbj.pissn

        # Title
        tbj.title = sbj.title

        # Continuation
        tbj.replaces = sbj.replaces

        # License information
        tbj.remove_licenses()
        for lic in sbj.licenses:
            tbj.add_license_obj(lic)
        tbj.license_terms_url = sbj.license_terms_url

        # Copyright
        tbj.author_retains_copyright = sbj.author_retains_copyright
        tbj.copyright_url = sbj.copyright_url

        return target

    def _rationalise_answers(self, wfc:WorkflowControl):
        t = wfc.triage
        R = app.cms.workflow.triage.fields

        for question in R.keys():
            triage_field = getattr(t, question)
            ans = triage_field.answer

            if "severity_value" in R[question]:
                if ans in R[question].severity_value:
                    triage_field.severity_value = R[question].severity_value[ans]

            if ans in R[question].compliant_answers:
                triage_field.compliant = True
            elif ans in R[question].non_compliant_answers:
                triage_field.compliant = False
            else:
                triage_field.compliant = None

    def _calculate_recommendation(self, wfc:WorkflowControl):
        t = wfc.triage
        R = app.cms.workflow.triage.fields

        def get_recommendation(field:TriageField, config):
            if "recommend" in config:
                if field.answer is not None and field.answer in config.recommend:
                    recommend = config.recommend[field.answer]
                    return [{
                        "code": recommend,
                        "reasons": {
                            "question": field.name,
                            "answer": field.answer,
                            "sv": field.severity_value,
                            "exception": None,
                        }
                    }]
            if isinstance(field, SpecialExceptionTriageField):
                if len(field.special_exceptions) > 0:
                    return [{
                        "code": "reject",
                        "reasons": {
                            "question": field.name,
                            "answer": field.answer,
                            "sv": field.severity_value,
                            "exception": field.special_exceptions,
                        }
                    }]

            return []

        recs = []

        for question in R.keys():
            recs += get_recommendation(getattr(t, question), R[question])

        def evaluate_recommendations(recs):
            r = []
            qf = []
            for rec in recs:
                if rec["code"] == "reject":
                    r.append(rec["reasons"])
                elif rec["code"] == "quick_fail":
                    qf.append(rec["reasons"])
            return r, qf

        reject, quick_fail = evaluate_recommendations(recs)

        if len(reject) > 0:
            t.recommend("reject", reject)
            return

        if len(quick_fail) > 0:
            t.recommend("quick_fail", quick_fail)
            return

        severity = t.get_fields_with_non_zero_severity_value()
        report = [
            {
                "question": s.name,
                "answer": s.answer,
                "sv": s.severity_value,
                "exception": s.exception
            }
            for s in severity
        ]
        sv_total = t.total_severity_value

        if sv_total < 3:
            t.recommend("normal", report)
        elif sv_total < 10:
            t.recommend("maned", report)
        else:
            t.recommend("integrity_ethics", report)

    ##########################
    ## Form serialisation

    def render_form(self):
        form_html = self.serialiser.data_to_string(
            self.form_instance.data,
            self.form_instance.struct,
            application=self._source_application,
            wfc=self._source_wfc,
            errors=self.form_instance.validation_result
        )
        return form_html

    def validation_report(self):
        def code2msg(error_code:ErrorCode, field):
            # field = error_code.error.field
            if isinstance(field, Structure):
                field = field.ref_

            cap = None
            if field.has_capability(GenericFormStructureCapability):
                cap = field.get_capability(GenericFormStructureCapability)
            elif field.has_capability(FormFieldCapability):
                cap = field.get_capability(FormFieldCapability)

            msg = cap.error_message(error_code)
            return msg

        # get the raw validation dict
        d = self.form_instance.validation_result.as_dict(code2msg)

        # enhance it for form usage
        if "errors" not in d:
            return d

        for e in d["errors"]:
            e["field_id"] = self.serialiser.make_id(self.form_instance.struct, e["path"], e["data_context"])
            if "relevant_to" in e:
                for r in e["relevant_to"]:
                    r["field_id"] = self.serialiser.make_id(self.form_instance.struct, r["path"])

        # now let's flatten it to make it simpler for the front end
        f = []
        for e in d["errors"]:
            if "msg" in e["code"] and e["code"]["msg"] != "":
                f.append({
                    "field_id": e["field_id"],
                    "code": e["code"]
                })

            for rt in e.get("relevant_to", []):
                if "msg" in rt["code"] and rt["code"]["msg"] != "":
                    f.append({
                        "field_id": rt["field_id"],
                        "code": rt["code"]
                    })

        m = {
            "valid": d["valid"],
            "errors": f,
            "full_error_trace": d["errors"]
        }

        return m

    def recommendation(self, workflow_control:WorkflowControl=None):
        if workflow_control is None:
            workflow_control = self.target_workflow_control
        if workflow_control is None:
            return None

        rec = workflow_control.triage.recommendation
        if rec is None:
            return None

        localised = []
        for entry in rec.get("reasons", []):
            reference = self.obj2form_xwalk.structure_map(entry["question"])
            if reference is None:
                continue

            label = entry["question"]
            path = None
            if isinstance(reference, Structure):
                label = reference.ref_.get_capability(GenericFormStructureCapability).label
                path = reference.ref_.path
            elif isinstance(reference, Field):
                label = reference.get_capability(FormFieldCapability).label
                path = reference.path

            field_id = self.serialiser.make_id(self.form_instance.struct, path)

            localised.append({
                "question": {
                    "name": entry["question"],
                    "field_id": field_id,
                    "text": label
                },
                "answer": entry.get("answer"),
                "sv": entry.get("sv"),
                "exception": entry.get("exception")
            })

        return {"code": rec.get("code"), "reasons": localised}

