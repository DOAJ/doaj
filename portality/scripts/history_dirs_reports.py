import os, codecs, json, csv

WORKING_DIR = "/home/richard/tmp/doaj/history/archive/"

BASE_DIRS = [
    "article_2016_web-pre2019",
    "article_2017_background-pre2019",
    "article_2018_background-pre2019",
    "article_2018_web-pre2019",
    "article_2019_background-2019",
    "article_2019_background-pre2019",
    "article_2019_web-2019",
    "article_2019_web-pre2019",
    "journal_2016_background-pre2019",
    "journal_2017_background-pre2019",
    "journal_2017_web-pre2019",
    "journal_2018_background-pre2019",
    "journal_2018_web-pre2019",
    "journal_2019_background-2019",
    "journal_2019_background-pre2019",
    "journal_2019_web-pre2019"
]

OUT_DIR = "/home/richard/tmp/doaj/history/archive/"


def history_dirs_reports(working_dir, base_dirs, out_dir):
    for bd in base_dirs:
        out = os.path.join(out_dir, bd + ".csv")

        with codecs.open(out, "wb", "utf-8") as o:
            writer = csv.writer(o)
            writer.writerow(["ID", "Date", "Path", "File ID"])
            dir = os.path.join(working_dir, bd)
            _walk_history_tree(dir, writer, working_dir)


def _walk_history_tree(dir, writer, working_dir):
    for dirpath, dirnames, filenames in os.walk(dir):
        if len(filenames) > 0:
            for f in filenames:
                fid = f.split(".")[0]
                path = os.path.join(dirpath, f)
                report_path = path[len(working_dir):]
                with codecs.open(path, "rb", "utf-8") as g:
                    data = json.load(g)
                    id = data.get("about", "no id")
                date = os.path.basename(dirpath)
                writer.writerow([id, date, report_path, fid])


if __name__ == "__main__":
    history_dirs_reports(WORKING_DIR, BASE_DIRS, OUT_DIR)