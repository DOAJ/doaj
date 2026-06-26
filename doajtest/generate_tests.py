from combinatrix.testintegration import load_parameter_sets
from portality.lib.paths import rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "matrices", "tasks.public_data_dump"), "data_dump", "test_id",
                               {"test_id": []})

STUB = rel2abs(__file__, "matrices", "tasks.public_data_dump", "stub.py")
OUT = rel2abs(__file__, "matrices", "tasks.public_data_dump", "test_tasks_public_data_dump.py")

tests = ""
for case in load_cases():
    num = case[0].zfill(3)
    tests += f"""
    def test_{num}(self):
        self.run_test({case[1]})
        """

with open(STUB, "r") as f:
    stub = f.read()
    stub += "\n\n"
    stub += tests

with open(OUT, "w") as f:
    f.write(stub)