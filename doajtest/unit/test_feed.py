import time

from doajtest.helpers import DoajTestCase
from portality import models
from portality.view import atom
from lxml import etree


class TestFeed(DoajTestCase):

    def test_01_object(self):
        # first try requesting a feed over the empty test index
        f = atom.get_feed("http://my.test.com")
        assert len(f.entries.keys()) == 0
        assert f.url == "http://my.test.com"

        # now populate the index and then re-get the feed
        ids = []
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_subject("LCC", "Agriculture")
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            ids.append(j.id)

            # make sure the last updated dates are suitably different
            time.sleep(1)

        time.sleep(1)

        with self.app_test.test_request_context('/feed'):
            f = atom.get_feed("http://my.test.com")
        assert len(f.entries.keys()) == 5

        # now go through the entries in order, and check they are as expected
        entry_dates = f.entries.keys()

        for i in range(5):
            e = f.entries.get(sorted(entry_dates)[i])[0]
            assert e["author"] == "Test Publisher {x}".format(x=i)
            assert len(e["categories"]) == 1
            assert e["categories"][0] == "LCC:Agriculture"
            assert e["content_src"].endswith("{x}000-0000?rss".format(x=i))
            assert e["alternate"].endswith("{x}000-0000?rss".format(x=i))
            assert e["id"] == "urn:uuid:" + ids[i]
            assert e["related"] == "http://homepage.com/{x}".format(x=i)
            assert "rights" in e
            assert e["summary"].startswith("Published by Test Publisher {x}".format(x=i))
            assert e["title"] == "Test Journal {x} ({x}000-0000)".format(x=i)
            assert "updated" in e

    def test_02_xml(self):
        # now populate the index and then re-get the feed
        ids = []
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_subject("LCC", "Agriculture")
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            ids.append(j.id)

            # make sure the last updated dates are suitably different
            time.sleep(1)

        time.sleep(1)

        with self.app_test.test_request_context('/feed'):
            f = atom.get_feed("http://my.test.com")
        s = f.serialise()

        xml = etree.fromstring(s)
        entries = xml.findall("{http://www.w3.org/2005/Atom}entry")

        for i in range(5):
            inv = 4 - i
            e = entries[i]
            assert e.xpath("atom:author/atom:name", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].text == "Test Publisher {x}".format(x=inv)
            assert e.xpath("atom:content", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].get("src").endswith("{x}000-0000?rss".format(x=inv))
            assert e.xpath("atom:id", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].text == "urn:uuid:" + ids[inv]
            assert e.xpath("atom:link[@rel='alternate']", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].get("href").endswith("{x}000-0000?rss".format(x=inv))
            assert e.xpath("atom:link[@rel='related']", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].get("href") == "http://homepage.com/{x}".format(x=inv)
            assert e.xpath("atom:category", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].get("term") == "LCC:Agriculture"
            assert e.xpath("atom:summary", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].text.startswith("Published by Test Publisher {x}".format(x=inv))
            assert e.xpath("atom:title", namespaces={'atom': 'http://www.w3.org/2005/Atom'})[0].text == "Test Journal {x} ({x}000-0000)".format(x=inv)
