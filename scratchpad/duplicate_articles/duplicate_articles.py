import codecs, csv
from portality import clcsv

IN = "/home/richard/tmp/article_duplicates_2018-05-22/duplicate_articles_global_2018-05-22.csv"

GENUINE = "/home/richard/tmp/article_duplicates_2018-05-22/genuine_duplicates.csv"
BAD_DATA = "/home/richard/tmp/article_duplicates_2018-05-22/bad_data.csv"

def _to_dict(header, row):
    d = {}
    for i, h in enumerate(header):
        d[h] = row[i]
    return d

unique_ids = []
unique_deduplicated = []
genuine_unique_ids = []
genuine_unique_deduplicated = []
bad_data_unique_ids = []
bad_data_unique_deduplicated = []
genuine_count = 0
bad_data_count = 0

with codecs.open(GENUINE, "wb", "utf-8") as a:
    awriter = csv.writer(a)

    with codecs.open(BAD_DATA, "wb", "utf-8") as b:
        bwriter = csv.writer(b)

        with codecs.open(IN, "rb", "utf-8") as f:
            reader = csv.writer(f)

            headers = next(reader)
            awriter.writerow(headers)
            bwriter.writerow(headers)

            i = 0
            for row in reader:
                print(i)
                i += 1

                data = _to_dict(headers, row)
                aid = data["article_id"]
                mid = data["match_id"]

                if aid not in unique_ids:
                    unique_ids.append(aid)
                if aid not in unique_deduplicated:
                    unique_deduplicated.append(aid)
                if mid not in unique_ids:
                    unique_ids.append(mid)

                titles_match = data["titles_match"] == "True"
                owners_match = data["owners_match"] == "True"
                issns_match = sorted(data["match_issns"].split(",")) == sorted(data["article_issns"].split(","))

                if titles_match and owners_match and issns_match:
                    genuine_count += 1
                    awriter.writerow(row)
                    if aid not in genuine_unique_ids:
                        genuine_unique_ids.append(aid)
                    if aid not in genuine_unique_deduplicated:
                        genuine_unique_deduplicated.append(aid)
                    if mid not in genuine_unique_ids:
                        genuine_unique_ids.append(mid)
                else:
                    bad_data_count += 1
                    bwriter.writerow(row)

                    if aid not in bad_data_unique_ids:
                        bad_data_unique_ids.append(aid)
                    if aid not in bad_data_unique_deduplicated:
                        bad_data_unique_deduplicated.append(aid)
                    if mid not in bad_data_unique_ids:
                        bad_data_unique_ids.append(mid)



print(("Total articles engaged in duplication: " + str(len(unique_ids))))
print(("Total articles that would remain after de-duplication: " + str(len(unique_deduplicated))))

print(("Total estimated genuine duplication pairs: " + str(genuine_count)))
print(("Total estimated articles engaged in genuine duplication: " + str(len(genuine_unique_ids))))
print(("Total estimated articles that would remain from genuine duplication after de-duplication: " + str(len(genuine_unique_deduplicated))))

print(("Total estimated bad data duplication pairs: " + str(bad_data_count)))
print(("Total estimated articles engaged in 'bad data' duplication: " + str(len(bad_data_unique_ids))))
print(("Total estimated articles that would remain from 'bad data' duplication after de-duplication: " + str(len(bad_data_unique_deduplicated))))

