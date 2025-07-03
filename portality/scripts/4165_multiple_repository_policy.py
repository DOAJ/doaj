from portality.models import Journal
import csv

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["IN DOAJ", "ID", "DEPOSIT POLICY SERVICES"])
        count = 0
        for j in Journal.iterate():
            dp_services = j.bibjson().deposit_policy
            if len(dp_services) > 1:
                print(dp_services)
                try:
                    writer.writerow([j.is_in_doaj(), j.id, dp_services])
                except AttributeError:
                    print("Error reading attributes for journal {0}".format(j['id']))
