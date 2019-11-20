import json
import time
import re
from collections import OrderedDict

from doajtest.helpers import DoajTestCase
from portality import models
from portality.upgrade import do_upgrade
from portality.lib.paths import rel2abs

def operation(journal):
    j = models.Journal.pull(journal.id)
    bj = j.bibjson()
    bj.title = "Updated Title"
    j.save()
    return j


class TestUpgrade(DoajTestCase):

    def test_upgrade(self):
        # populate the index with some journals with title
        saved_journals = {}
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal"
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            saved_journals[j.id] = j.last_updated


        # and with some journals without title
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.add_identifier(bj.P_ISSN, "{x}000-0001".format(x=i))
            bj.title = "Journal to Change"
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            saved_journals[j.id] = j.last_updated

        # make sure the last updated dates will be suitably different after migration
        time.sleep(1.5)

        path =rel2abs(__file__, ".", "resources", "migrate.json")
        with open(path) as f:
            instructions = json.loads(f.read(), object_pairs_hook=OrderedDict)
        do_upgrade(instructions,None)

        p = re.compile('[0-4]000-0001')

        for id in saved_journals:
            j = models.journal.Journal.pull(id)
            bj = j.bibjson()
            pissn = bj.get_one_identifier(bj.P_ISSN)

            if not p.match(pissn):
                assert bj.title == "Test Journal"
                assert j.last_updated == saved_journals[j.id]

            else:
                assert bj.title == "Updated Title"
                assert not j.last_updated == saved_journals[j.id]










