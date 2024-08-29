from portality import models
from portality.bll import exceptions
import csv
from datetime import datetime

QUERY = {
        "track_total_hits": True,
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "admin.application_type.exact": "new_application"
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "created_date": {
                                "gte": "2019-01-01T00:00:00Z",
                                "lte": "2023-12-31T23:59:59Z"
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "applications_by_country": {
                "aggs": {
                    "applications_by_year": {
                        "date_histogram": {
                            "field": "created_date",
                            "calendar_interval": "year",
                            "format": "yyyy",
                            "min_doc_count": 0
                        }
                    }
                },
                "terms": {
                    "field": "index.country.exact",
                    "size": 1000
                }
            }
        }
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file", required=True)
    args = parser.parse_args()

    # Initialize CSV writers for both reports
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Country", "Year", "Count"])

        res = models.Application.send_query(QUERY)
        country_buckets = res["aggregations"]["applications_by_country"]["buckets"]

        def get_country(country_bucket):
            return country_bucket["key"]

        def get_years_data(country_bucket):
            return country_bucket["applications_by_year"]["buckets"]

        def get_year(year_bucket):
            return year_bucket["key_as_string"]

        def get_count(year_bucket):
            return year_bucket["doc_count"]


        for country_bucket in country_buckets:
            years_buckets = get_years_data(country_bucket)
            for years_bucket in years_buckets:
                writer.writerow([get_country(country_bucket), get_year(years_bucket), get_count(years_bucket)])

    print("Reports generated successfully.")
