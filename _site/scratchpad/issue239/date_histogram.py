from portality import models
from datetime import datetime
import csv, requests, urllib.request, urllib.parse, urllib.error, json

query = {
    "query" : { "bool" : {"must" : [{"term" : {"_type" : "article"}}]}},
    "size" : 0,
    "facets" : {
        "monthly" : {
            "date_histogram" : {
                "field" : "created_date",
                "interval" : "month"
            }
        },
        "yearly" : {
            "date_histogram" : {
                "field" : "created_date",
                "interval" : "year"
            }
        }
    }
}

base_url = "http://doaj.org/query/journal,article/_search"
query_url = base_url + "?source=" + urllib.parse.quote_plus(json.dumps(query))
resp = requests.get(query_url)
j = resp.json()

facets = j.get("facets", {})
monthly = facets.get("monthly", {}).get("entries", [])
yearly = facets.get("yearly", {}).get("entries", [])

writer = csv.writer(open("article_creates.csv", "wb"))
writer.writerow(["Date", "Articles Created", "Cumulative Total"])

month_total = 0
for month in monthly:
    count = month.get("count")
    dt = datetime.fromtimestamp(month.get("time")/1000.0)
    month_total += count
    writer.writerow([dt.strftime("%Y-%m-%d"), count, month_total])

writer.writerow([])

year_total = 0
for year in yearly:
    count = year.get("count")
    dt = datetime.fromtimestamp(year.get("time")/1000.0)
    year_total += count
    writer.writerow([dt.strftime("%Y"), count, year_total])

