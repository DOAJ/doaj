import doajtest  # runs the __init__.py which runs the tests bootstrap code. All tests should import this.
from unittest import TestCase
from portality import dao

class TestWorkflow(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generic_csv(self):
        data = {'col1': 2, 'col2': 'string', 'keywords': ['hoppity', 'hop', 'hop 2']}
        o = dao.DomainObject(**data)
        # expect alphabetic order of keys
        expected = ['2', 'string', 'hoppity,hop,hop 2']
        result = o.csv()
        assert result == expected  # You can compare lists: [1,2,3] != [1,3,2] but [1,2,3] == [1,2,3]
