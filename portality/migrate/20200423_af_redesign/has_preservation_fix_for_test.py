import esprit

from portality.core import es_connection
from portality.lib import dates

m = {
    "embed" : "Embed",
    "no" : "No"
}

batch_size = 1000

types = ["doaj-journal", "doaj-application"]

for ct in types:
    batch = []
    for result in esprit.tasks.scroll(es_connection, ct, keepalive="1m", page_size=1000, scan=True):
        preservation_url = result.get("bibjson", {}).get("preservation", {}).get("url")
        services = result.get("bibjson", {}).get("preservation", {}).get("service", [])

        if len(services) == 0 and preservation_url:
            result["bibjson"]["preservation"]["has_preservation"] = False

        batch.append(result)

        if len(batch) >= batch_size:
            print(dates.now(), "writing ", len(batch), "to", ct)
            esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="index")
            batch = []

    if len(batch) > 0:
        print(dates.now(), "final result set / writing ", len(batch), "to", ct)
        esprit.raw.bulk(es_connection, batch, idkey="id", type_=ct, bulk_type="index")
