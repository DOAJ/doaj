from formulaic.core import Structure, OPTIONAL, SINGLE, FieldCapability, REPEATABLE, Field, REQUIRED
from formulaic.serialise.form.core import FormCapability, FormObject, CompoundFieldCapability
from portality.forms.workflow.core import JinjaFormRenderer
from portality.forms.workflow.triage.fields import RecordID
from portality.forms.workflow.triage.fieldsets import EthicsCriteria, ISSN, Database, Website, Content, \
    SpecialException, MetadataReview
from portality.ui import templates

class TriageFormRenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_FORM

class TriageFormRORenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_RO_FORM

class TriageForm(Structure):
    class TriageFormCapability(FormCapability):
        order = [
            "id",
            "special_exception",
            "ethics",
            "issn",
            "database",
            "website",
            "content",
            "metadata_review"
        ]
        render_class = TriageFormRenderer

        alt_render = {
            "ro": {
                "render_class": TriageFormRORenderer
            }
        }

    name_ = "triage"
    capabilities_ = (
        TriageFormCapability(),
    )

    id = RecordID(OPTIONAL, SINGLE)
    special_exception = SpecialException(OPTIONAL, SINGLE)
    ethics = EthicsCriteria(OPTIONAL, SINGLE)
    issn = ISSN(OPTIONAL, SINGLE)
    database = Database(OPTIONAL, SINGLE)
    website = Website(OPTIONAL, SINGLE)
    content = Content(OPTIONAL, SINGLE)
    metadata_review = MetadataReview(OPTIONAL, SINGLE)

class TriageSubmission(FormObject):
    struct = TriageForm()

