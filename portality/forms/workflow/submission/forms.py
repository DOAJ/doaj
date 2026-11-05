from formulaic.core import Structure, SINGLE, OPTIONAL
from formulaic.serialise.form.core import FormObject, FormCapability
from portality.forms.workflow.core import JinjaFormRenderer
from portality.forms.workflow.submission.fieldsets import AboutTheJournal, OACompliance, CopyrightLicensing, Editorial, \
    BestPractices, BusinessModel
from portality.ui import templates


class SubmissionFormRORenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_RO_FORM    # Re-using this as they are used in the same context

class SubmissionROForm(Structure):
    class SubmissionFormCapability(FormCapability):
        order = [
            "oa_compliance",
            "about_the_journal",
            "copyright_licensing",
            "editorial",
            "business_model",
            "best_practices"
        ]
        render_class = SubmissionFormRORenderer

    name_ = "submission_ro"
    capabilities_ = (
        SubmissionFormCapability(),
    )

    oa_compliance = OACompliance(OPTIONAL, SINGLE)
    about_the_journal = AboutTheJournal(OPTIONAL, SINGLE)
    copyright_licensing = CopyrightLicensing(OPTIONAL, SINGLE)
    editorial = Editorial(OPTIONAL, SINGLE)
    business_model = BusinessModel(OPTIONAL, SINGLE)
    best_practices = BestPractices(OPTIONAL, SINGLE)

class SubmissionRO(FormObject):
    struct = SubmissionROForm()