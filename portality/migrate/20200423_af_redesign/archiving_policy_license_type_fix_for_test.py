import esprit
from portality.core import app, es_connection
from portality import models
from datetime import datetime

known_licenses = [
    "CC BY",
    "CC BY-NC",
    "CC BY-NC-ND",
    "CC BY-NC-SA",
    "CC BY-ND",
    "CC BY-SA",
    "CCO",
    "Public domain"
]

batch_size = 1000

types = ["doaj-journal", "doaj-application"]

for ct in types:
    batch = []
    for result in esprit.tasks.scroll(es_connection, ct, keepalive="1m", page_size=1000, scan=True):

        if len(result.get("bibjson", {}).get("preservation", {}).get("service", [])) == 0:
            if "preservation" not in result["bibjson"]:
                result["bibjson"]["preservation"] = {}
            result["bibjson"]["preservation"]["has_preservation"] = False

        for lic in result.get("bibjson", {}).get("license", []):
            if lic.get("type") not in known_licenses:
                lic["type"] = "Publisher's own license"

        batch.append(result)

        if len(batch) >= batch_size:
            print(datetime.now(), "writing ", len(batch), "to", ct)
            esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="index")
            batch = []

    if len(batch) > 0:
        print(datetime.now(), "final result set / writing ", len(batch), "to", ct)
        esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="index")
