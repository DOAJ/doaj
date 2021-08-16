import csv
from copy import deepcopy
from datetime import datetime

import esprit

from portality.core import es_connection
from portality.models import Journal
from portality.settings import BASE_FILE_PATH

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", help="csv with backup data")
    args = parser.parse_args()

    if not args.data:
        print("Please specify a csv data file path with the -d option")
        parser.print_help()
        exit()
        #args.data = BASE_FILE_PATH + "/migrate/2966_add_oa_start_date_from_backup/oa_start_out.csv"

    try:
        f = open(args.data)
    except:
        print("Could not open file: " + args.data + ". Try again.")

    batch = []
    batch_size = 1000
    csv_reader = csv.reader(f)
    header = next(csv_reader)
    if header is not None:
        for row in csv_reader:
            print(row[0])
            j = Journal.pull(row[0])
            if j is not None and "oa_start" not in j["bibjson"]:
                data = j.data
                data["bibjson"]["oa_start"] = row[1]

                batch.append(data)

                if len(batch) >= batch_size:
                    print(datetime.now(), "writing ", len(batch), "to", "journal")
                    esprit.raw.bulk(es_connection, batch, idkey="id", type_="journal", bulk_type="index")
                    batch = []

            if len(batch) > 0:
                print(datetime.now(), "final result set / writing ", len(batch), "to", "journal")
                esprit.raw.bulk(es_connection, batch, idkey="id", type_="journal", bulk_type="index")

    f.close()

