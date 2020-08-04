import esprit
from portality.core import app, es_connection
from portality import models
from datetime import datetime

m = {
    "embed" : "Embed",
    "no" : "No"
}

batch_size = 1000

types = ["doaj-journal", "doaj-application"]

for ct in types:
    batch = []
    for result in esprit.tasks.scroll(es_connection, ct, keepalive="1m", page_size=1000, scan=True):
        ld = result.get("bibjson", {}).get("article", {}).get("license_display")
        if ld is not None:
            ld = [m.get(x, x) for x in ld]
            result["bibjson"]["article"]["license_display"] = ld
        batch.append(result)

        if len(batch) >= batch_size:
            print(datetime.now(), "writing ", len(batch), "to", ct)
            esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="update")
            batch = []

    if len(batch) > 0:
        print(datetime.now(), "final result set / writing ", len(batch), "to", ct)
        esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="update")
