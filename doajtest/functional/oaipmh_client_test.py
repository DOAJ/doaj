import requests
from lxml import etree

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
# Plus, this test requires a non-empty index, so providing it with a blank index isn't useful
#from doajtest.bootstrap import prepare_for_test
#prepare_for_test()

NS = "{http://www.openarchives.org/OAI/2.0/}"

JOURNAL_BASE_URL = "http://localhost:5004/oai"
ARTICLE_BASE_URL = "http://localhost:5004/oai.article"

def harvest(base_url, resToken=None):
    url = base_url + "?verb=ListRecords"
    if resToken is not None:
        url += "&resumptionToken=" + resToken
    else:
        url += "&metadataPrefix=oai_dc"

    print "harvesting " + url
    resp = requests.get(url)
    assert resp.status_code == 200, resp.text

    xml = etree.fromstring(resp.text[39:])
    rtel = xml.find(".//" + NS + "resumptionToken")
    if rtel is not None and (rtel.text is not None and rtel.text != ""):
        print "resumption token", rtel.text, "cursor", rtel.get("cursor") + "/" + rtel.get("completeListSize")
        return rtel.text

    print "no resumption token, complete"
    return None

# journals
rt = None
while True:
    rt = harvest(JOURNAL_BASE_URL, rt)
    if rt is None:
        break

# articles
rt = None
while True:
    rt = harvest(ARTICLE_BASE_URL, rt)
    if rt is None:
        break