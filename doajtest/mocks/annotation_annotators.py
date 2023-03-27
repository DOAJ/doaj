from portality.annotation.annotator import Annotator

class AnnotatorsMockFactory(object):
    @classmethod
    def mock_annotator(cls):
        return MockAnnotator


class MockAnnotator(Annotator):
    __identity__ = "mock_annotator"

    def annotate(self, form,
                        jla,
                        annotations,
                        resources,
                        logger):
        annotations.add_annotation(field="pissn",
                                   original_value="1234-5678",
                                   suggested_value="9876-5432",
                                   advice="Change the issn",
                                   reference_url="http://example.com/9876-5432")
