import csv
from datetime import datetime

import esprit

from portality.core import es_connection
from portality.models import Journal
from portality.util import ipt_prefix


def reinstate_oa_start(csv_reader):
    """ Write the OA start date into Journals from the CSV file containing rows of id,oa_start_date """

    batch = []
    batch_size = 1000
    header = next(csv_reader)
    if header is not None:
        for row in csv_reader:
            j = Journal.pull(row[0])
            if j is not None and "oa_start" not in j["bibjson"]:
                j.bibjson().oa_start = row[1]
                batch.append({'doc': j.data})

                if len(batch) >= batch_size:
                    print('{0}, writing {1} to {2}'.format(datetime.now(), len(batch), ipt_prefix('journal')))
                    r = esprit.raw.bulk(es_connection, batch, idkey="doc.id", type_=ipt_prefix("journal"), bulk_type="update")
                    assert r.status_code == 200, r.json()
                    batch = []

        if len(batch) > 0:
            print('{0}, final result set / writing {1} to {2}'.format(datetime.now(), len(batch), ipt_prefix('journal')))
            r = esprit.raw.bulk(es_connection, batch, idkey="doc.id", type_=ipt_prefix("journal"), bulk_type="update")
            assert r.status_code == 200, r.json()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", help="csv with backup data", required=True)
    args = parser.parse_args()

    try:
        with open(args.data) as f:
            reinstate_oa_start(csv.reader(f))
    except Exception as e:
        print("Could not process file: " + args.data + ". Error: " + str(e))
        raise
