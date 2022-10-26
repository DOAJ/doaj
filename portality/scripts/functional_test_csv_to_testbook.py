import csv, yaml, os


def migrate(infile, outfile, suite, testset):
    with open(infile, "r") as f:
        reader = csv.reader(f)
        rows = [row for row in reader]
    rows = rows[1:]

    last_row_empty = False
    tests = []
    current_test = {}
    current_step = {}
    for row in rows:
        if _empty(row) or _note_row(row):
            last_row_empty = True
            continue

        if _test_title(row) and last_row_empty:
            if len(current_test.keys()) > 0:
                tests.append(current_test)
            current_test = {"title": row[2].strip(), "context" : {"role" : ""}, "steps": []}
        else:   # this is a regular test row
            if len(current_test.keys()) == 0:
                raise Exception("Attempt to add step before test is initialised")

            if row[1]:
                current_test["context"]["role"] = row[1].strip()
            if row[2]:
                if len(current_step.keys()) > 0:
                    current_test["steps"].append(current_step)
                current_step = {"step": row[2].strip()}
            if row[3]:
                if "results" not in current_step:
                    current_step["results"] = []
                current_step["results"].append(row[3].strip())

        last_row_empty = False

    if len(current_step.keys()) > 0:
        current_test["steps"].append(current_step)
    if len(current_test.keys()) > 0:
        tests.append(current_test)

    testset = {
        "suite": suite,
        "testset": testset,
        "tests": tests
    }

    outdir = os.path.dirname(outfile)
    os.makedirs(outdir, exist_ok=True)
    with open(outfile, "w") as f:
        yaml.safe_dump(testset, stream=f, sort_keys=False)


def _test_title(row):
    return row[1] == "" and row[2] != "" and row[3] == ""


def _empty(row):
    return row[0] == "" and row[1] == "" and row[2] == "" and row[3] == ""


def _note_row(row):
    return row[0] != "" and row[1] == "" and row[2] == "" and row[3] == ""


def migrate_all(indir, outdir):
    for fn in os.listdir(indir):
        print(fn)
        rawname = fn[:-1 * len(".csv")]
        suite, testset = rawname.split(" - ")
        path = os.path.join(indir, fn)
        subpath = os.path.join(_safe_name(suite), _safe_name(testset) + ".yml")
        out = os.path.join(outdir, subpath)
        migrate(path, out, suite, testset)


def _safe_name(name):
    return name.lower().replace(" ", "_")


# migrate("/home/richard/tmp/doaj/functionaltests/Admin Article Metadata Form - Admin Article Metadata Form.csv",
#         "/home/richard/Code/External/doaj3/doajtest/testbook/admin_article_metadata_form/admin_article_metadata_form.yml",
#         "Admin Article Metadata Form",
#         "Admin Article Metadata Form")

migrate_all("/home/richard/tmp/doaj/functionaltests", "/home/richard/Code/External/doaj3/doajtest/testbook/migration/")