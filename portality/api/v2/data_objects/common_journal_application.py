from copy import deepcopy

from portality.lib import dataobj, swagger

class OutgoingCommonJournalApplication(dataobj.DataObj, swagger.SwaggerSupport):

    @classmethod
    def from_model(cls, journal_or_app):
        d = deepcopy(journal_or_app.data)

        # we need to re-write the preservation section
        # joa = d.get("bibjson", {}).get("preservation")
        joa = journal_or_app.bibjson().preservation
        if joa is not None:
            njoa = {}
            if "url" in joa:
                njoa["url"] = joa["url"]

            if "service" in joa:
                npol = []
                for pol in joa["service"]:
                    if isinstance(pol, list):
                        npol.append({"name" : pol[1], "domain" : pol[0]})
                    else:
                        npol.append({"name" : pol})
                njoa["service"] = npol

            d["bibjson"]["preservation"] = njoa
        cd = cls(d)
        return cd
