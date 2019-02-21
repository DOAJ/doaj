import codecs
from copy import deepcopy
from portality import clcsv

duplicate_report = "/home/richard/tmp/doaj/article_duplicates_2019-02-12/duplicate_articles_global_2019-02-12.csv"
noids_report = "/home/richard/tmp/doaj/article_duplicates_2019-02-12/noids_2019-02-12.csv"
out = "/home/richard/tmp/doaj/article_duplicates_2019-02-12/out.csv"

def analyse(duplicate_report, noids_report, out):
    with codecs.open(out, "wb", "utf-8") as o:
        with codecs.open(duplicate_report, "rb", "utf-8") as f:
            reader = clcsv.UnicodeReader(f)
            headers = reader.next()
            next_row = None
            while True:
                match_set, next_row = _read_match_set(reader, next_row)
                ids = [m["id"] for m in match_set["matches"]]
                o.write("--" + ",".join(ids) + "\n\n")
                if next_row is None:
                    break

def _read_match_set(reader, next_row):
    root = None
    match_set = {"type" : None, "matches" : []}
    while True:
        if next_row is not None:
            row = deepcopy(next_row)
            next_row = None
        else:
            try:
                row = reader.next()
            except StopIteration:
                return match_set, None

        if row is None:
            return match_set, None

        a_id = row[0]
        if root is not None and a_id != root["id"]:
            return match_set, row

        a_created = row[1]
        a_doi = row[2]
        a_ft = row[3]
        a_owner = row[4]
        a_issns = row[5]
        a_in_doaj = row[6]

        match_type = row[8]

        b_id = row[9]
        b_created = row[10]
        b_doi = row[11]
        b_ft = row[12]
        b_owner = row[13]
        b_issns = row[14]
        b_in_doaj = row[15]

        title_match = row[17]

        if match_set["type"] is None:
            match_set["type"] = match_type

        if root is None:
            root = {
                "id" : a_id,
                "created": a_created,
                "doi" : a_doi,
                "fulltext" : a_ft,
                "owner" : a_owner,
                "issns" : a_issns,
                "in_doaj" : a_in_doaj,
                "title_match" : title_match
            }
            match_set["matches"].append(root)

        match = {
            "id" : b_id,
            "created": b_created,
            "doi" : b_doi,
            "fulltext" : b_ft,
            "owner" : b_owner,
            "issns" : b_issns,
            "in_doaj" : b_in_doaj,
            "title_match" : title_match
        }
        match_set["matches"].append(match)

analyse(duplicate_report, noids_report, out)
