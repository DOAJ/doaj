from portality.bll.services.workflow.core import State
from portality.models import WorkflowControl

##################################
## Cancelled state definition values

MODULE_CANCELLED = "cancelled"
MODULE_CANCELLED_STAGE_CANCELLED = "cancelled"

##################################
## Rejected state definition(s)

class Cancelled(State):
    module = MODULE_CANCELLED
    stage = MODULE_CANCELLED_STAGE_CANCELLED
    reviewer = WorkflowControl.ANY