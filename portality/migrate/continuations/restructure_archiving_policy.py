from portality.models import Journal

def migrate(data):
    if "bibjson" not in data:
        return Journal(**data)
    ap = data.get("bibjson").get("archiving_policy")
    if ap is None:
        return Journal(**data)

    nap = {}
    if "url" in ap:
        nap["url"] = ap["url"]
    if "policy" in ap:
        nap["known"] = []
        for p in ap["policy"]:
            if isinstance(p, basestring):
                nap["known"].append(p)
            else:
                k, v = p
                if k.lower() == "other":
                    nap["other"] = v
                elif k.lower() == "a national library":
                    nap["nat_lib"] = v

    data["bibjson"]["archiving_policy"] = nap
    return Journal(**data)