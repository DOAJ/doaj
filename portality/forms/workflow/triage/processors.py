from copy import deepcopy

from formulaic import engine
from formulaic.serialise.form.core import FormSerialiser, FormDataParser
from portality.bll import DOAJ
from portality.bll.services.workflow.core import ApplicationEdit
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
        set_compliance(t.database_withdrawn, R.database_withdrawn)
        set_compliance(t.database_withdrawn_exception_ignore_embargo, R.database_withdrawn_exception_ignore_embargo)
        set_compliance(t.database_withdrawn_exception_website_unavailable, R.database_withdrawn_exception_website_unavailable)
        set_compliance(t.database_withdrawn_exception_content, R.database_withdrawn_exception_content)
        set_compliance(t.database_embargo, R.database_embargo)
        set_compliance(t.database_embargo_exception_issn, R.database_embargo_exception_issn)
        set_compliance(t.database_embargo_exception_maned, R.database_embargo_exception_maned)
        set_compliance(t.database_embargo_exception_website, R.database_embargo_exception_website)
        set_compliance(t.database_embargo_exception_content, R.database_embargo_exception_content)
        set_compliance(t.database_not_listed, R.database_not_listed)
        set_compliance(t.database_not_duplicate, R.database_not_duplicate)
        set_compliance(t.issn_at_least_one, R.issn_at_least_one)
        set_compliance(t.issn_title_match, R.issn_title_match)
        set_compliance(t.issn_continuation, R.issn_continuation)
        set_compliance(t.website_working, R.website_working)
        set_compliance(t.website_issn, R.website_issn)
        set_compliance(t.website_url, R.website_url)
        set_compliance(t.website_license_policy, R.website_license_policy)
        set_compliance(t.website_copyright, R.website_copyright)
        set_compliance(t.content_no_login, R.content_no_login)
        set_compliance(t.content_no_embargo, R.content_no_embargo)
        set_compliance(t.content_publish_enough, R.content_publish_enough)
        set_compliance(t.content_unique_link, R.content_unique_link)
        set_compliance(t.content_format, R.content_format)
        set_compliance(t.content_new_journal, R.content_new_journal)
        set_compliance(t.admin_metadata_review, R.admin_metadata_review)
        set_compliance(t.admin_special_exception, R.admin_special_exception)

        def set_exception(exceptable, rule_source):
            if exceptable.answer in rule_source.exception_answers:
                exceptable.exception = True
            else:
                exceptable.exception = False

        set_exception(t.database_withdrawn_exception_ignore_embargo, R.database_withdrawn_exception_ignore_embargo)
        set_exception(t.database_withdrawn_exception_website_unavailable, R.database_withdrawn_exception_website_unavailable)
        set_exception(t.database_withdrawn_exception_content, R.database_withdrawn_exception_content)
        set_exception(t.database_embargo_exception_issn, R.database_embargo_exception_issn)
        set_exception(t.database_embargo_exception_maned, R.database_embargo_exception_maned)
        set_exception(t.database_embargo_exception_website, R.database_embargo_exception_website)
        set_exception(t.database_embargo_exception_content, R.database_embargo_exception_content)

        def set_severity(complyable, rule_source):
            if "severity_value" in rule_source and complyable.compliant is False:
                complyable.severity_value = rule_source.severity_value

        # Next apply severity values
        set_severity(t.ethics_no_nonstandard_metrics, R.ethics_no_nonstandard_metrics)
        set_severity(t.ethics_no_fake_impact, R.ethics_no_fake_impact)
        set_severity(t.ethics_no_false_doaj_claim, R.ethics_no_false_doaj_claim)
        set_severity(t.ethics_no_suspicious_ties, R.ethics_no_suspicious_ties)

    def render_form(self):
        form_html = self.serialiser.data_to_string(
            self.form_instance.data,
            self.form_instance.struct,
            application=self._source_application,
            wfc=self._source_wfc,
            errors=self.form_instance.validation_result
        )
        return form_html
