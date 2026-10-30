from portality import constants
from portality.bll import DOAJ
from portality.bll.services.workflow.core import State
from portality.models import Account, WorkflowControl

##################################
## Rejected state definition values

MODULE_REJECTED = "rejected"
MODULE_REJECTED_STAGE_REJECTED = "rejected"

##################################
## Rejected state definition(s)

class Rejected(State):
    module = MODULE_REJECTED
    stage = MODULE_REJECTED_STAGE_REJECTED
    reviewer = WorkflowControl.ANY

    def apply(self):
        # Ensure the workflow control object is in the right state
        wf_control = self.workflow_control
        if wf_control.module != self.module:
            wf_control.module = self.module

        if wf_control.stage != self.stage:
            wf_control.stage = self.stage

        # back-compatibility for the original workflow
        application = self.application

        if application.application_status != constants.APPLICATION_STATUS_REJECTED:
            appSvc = DOAJ.applicationService()
            acc = None
            if wf_control.reviewer_id is not None:
                acc = Account.pull(wf_control.reviewer_id)
            if acc is None:
                # FIXME: what's the way to do this?
                acc = Account.pull("system")
            appSvc.reject_application(application, acc)

        application.remove_editor_group()

        if wf_control.reviewer_id is not None:
            if application.editor != wf_control.reviewer_id:
                application.set_editor(wf_control.reviewer_id)
        else:
            application.remove_editor()