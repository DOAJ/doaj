from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal

class ModelArticleMockFactory(object):

    @classmethod
    def get_journal(cls, specs, in_doaj=True):
        journals = []

        for spec in specs:
            j = JournalFixtureFactory.make_legacy_journal_object(in_doaj=in_doaj)
            bj = j.bibjson()
            bj.title = spec.get("title", "Journal Title")
            del bj.eissn
            del bj.pissn
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

