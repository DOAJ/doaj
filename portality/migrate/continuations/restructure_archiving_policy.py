from portality.models import Journal, Suggestion

def migrate_journal(data):
    if "bibjson" not in data:
        return Journal(**data)
    ap = data.get("bibjson").get("archiving_policy")
    if ap is None:
        return Journal(**data)

    data["bibjson"]["archiving_policy"] = _reformat_data(ap)
    return Journal(**data)

def migrate_suggestion(data):
    if "bibjson" not in data:
        return Suggestion(**data)
    ap = data.get("bibjson").get("archiving_policy")
    if ap is None:
        return Suggestion(**data)

    data["bibjson"]["archiving_policy"] = _reformat_data(ap)
    return Suggestion(**data)

def _reformat_data(ap):
    nap = {}
    if "url" in ap:
        nap["url"] = ap["url"]
    if "policy" in ap:
        nap["known"] = []
        for p in ap["policy"]:
            if isinstance(p, str):
                nap["known"].append(p)
            else:
                k, v = p
                if k.lower() == "other":
                    nap["other"] = v
                elif k.lower() == "a national library":
                    nap["nat_lib"] = v

    return nap