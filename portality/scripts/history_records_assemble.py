import codecs, os, shutil
from portality import clcsv

ID = "758ee777890a4e2986466d5d3ddd53df"

JOURNAL_CSV = "/home/richard/tmp/doaj/history/journals.csv"

OUT_DIR = "/home/richard/tmp/doaj/history/workspace/"

def history_records_assemble(id, source, out_dir):
    with codecs.open(source, "rb", "utf-8") as f:
        reader = clcsv.UnicodeReader(f)
        for row in reader:
            if row[0] == id:
                fn = row[1] + "_" + row[3]
                out = os.path.join(out_dir, fn)
                shutil.copy(row[2], out)

if __name__ == "__main__":
    history_records_assemble(ID, JOURNAL_CSV, OUT_DIR)