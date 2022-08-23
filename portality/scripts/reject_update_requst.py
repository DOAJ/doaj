from portality.models import Application
from portality.constants import APPLICATION_STATUS_REJECTED

UR_TO_REJECT = "5742fbfb237f4b38a7b58d54951727d6"

if __name__ == "__main__":
    ur = Application.pull(UR_TO_REJECT)
    ur.set_application_status(APPLICATION_STATUS_REJECTED)
    ur.save()
