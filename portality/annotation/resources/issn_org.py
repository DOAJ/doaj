from portality.annotation.resource_bundle import Resource
import requests
import json
from bs4 import BeautifulSoup


class ISSNOrg(Resource):
    __identity__ = "issn_org"

    def make_resource_id(self, issn):
        return self.name() + "_" + issn

    def reference_url(self, issn):
        return "https://portal.issn.org/resource/ISSN/" + issn

    def fetch_fresh(self, issn):
        resp = requests.get(self.reference_url(issn))
        page = BeautifulSoup(resp.text, features="lxml")

        scripts = page.find_all("script", type="application/ld+json")
        if len(scripts) == 0:
            return None

        raw = scripts[0].string
        data = json.loads(raw)
        return data
