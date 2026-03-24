from portality.lib import plugin
import random
import string
from portality import models


class TestDrive():
    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    def generate_unique_issn(self):
        while True:
            s = self.create_random_str(n_char=8)
            issn = s[:4] + '-' + s[4:]
            if len(models.Journal.find_by_issn(issn)) == 0 :
                return issn

    def setup(self) -> dict:
        return {"status": "not implemented"}

    def teardown(self, setup_params) -> dict:
        return {"status": "not implemented"}


class TestFactory():
    @classmethod
    def get(cls, test_id):
        modname = test_id
        classname = test_id.replace("_", " ").title().replace(" ", "")
        classpath = "doajtest.testdrive." + modname + "." + classname
        klazz = plugin.load_class(classpath)
        return klazz()