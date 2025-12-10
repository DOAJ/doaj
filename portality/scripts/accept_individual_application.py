from portality.bll import DOAJ
from portality import models
from portality.lib.thread_utils import wait_until

ID = "9ede8319c58b40238dcf52210649fe29"
USER = "richard"

app = models.Application.pull(ID)
acc = models.Account.pull(USER)

applicationSvc = DOAJ.applicationService()
journal = applicationSvc.accept_application(app, acc)

wait_until(lambda: models.Journal.pull(journal.id) is not None, timeout=5)
print("Created journal:", journal.id)
