from portality import models, clcsv
import codecs
from portality.core import app

# list the accounts which meet the criteria of having one or more journals in doaj
journal_accounts = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.in_doaj" : True}}
            ]
        }
    },
    "size" : 0,
    "aggs" : {
        "accs" : {
            "terms" : {
                "field" : "admin.owner.exact",
                "size" : 0
            }
        }
    }
}

# list the accounts which meet the criteria of having one ore more applications in the status "reapplication"
reapp_accounts = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.application_status.exact" : "reapplication"}}
            ]
        }
    },
    "size" : 0,
    "aggs" : {
        "accs" : {
            "terms" : {
                "field" : "admin.owner.exact",
                "size" : 0
            }
        }
    }
}

def do_report(out):
    # list the accounts which meet the criteria of having one or more journals in doaj
    jresp = models.Journal.query(q=journal_accounts)
    jaccs = [agg.get("key") for agg in jresp.get("aggregations", {}).get("accs", {}).get("buckets", []) if agg.get("doc_count") < 11]
    print "{x} accounts with between 1 and 10 journals in the DOAJ".format(x=len(jaccs))

    # list the accounts which meet the criteria of having one ore more applications in the status "reapplication"
    rresp = models.Suggestion.query(q=reapp_accounts)
    raccs = [agg.get("key") for agg in rresp.get("aggregations", {}).get("accs", {}).get("buckets", [])]
    print "{x} accounts with at least one outstanding reapplication".format(x=len(raccs))

    # get the intersection of those lists, and pull the email address from the index to make the final list
    with codecs.open(out, "wb", "utf-8") as f:
        writer = clcsv.UnicodeWriter(f, encoding="utf-8")
        writer.writerow(["Account ID", "Email"])
        counter = 0
        for acc in raccs:
            if acc in jaccs:
                counter += 1
                am = models.Account.pull(acc)
                if am is not None:
                    writer.writerow([acc, am.email])
                else:
                    writer.writerow([acc, u"No corresponding account record found"])
    print "{x} accounts appear in both lists".format(x=counter)


if __name__ == "__main__":

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with -o"
        exit()

    do_report(args.out)