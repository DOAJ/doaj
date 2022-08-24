import requests, time
from lxml import etree
from datetime import datetime, timedelta

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
# Plus, this test requires a non-empty index, so providing it with a blank index isn't useful
#from doajtest.bootstrap import prepare_for_test
#prepare_for_test()

NS = "{http://www.openarchives.org/OAI/2.0/}"

def harvest(base_url, verb="ListRecords", metadata_prefix="oai_dc", rate_limit=0, last_req=None, res_token=None, idents=None):
    url = base_url + "?verb=" + verb
    if res_token is not None:
        url += "&resumptionToken=" + res_token
    else:
        url += "&metadataPrefix=" + metadata_prefix

    if rate_limit > 0:
        req_period = timedelta(seconds=1 / rate_limit)
    else:
        req_period = timedelta()

    if last_req is None:
        last_req = datetime.min

    if idents is None:
        idents = []

    # Apply our rate limiting for requests
    now = datetime.utcnow()
    if now - last_req < req_period:
        time.sleep((req_period - (now - last_req)).total_seconds())

    print("harvesting " + url)
    resp = requests.get(url)
    assert resp.status_code == 200, resp.text

    xml = etree.fromstring(resp.text[39:])

    records = xml.findall(".//" + NS + "record")
    for record in records:
        oai_id = record.find(".//" + NS + "identifier").text
        if oai_id in idents:
            print("DUPLICATE ID: " + oai_id)
            return None
        idents.append(oai_id)

    rtel = xml.find(".//" + NS + "resumptionToken")
    if rtel is not None:
        if rtel.text is not None and rtel.text != "":
            print("\tresumption token", rtel.text, "cursor", rtel.get("cursor") + "/" + rtel.get("completeListSize"))
            print("\tresults received: ", len(idents))
            return rtel.text
        else:
            print("\tno resumption token, complete. cursor", rtel.get("cursor") + "/" + rtel.get("completeListSize"))
    else:
        print("no results")
        return None


RUN_CONFIGURATION = {
    "base_url": "https://doaj.org/",
    "rate_limit": 0,
    "endpoints" : [
        {
            "endpoint": "oai",
            "verb": "ListRecords",
            "metadataPrefix": "oai_dc"
        },
        {
            "endpoint": "oai.article",
            "verb": "ListRecords",
            "metadataPrefix": "oai_dc"
        },
        {
            "endpoint": "oai.article",
            "verb": "ListRecords",
            "metadataPrefix": "oai_doaj"
        }
    ]
}


def run(config):
    for endpoint in config.get("endpoints", []):
        rt = None
        last_req=None
        idents = []
        while True:
            request_time = datetime.utcnow()
            rt = harvest(
                config.get("base_url") + endpoint.get("endpoint"),
                verb=endpoint.get("verb", "ListRecords"),
                metadata_prefix=endpoint.get("metadataPrefix", "oai_dc"),
                rate_limit=config.get("rate_limit"),
                last_req=last_req,
                res_token=rt,
                idents=idents
            )
            last_req = request_time

            if rt is None:
                break


if __name__ == "__main__":
    run(RUN_CONFIGURATION)