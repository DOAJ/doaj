from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal

class ModelArticleMockFactory(object):

    @classmethod
    def get_journal(cls, specs):
        journals = []

        for spec in specs:
            source = JournalFixtureFactory.make_journal_source(in_doaj=True)
            j = Journal(**source)
            bj = j.bibjson()
            bj.title = spec.get("title", "Journal Title")
            bj.remove_identifiers()
            if "pissn" in spec:
                bj.add_identifier(bj.P_ISSN, spec.get("pissn"))
            if "eissn" in spec:
                bj.add_identifier(bj.E_ISSN, spec.get("eissn"))
            spec["instance"] = j
            journals.append(spec)

        def mock(self):
            bibjson = self.bibjson()

            # first, get the ISSNs associated with the record
            pissns = bibjson.get_identifiers(bibjson.P_ISSN)
            eissns = bibjson.get_identifiers(bibjson.E_ISSN)

            for j in journals:
                if j["pissn"] in pissns and j["eissn"] in eissns:
                    return j["instance"]

        return mock

    @classmethod
    def save(self, filename="filename.xml", stream=None):

        self.filename = filename
        self.stream = stream

        def mock(self, path):
            with open(path, "wb") as f:
                f.write(self.stream.read())

        return mock
