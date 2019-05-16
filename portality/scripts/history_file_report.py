import os, codecs, json
from portality import clcsv

WORKING_DIR = "/home/richard/tmp/doaj/history/"

BASE_DIRS = [
    "app-1-current", "app-1-old-root-tarball", "bg-app-1-current", "bg-app-1-old-root-tarball",
    "s3-app-1-old", "s3-bg-all-1-old"
]

OUT_DIR = "/home/richard/tmp/doaj/history/"

def history_file_report(working_dir, base_dirs, out_dir):

    journal_out = os.path.join(out_dir, "journals.csv")
    article_out = os.path.join(out_dir, "articles.csv")

    with codecs.open(journal_out, "wb", "utf-8") as j, \
        codecs.open(article_out, "wb", "utf-8") as a:

        jwriter = clcsv.UnicodeWriter(j)
        awriter = clcsv.UnicodeWriter(a)

        jwriter.writerow(["ID", "Date", "Path", "File ID"])
        awriter.writerow(["ID", "Date", "Path", "File ID"])

        for bd in base_dirs:
            dir = os.path.join(working_dir, bd)
            journal_dir = os.path.join(dir, "journal")
            article_dir = os.path.join(dir, "article")

            _walk_history_tree(journal_dir, jwriter)
            _walk_history_tree(article_dir, awriter)

def _walk_history_tree(dir, writer):
    for dirpath, dirnames, filenames in os.walk(dir):
        if len(filenames) > 0:
            for f in filenames:
                fid = f.split(".")[0]
                path = os.path.join(dirpath, f)
                with codecs.open(path, "rb", "utf-8") as g:
                    data = json.load(g)
                    id = data.get("about", "no id")
                date = os.path.basename(dirpath)
                writer.writerow([id, date, path, fid])

if __name__ == "__main__":
    history_file_report(WORKING_DIR, BASE_DIRS, OUT_DIR)