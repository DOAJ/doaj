import csv
import requests

from portality.core import app

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()
    out = args.out

    if not args.out:
        print("The output not specified, saving to oa_start_out.csv")
        out = "oa_start_out.csv"

    headers = {
        'Authorization': 'Basic ' + app.config.get("AUTHORIZATION_CODE"),
        'Content-Type': 'text/plain',
    }

    data = '{ "_source": ["bibjson.oa_start", "admin.in_doaj"], "query": { "filtered": { "filter": { "exists" : { "field" : "bibjson.oa_start" } }, "query": { "match_all": {} } } }, "size": 200000 }'

    response = requests.post('https://doajes.cottagelabs.com/doaj/journal/_search', headers=headers, data=data)

    js = response.json()
    hits = js["hits"]["hits"]

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "OA Start Date", "In doaj?"])

        for h in hits:
            try:
                in_doaj = h["_source"]["admin"]["in_doaj"]
            except KeyError:
                in_doaj = ""
            writer.writerow([h["_id"], h["_source"]["bibjson"]["oa_start"]["year"], in_doaj])


