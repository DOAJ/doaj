from formulaic.core import Structure, OPTIONAL, SINGLE, FieldCapability
from formulaic.serialise.form.core import FormCapability, FormObject
from portality.forms.workflow.core import JinjaFormRenderer
from portality.forms.workflow.triage.fields import RecordID
from portality.forms.workflow.triage.fieldsets import EthicsCriteria, ISSN, Database, Website, Content, Admin
from portality.ui import templates

class TriageFormRenderer(JinjaFormRenderer):
    template = templates.WORKFLOW_TRIAGE_FORM

class TriageForm(Structure):
    class TriageFormCapability(FormCapability):
        order = [
            "id",
            "ethics",
            "database",
            "issn",
            "website",
            "content",
            "admin"
        ]
        render_class = TriageFormRenderer

    name_ = "triage"
    capabilities_ = (
        TriageFormCapability(),
    )

    id = RecordID(OPTIONAL, SINGLE)
    ethics = EthicsCriteria(OPTIONAL, SINGLE)
    database = Database(OPTIONAL, SINGLE)
    issn = ISSN(OPTIONAL, SINGLE)
    website = Website(OPTIONAL, SINGLE)
    content = Content(OPTIONAL, SINGLE)
    admin = Admin(OPTIONAL, SINGLE)

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
