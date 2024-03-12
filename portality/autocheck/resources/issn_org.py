from datetime import datetime

from portality.autocheck.resource_bundle import Resource
from portality.core import app

import requests
import json
import time
from bs4 import BeautifulSoup


class ISSNOrg(Resource):
    __identity__ = "issn_org"

    def __init__(self, resource_bundle):
        super(ISSNOrg, self).__init__(resource_bundle)
        self._timeout = app.config.get("AUTOCHECK_RESOURCE_ISSN_ORG_TIMEOUT", 10)
        self._throttle = app.config.get("AUTOCHECK_RESOURCE_ISSN_ORG_THROTTLE", 0)
        self._last_request = None

    def make_resource_id(self, issn):
        return self.name() + "_" + issn

    def reference_url(self, issn):
        return "https://portal.issn.org/resource/ISSN/" + issn

    def fetch_fresh(self, issn):
        if self._last_request is not None:
            now = datetime.utcnow()
            since_last = (now - self._last_request).total_seconds()
            if since_last < self._throttle:
                time.sleep(self._throttle - since_last)

        resp = requests.get(self.reference_url(issn), timeout=self._timeout)
        self._last_request = datetime.utcnow()

        page = BeautifulSoup(resp.text, features="lxml")

        scripts = page.find_all("script", type="application/ld+json")
        if len(scripts) == 0:
            return None

        raw = scripts[0].string
        data = json.loads(raw)
        return ISSNOrgData(data)


class ISSNOrgData(object):
    def __init__(self, raw):
        self.data = raw

    @property
    def version(self):
        return self.data.get("mainEntityOfPage", {}).get("version")

    def is_registered(self):
        return self.version == "Register"

    @property
    def archive_components(self):
        return [ac for ac in self.data.get("subjectOf", []) if ac.get("@type") == "ArchiveComponent"]
