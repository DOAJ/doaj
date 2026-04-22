from portality.lib import plugin
import random
import string
from portality import models


class TestDrive:
    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    @staticmethod
    def generate_unique_issn():
        """ Generate a unique -and valid- ISSN that isn't already present, by checking the index """

        while True:
            digits = [random.randint(0, 9) for _ in range(7)]
            checksum = (11 - sum(v * w for v, w in zip(digits, range(8, 1, -1))) % 11) % 11
            s = ''.join(map(str, digits))
            issn = f"{s[:4]}-{s[4:]}{'X' if checksum == 10 else checksum}"

            # Look in the index to check whether this is unique.
            if len(models.Journal.find_by_issn(issn)) == len(models.Application.find_by_issn(issn)) == 0:
                return issn

    def setup(self) -> dict:
        return {"status": "not implemented"}

    def teardown(self, setup_params) -> dict:
        return {"status": "not implemented"}


class TestFactory:
    @classmethod
    def get(cls, test_id):
        modname = test_id
        classname = test_id.replace("_", " ").title().replace(" ", "")
        classpath = "doajtest.testdrive." + modname + "." + classname
        klazz = plugin.load_class(classpath)
        return klazz()
