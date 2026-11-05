"""Generate test files from parameter matrices.

Usage:
    python generate_tests.py [matrix_dir] [bundle_name] [run_test import path] [outdir]

matrix_dir: directory under matrices to read (default: "tasks.public_data_dump")
bundle_name: bundle name to load parameter sets for (default: "data_dump")
"""

import argparse, json, re
from combinatrix.testintegration import load_parameter_sets
from portality.lib.paths import rel2abs

def load_cases(matrix_dir, bundle):
    return load_parameter_sets(rel2abs(__file__, "matrices", matrix_dir), bundle, "test_id", {"test_id": []})


def main():
    p = argparse.ArgumentParser(description="Generate tests from combinatrix matrices")
    p.add_argument("matrix_dir", nargs="?", default="tasks.public_data_dump",
                   help="directory under matrices to read (e.g. 'tasks.public_data_dump')")
    p.add_argument("bundle", nargs="?", default="data_dump", help="bundle name to load parameter sets for")
    p.add_argument("import_path", nargs="?", default="", help="import for run_test function")
    p.add_argument("outdir", nargs="?", default="", help="directory to write the test to")
    args = p.parse_args()

    matrix_dir = args.matrix_dir
    bundle = args.bundle
    # convert bundle to CapWords (PascalCase) for use in class names
    bundle_cap = "".join([p.capitalize() for p in re.split(r'[^0-9A-Za-z]+', bundle) if p])
    outdir = args.outdir
    import_path = args.import_path



    # output paths
    out_filename = f"test_{bundle}.py"
    out_path = rel2abs(__file__, "unit", outdir, out_filename)

    tests = f"""
from doajtest.helpers import DoajTestCase
from {import_path} import run_test 

class Test{bundle_cap}(DoajTestCase):
    """
    for case in load_cases(matrix_dir, bundle):
        num = case[0].zfill(3)
        args = json.dumps(case[1], indent=2)
        tests += f"""
    def test_{num}(self):
        run_test({args})
        """

    with open(out_path, "w") as f:
        f.write(tests)


if __name__ == "__main__":
    main()
