import csv

from portality import models

if __name__ == "__main__":

    with open('NO OA Date - Sheet1.csv', mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = []
        row_url = 3
        row_pissn = 4
        row_eissn = 2
        row_oa_start = 7
        row_count = 0
        for row in csv_reader:
            rows.append(row)

        for row in rows:
            if row_count < 2:
                row_count += 1
            else:
                # extract id
                address = "https://doaj.org/toc/"
                address_length = len(address)
                jid = row[row_url][address_length:]

                # find journal
                j = models.Journal.pull(jid)
                if j is not None:
                    jbib = j.bibjson()
                    # validate with pissn and eissn (always at least one exists and is checked with the data)
                    if (jbib.pissn and jbib.pissn != row[row_pissn]) or (jbib.eissn and jbib.eissn != row[row_eissn]):
                        print("PISSN/EISSN mismatch with journal id for row " + str(row_count) + ". Pissn provided: " + row[row_pissn] + ", pissn of journal: " + jbib.pissn + ", eissn provided: " + row[row_eissn] + ", eissn of journal: " + jbib.eissn)
                    else:
                        jbib.oa_start = int(row[row_oa_start])
                        j.save(blocking=True)
                        print("OA Start date " + str(jbib.oa_start) + " saved for journal: " + jid)
                else:
                    print("Journal not found: " + jid + ", row: " + str(row_count))
                row_count += 1

