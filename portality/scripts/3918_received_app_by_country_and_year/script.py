from portality import models
from portality.bll import exceptions
import csv
from datetime import datetime

QUERY_BY_YEAR = {
    "track_total_hits": True,
    "query": {
        "bool": {
            "must": [
                {"match_all": {}}
            ],
            "filter": [
                {
                    "range": {
                        "created_date": {
                            "gte": "2021-01-01T00:00:00Z",
                            "lte": "2023-12-31T23:59:59Z"
                        }
                    }
                }
            ]
        }
    },
    "sort": [{"created_date": {"order": "asc"}}],
    "aggs": {
        "applications_by_year": {
            "date_histogram": {
                "field": "created_date",
                "calendar_interval": "year",
                "format": "yyyy",
                "min_doc_count": 0
            }
        }
    }
}

QUERY_BY_COUNTRY = {
    "track_total_hits": True,
    "query": {
        "bool": {
            "must": [
                {"match_all": {}}
            ],
            "filter": [
                {
                    "range": {
                        "created_date": {
                            "gte": "2021-01-01T00:00:00Z",
                            "lte": "2023-12-31T23:59:59Z"
                        }
                    }
                }
            ]
        }
    },
    "sort": [{"bibjson.publisher.country.exact": {"order": "asc"}}],
    "aggs": {
        "applications_by_country": {
            "terms": {
                "field": "bibjson.publisher.country.exact",
                "size": 1000
            }
        }
    }
}


def get_year_from_created_date(created_date):
    # Parse the datetime string and extract the year
    dt = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
    return str(dt.year)


def count_apps_per_year():
    res = models.Application.send_query(QUERY_BY_YEAR)
    buckets = res["aggregations"]["applications_by_year"]["buckets"]
    apps_by_year_count = {bucket['key_as_string']: bucket['doc_count'] for bucket in buckets}
    return apps_by_year_count


def count_apps_per_country():
    res = models.Application.send_query(QUERY_BY_COUNTRY)
    buckets = res["aggregations"]["applications_by_country"]["buckets"]
    apps_by_country_count = {bucket['key']: bucket['doc_count'] for bucket in buckets}
    return apps_by_country_count


def get_metadata(app):
    bibjson = app.bibjson()
    year = str(get_year_from_created_date(app.created_date))
    id = app.id
    title = bibjson.title
    pissn = bibjson.pissn
    eissn = bibjson.eissn
    country = bibjson.publisher_country
    return  {
        "year": year,
        "id": id,
        "title": title,
        "pissn": pissn,
        "eissn": eissn,
        "country": country
    }

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path without extention!", required=True)
    args = parser.parse_args()

    # Output file paths
    output_by_year = args.out + "-by_year.csv"
    output_by_country = args.out + "-by_country.csv"

    apps_by_year_count = count_apps_per_year()
    apps_by_country_count = count_apps_per_country()

    # Initialize CSV writers for both reports
    with open(output_by_year, "w", newline="", encoding="utf-8") as f_by_year, \
            open(output_by_country, "w", newline="", encoding="utf-8") as f_by_country:

        writer_year = csv.writer(f_by_year)
        writer_year.writerow(["ID", "Title", "PISSN", "EISSN", "Country", "Created"])

        writer_country = csv.writer(f_by_country)
        writer_country.writerow(["ID", "Title", "PISSN", "EISSN", "Created", "Country"])

        currently_processed_year = ""
        for app in models.Application.iterate(q=QUERY_BY_YEAR, page_size=100, keepalive='5m'):
            meta = get_metadata(app)
            if (meta["year"] != currently_processed_year):
                currently_processed_year = meta["year"]
                writer_year.writerow(
                    ["YEAR:", currently_processed_year, "COUNT:", str(apps_by_year_count[currently_processed_year])])

            writer_year.writerow([meta["id"], meta["title"], meta["pissn"], meta["eissn"], meta["country"], meta["year"]])

        currently_processed_country = ""
        for app in models.Application.iterate(q=QUERY_BY_COUNTRY, page_size=100, keepalive='5m'):
            meta = get_metadata(app)
            if (meta["country"] != currently_processed_country):
                currently_processed_country = meta["country"]
                writer_country.writerow(["COUNTRY:", currently_processed_country, "COUNT:",
                                         str(apps_by_country_count[currently_processed_country])])

            writer_country.writerow(
                [meta["id"], meta["title"], meta["pissn"], meta["eissn"], meta["year"], meta["country"]])

    print("Reports generated successfully.")
