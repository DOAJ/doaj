def migrate(data):
    if "application_status" in data.get("admin", {}):
        del data["admin"]["application_status"]
    return data