from portality.lib import plugin
import random
import string


class TestDrive():
    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

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