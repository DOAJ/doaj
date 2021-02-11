from portality import models

def migrate(data):
    if "history" not in data:
        return data

    admin = data.get("admin", {})
    issns = _get_issns(data.get("bibjson", {}))
    replaces = None
    created = data.get("created_date")      # created date defaults to the parent record's created date - will be overridden later if possible

    for h in data["history"]:
        obj = {"bibjson" : h.get("bibjson")}
        if "replaces" in h:
            obj["bibjson"]["replaces"] = h.get("replaces")
        if "isreplacedby" in h:
            obj["bibjson"]["is_replaced_by"] = h.get("isreplacedby")
            for irb in h["isreplacedby"]:
                if irb in issns:
                    replaces = _get_issns(obj["bibjson"])
        #if "date" in h:
        #    created = h["date"]

        j = models.Journal(**obj)
        j.set_in_doaj(admin.get("in_doaj", False))
        j.set_ticked(admin.get("ticked", False))
        j.set_seal(admin.get("seal", False))
        j.set_owner(admin.get("owner"))
        j.set_editor_group(admin.get("editor_group"))
        j.set_editor(admin.get("editor"))
        for c in admin.get("contact", []):
            j.add_contact(c.get("name"), c.get("email"))
        # FIXME: note that the date on the history records appears to be the date of import from the last version of DOAJ, so not much value in it.  Defaulting to the parent's created date
        if created is not None:
            j.set_created(created)

        j.add_note("Continuation automatically extracted from journal {x} during migration".format(x=data.get("id")))
        j.save()

    if replaces is not None:
        data["bibjson"]["replaces"] = replaces
    del data["history"]
    return data

def _get_issns(bibjson):
    issns = []
    for ident in bibjson.get("identifier", []):
        if ident.get("type") in ["pissn", "eissn"]:
            issns.append(ident.get("id"))
    return issns