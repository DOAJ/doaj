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
        if _empty(row):
            last_row_empty = True
            continue

        if _test_title(row) and last_row_empty:
            if len(current_test.keys()) > 0:
                tests.append(current_test)
            current_test = {"title": row[2], "context" : {"role" : ""}, "steps": []}
        else:   # this is a regular test row
            if len(current_test.keys()) == 0:
                raise Exception("Attempt to add step before test is initialised")

            if row[1]:
                current_test["context"]["role"] = row[1]
            if row[2]:
                if len(current_step.keys()) > 0:
                    current_test["steps"].append(current_step)
                current_step = {"step": row[2]}
            if row[3]:
                if "results" not in current_step:
                    current_step["results"] = []
                current_step["results"].append(row[3])

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


migrate("/home/richard/tmp/doaj/Dashboard - Editorial Group Status.csv",
        "/home/richard/Code/External/doaj3/doajtest/testbook/dashboard/editorial_group_status.yml",
        "Editor Search",
        "Journals")