from formulaic.core import Structure, OPTIONAL, SINGLE, FieldCapability
from formulaic.serialise.form.core import FormCapability, FormObject
from portality.forms.workflow.core import JinjaFormRenderer
from portality.forms.workflow.triage.fields import RecordID
from portality.forms.workflow.triage.fieldsets import EthicsCriteria, ISSN, Database, Website, Content, \
    SpecialException, MetadataReview
from portality.ui import templates

class TriageFormRenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_FORM

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

###################################

# class TriageRORenderer(JinjaFormRenderer):
#     template = templates.WORKFLOW_TRIAGE_READ_ONLY
#
# class TriageRO(Structure):
#     class C(FormCapability):
#         order = [
#             "ethics",
#             "database",
#             "issn",
#             "website",
#             "content",
#             "admin"
#         ]
#
#     name_ = "triage_readonly"
#     capabilities_ = (C(),)
#
#     ethics = EthicsCriteriaRO(OPTIONAL, SINGLE)
#     database = DatabaseRO(OPTIONAL, SINGLE)
#     issn = ISSNRO(OPTIONAL, SINGLE)
#     website = WebsiteRO(OPTIONAL, SINGLE)
#     content = ContentRO(OPTIONAL, SINGLE)
#     admin = AdminRO(OPTIONAL, SINGLE)
#
