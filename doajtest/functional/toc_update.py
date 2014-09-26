from portality import models
from portality.scripts import toc
import time

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
# Plus, this test requires a non-empty index, so providing it with a blank index isn't useful
#from doajtest.bootstrap import prepare_for_test
#prepare_for_test()

ISSN = "2345-6789"

# create a journal
journal = models.Journal()
jbj = journal.bibjson()
jbj.add_identifier(jbj.P_ISSN, ISSN)
jbj.title = "ToC Journal"
journal.save()
print journal.id

# create some article data
article1 = models.Article()
bj1 = article1.bibjson()
bj1.add_identifier(bj1.P_ISSN, ISSN)
bj1.volume = "1"
bj1.number = "A"
bj1.title = "Article 1"
article1.save()

article2 = models.Article()
bj2 = article2.bibjson()
bj2.add_identifier(bj1.P_ISSN, ISSN)
bj2.volume = "2"
bj2.number = "B"
bj2.title = "Article 2"
article2.save()

article3 = models.Article()
bj3 = article3.bibjson()
bj3.add_identifier(bj1.P_ISSN, ISSN)
bj3.volume = "02"
bj3.number = "C"
bj3.title = "Article 3"
article3.save()

# generate the toc
time.sleep(2)
toc.generate_toc(journal, verbose=True)

# check the volumes in the toc
time.sleep(2)
toc_volumes = models.JournalVolumeToC.list_volumes(journal.id)
print toc_volumes
assert len(toc_volumes) == 3
assert "1" in toc_volumes
assert "2" in toc_volumes
assert "02" in toc_volumes

# update article 3 to normalise the volume names
bj3.volume = "2"
article3.save()

# re-generate the toc
time.sleep(2)
toc.generate_toc(journal, verbose=True)

# re-check the volumes in the toc
time.sleep(2)
toc_volumes = models.JournalVolumeToC.list_volumes(journal.id)
print toc_volumes
assert len(toc_volumes) == 2
assert "1" in toc_volumes
assert "2" in toc_volumes

article1.delete()
article2.delete()
article3.delete()
journal.delete()