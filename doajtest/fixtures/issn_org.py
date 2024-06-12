from copy import deepcopy
from portality.lib import paths

class IssnOrgFixtureFactory(object):
    @classmethod
    def web_page_body(cls):
        source = paths.rel2abs(__file__, "../unit/resources/issn_org_web_page.html")
        with open(source) as f:
            return f.read()