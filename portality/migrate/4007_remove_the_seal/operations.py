from portality import models

def journal_remove_seal(record):
    if "seal" in record.get("admin", {}):
        del record["admin"]["seal"]
    if "has_seal" in record.get("index", {}):
        del record["index"]["has_seal"]
    return record
