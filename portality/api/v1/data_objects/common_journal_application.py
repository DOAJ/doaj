from copy import deepcopy

from portality.lib import dataobj, swagger

class OutgoingCommonJournalApplication(dataobj.DataObj, swagger.SwaggerSupport):

    @classmethod
    def from_model(cls, journal_or_app):
        d = deepcopy(journal_or_app.data)

        # we need to re-write the archiving policy section
        joa = d.get("bibjson", {}).get("archiving_policy")
        if joa is not None:
            njoa = {}
            if "url" in joa:
                njoa["url"] = joa["url"]
            if "policy" in joa:
                npol = []
                for pol in joa["policy"]:
                    if isinstance(pol, list):
                        npol.append({"name" : pol[1], "domain" : pol[0]})
                    else:
                        npol.append({"name" : pol})
                njoa["policy"] = npol
            d["bibjson"]["archiving_policy"] = njoa

        return cls(d)