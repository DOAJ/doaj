from portality.models import Journal, Application
import csv

if __name__ == "__main__":

    RECORDS = [Journal, Application]
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    out = "out.csv"

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["IN DOAJ", "ID", "DEPOSIT POLICY SERVICES", "TYPE OF RECORD"])
        count = 0
        for record in RECORDS:
            for r in record.iterate():
                dp_services = r.bibjson().deposit_policy
                if dp_services and len(dp_services) > 1:
                    try:
                        if record is Application:
                            field = r.application_type
                        else:
                            field = r.is_in_doaj()
                        writer.writerow([field, r.id, dp_services])
                    except AttributeError:
                        print("Error reading attributes for journal {0}".format(r.id))
