from portality import models
from portality.api.v1.data_objects import journal

jm = models.Journal.pull('6080c97800d54efeb6dbe4b60e437f29')
j = journal.JournalDO.from_model(jm)

print 'la'