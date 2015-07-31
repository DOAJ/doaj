from portality import models
from portality.api.v1.data_objects import journal

#jm = models.Journal.pull('6080c97800d54efeb6dbe4b60e437f29')
jm = models.Journal.pull('e52d9e100f5147edbf65b756f1e9bab6')
j = journal.JournalDO.from_model(jm)

print j.bibjson

print 'la'