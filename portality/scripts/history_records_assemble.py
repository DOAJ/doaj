import os, shutil, tarfile, json, csv
from portality import clcsv

# I have not included jsondiff in the requiremets for the app, as I don't think that we'll stick
# with this long-term, as there is a more standard specification out there, and for some reason this
# library doesn't conform to it.  Does for the time being, if you are using this script you just need
# to pip install it.
from jsondiff import diff, symbols

ID = "530ee48c2e31475eb4afd82581fd9710"

ASSEMBLE = True
DIFF = True

CSV_DIR = "/home/richard/tmp/doaj/history.20200306"

TAR_DIR = "/home/richard/tmp/doaj/history.20200306/history"

OUT_DIR = "/home/richard/tmp/doaj/history.20200306/workspace/"


def history_records_assemble(id, csv_dir, tar_dir, out_dir, assemble, do_diff):

    if assemble:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir)

        csvs = [c for c in os.listdir(csv_dir) if c.endswith(".csv")]
        paths = []

        # find all the files from the index csvs
        for c in csvs:
            tarname = c.rsplit(".", 1)[0] + ".tar.gz"
            with open(os.path.join(csv_dir, c), "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] == id:
                        paths.append({
                            "csv" : c,
                            "tarname" : tarname,
                            "tarpath" : row[2],
                            "date" : row[1],
                            "fileid" : row[3]
                        })

        # gather all the files in the target directory
        with open(os.path.join(out_dir, "_index." + id + ".csv"), "w", encoding="utf-8") as g:
            writer = csv.writer(g)
            writer.writerow(["CSV", "Tar Name", "Tar Path", "Date", "File ID"])
            for p in paths:
                tarball = tarfile.open(os.path.join(tar_dir, p["tarname"]), "r:gz")
                try:
                    member = tarball.getmember(p["tarpath"])
                except KeyError:
                    p["tarpath"] = p["tarpath"][1:] if p["tarpath"].startswith("/") else p["tarpath"]
                    member = tarball.getmember(p["tarpath"])

                handle = tarball.extractfile(member)
                out = os.path.join(out_dir, p["date"] + "_" + p["fileid"] + ".json")
                with open(out, "wb") as f:
                    shutil.copyfileobj(handle, f)
                writer.writerow([p["csv"], p["tarname"], p["tarpath"], p["date"], p["fileid"]])

    if do_diff:
        difffile = os.path.join(out_dir, "_diff." + id + ".json")
        if os.path.exists(difffile):
            os.remove(difffile)

        # order the files and diff them into a single summary file
        # FIXME: note that this is not the standardised form of jsondiff, for some reason, but it
        # will do for now.
        changes = []
        files = [f for f in os.listdir(out_dir) if f.endswith(".json")]
        files.sort()
        for i in range(len(files) - 1):
            f1 = files[i]
            f2 = files[i + 1]
            with open(os.path.join(out_dir, f1), "r", encoding="utf-8") as r1, \
                    open(os.path.join(out_dir, f2), "r", encoding="utf-8") as r2:
                j1 = json.loads(r1.read())
                j2 = json.loads(r2.read())
                d = diff(j1, j2)
                d["_from"] = f1
                d["_to"] = f2
                d = _fix_symbols(d)
                changes.append(d)

        with open(difffile, "w", encoding="utf-8") as o:
            try:
                o.write(json.dumps(changes, indent=2, sort_keys=True))
            except TypeError:
                print(changes)
                raise


def _fix_symbols(data):
    def fix_layer(d):
        if not isinstance(d, dict):
            return d
        newData = {}
        for k, v in d.items():
            if isinstance(k, symbols.Symbol):
                newData[repr(k)] = v
            else:
                newData[k] = v
        return newData

    def recurse(d):
        if not isinstance(d, dict):
            return d
        d = fix_layer(d)
        for k, v in list(d.items()):
            d[k] = recurse(d[k])
        return d

    return recurse(data)


if __name__ == "__main__":
    history_records_assemble(ID, CSV_DIR, TAR_DIR, OUT_DIR, ASSEMBLE, DIFF)