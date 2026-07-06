from formulaic.core import Structure, OPTIONAL, SINGLE
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
    capabilities_ = (TriageFormCapability(),)

    id = RecordID(OPTIONAL, SINGLE)
    ethics = EthicsCriteria(OPTIONAL, SINGLE)
    database = Database(OPTIONAL, SINGLE)
    issn = ISSN(OPTIONAL, SINGLE)
    website = Website(OPTIONAL, SINGLE)
    content = Content(OPTIONAL, SINGLE)
    admin = Admin(OPTIONAL, SINGLE)

class TriageSubmission(FormObject):
    struct = TriageForm()