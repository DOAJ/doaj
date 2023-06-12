import os, json, csv, tarfile, re, shutil

path_regex = "^history/([^/]+)/((\d{4})-\d{2}-\d{2})/(.+)$"
existing_regex = "^([^\/]+)/(\d{4}-\d{2}-\d{2})/(.+)$"

def history_archive(config):
    _extract_and_restructure(config)
    _merge_existing(config)
    _history_dirs_reports(config)
    _create_new_archives(config)


def _merge_existing(config):
    for existing in config.get("existing", []):
        path = os.path.join("existing", existing)
        tf = tarfile.open(path)
        members = tf.getmembers()
        for member in members:
            if not member.isfile():
                continue
            m = re.match(existing_regex, member.name)
            if m is None:
                continue
            outdir = os.path.join("reorg", m[1], m[2])
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            outfile = os.path.join(outdir, m[3])
            if os.path.exists(outfile):
                continue

            extract = tf.extractfile(member)
            with open(outfile, "wb") as out:
                shutil.copyfileobj(extract, out)


def _extract_and_restructure(config):
    if os.path.exists("reorg"):
        os.rmdir("reorg")
    os.makedirs("reorg")

    news = config.get("new", [])
    for new in news:
        path = os.path.join("new", new.get("tar"))
        tf = tarfile.open(path)
        members = tf.getmembers()
        for member in members:
            if not member.isfile():
                continue
            m = re.match(path_regex, member.name)
            if m is None:
                continue
            outdir = os.path.join("reorg", m[1] + "_" + m[3] + "_" + new.get("source"), m[2])
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            extract = tf.extractfile(member)
            outfile = os.path.join(outdir, m[4])
            with open(outfile, "wb") as out:
                shutil.copyfileobj(extract, out)


def _history_dirs_reports(config):
    if os.path.exists("final"):
        os.rmdir("final")
    os.makedirs("final")

    dirs = os.listdir("reorg")
    for dir in dirs:
        fulldir = os.path.join("reorg", dir)
        out = os.path.join("final", dir + ".csv")

        with open(out, "w", encoding="utf-8") as o:
            writer = csv.writer(o)
            writer.writerow(["ID", "Date", "Path", "File ID"])
            _walk_history_tree(fulldir, writer)


def _walk_history_tree(dir, writer):
    for dirpath, dirnames, filenames in os.walk(dir):
        if len(filenames) > 0:
            for f in filenames:
                fid = f.split(".")[0]
                path = os.path.join(dirpath, f)
                report_path = path[len("reorg/"):]
                # check for empty files
                if os.stat(path).st_size > 0:
                    with open(path, "r", encoding="utf-8") as g:
                        data = json.load(g)
                        id = data.get("about", "no id")
                    date = os.path.basename(dirpath)
                    writer.writerow([id, date, report_path, fid])


def _create_new_archives(config):
    if not os.path.exists("final"):
        os.makedirs("final")

    dirs = os.listdir("reorg")
    for dir in dirs:
        source_dir = os.path.join("reorg", dir)
        outfile = os.path.join("final", dir + ".tar.gz")
        with tarfile.open(outfile, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="run configuration")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.loads(f.read())

    history_archive(config)