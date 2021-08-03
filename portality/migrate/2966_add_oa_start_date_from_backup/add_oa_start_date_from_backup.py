import csv
from copy import deepcopy

from portality.models import Journal
from portality.settings import BASE_FILE_PATH

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        args.out = "out.txt"
        # print("Please specify an output file path with the -o option")
        # parser.print_help()
        # exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Journal ID', 'OA Start Date'])

        f = open(BASE_FILE_PATH + "/migrate/2966_add_oa_start_date_from_backup/oa_start_out.csv")
        csv_reader = csv.reader(f)
        header = next(csv_reader)
        if header is not None:
            for row in csv_reader:
                print(row)
                j = Journal.pull(row[0])
                if j is not None:
                    j.bibjson().oa_start = row[1]
                    j.save()
                    writer.writerow([j.id, j.bibjson().oa_start])
        f.close()

