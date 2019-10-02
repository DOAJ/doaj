import requests, time
from lxml import etree
from datetime import datetime, timedelta

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
# Plus, this test requires a non-empty index, so providing it with a blank index isn't useful
#from doajtest.bootstrap import prepare_for_test
#prepare_for_test()

NS = "{http://www.openarchives.org/OAI/2.0/}"

JOURNAL_BASE_URL = "http://localhost:5004/oai"
ARTICLE_BASE_URL = "http://localhost:5004/oai.article"

# Rate limit the requests (number per second or 0 to disable)
RATE_LIMIT = 0

if RATE_LIMIT > 0:
    req_period = timedelta(seconds=1 / RATE_LIMIT)
else:
    req_period = timedelta()
last_req = datetime.min

IDENTS = []

def harvest(base_url, res_token=None):
    url = base_url + "?verb=ListRecords"
    if res_token is not None:
        url += "&resumptionToken=" + res_token
    else:
        url += "&metadataPrefix=oai_dc"

    # Apply our rate limiting for requests
    now = datetime.utcnow()
    global last_req
    if now - last_req < req_period:
        time.sleep((req_period - (now - last_req)).total_seconds())

    print ("harvesting " + url)
    last_req = now
    resp = requests.get(url)
    assert resp.status_code == 200, resp.text

    xml = etree.fromstring(resp.text[39:])

    records = xml.findall(".//" + NS + "record")
    for record in records:
        oai_id = record.find(".//" + NS + "identifier").text
        if oai_id in IDENTS:
            print ("DUPLICATE ID: " + oai_id)
            return None
        IDENTS.append(oai_id)

    rtel = xml.find(".//" + NS + "resumptionToken")
    if rtel is not None:
        if rtel.text is not None and rtel.text != "":
            print ("\tresumption token", rtel.text, "cursor", rtel.get("cursor") + "/" + rtel.get("completeListSize"))
            print ("\tresults received: ", len(IDENTS))
            return rtel.text
        else:
            print ("\tno resumption token, complete. cursor", rtel.get("cursor") + "/" + rtel.get("completeListSize"))
    else:
        print ("no results")
        return None


# journals
rt = None
while True:
    rt = harvest(JOURNAL_BASE_URL, rt)
    if rt is None:
        break

IDENTS = []

# articles
rt = None
while True:
    rt = harvest(ARTICLE_BASE_URL, rt)
    if rt is None:
        break
