def migrate_journal(data):
    if "application_status" in data.get("admin", {}):
        del data["admin"]["application_status"]
    return data

def migrate_suggestion(data):
    if "in_doaj" in data.get("admin", {}):
        del data["admin"]["in_doaj"]
    if "history" in data:
        del data["history"]
    return data