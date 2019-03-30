from portality.lib import report_to_csv

QUERY = {
    "query": {
        "filtered" : {
            "query" : {"match_all" : {}},
            "filter" : {
                "bool" : {
                    "should" : [
                        {"missing" : {"field" : "bibjson.apc_url"}},
                        {"missing" : {"field" : "bibjson.submission_charges_url"}}
                    ]
                }
            }
        }
    }
}

HEADERS = ["ID", "Journal Name", "ISSNs", "Q14", "Q18"]

def output_map(record):
    return {
        "ID" : record.get("id"),
        "Journal Name" : record.get("bibjson", {}).get("title"),
        "ISSNs" : ", ".join(record.get("index", {}).get("issn", [])),
        "Q14" : str(record.get("bibjson", {}).get("apc_url") is not None),
        "Q18" : str(record.get("bibjson", {}).get("submission_charges_url") is not None)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("You must provide an output file with -o")
        exit(0)

    gen = report_to_csv.query_result_generator(QUERY, "journal")
    report_to_csv.report_to_csv(gen, HEADERS, output_map, args.out)