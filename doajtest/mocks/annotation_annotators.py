from portality.autocheck.checker import Checker

class AnnotatorsMockFactory(object):
    @classmethod
    def mock_annotator(cls):
        return MockChecker


class MockChecker(Checker):
    __identity__ = "mock_annotator"

    def check(self, form,
              jla,
              autochecks,
              resources,
              logger):
        autochecks.add_check(field="pissn",
                              original_value="1234-5678",
                              suggested_value="9876-5432",
                              advice="Change the issn",
                              reference_url="http://example.com/9876-5432")
