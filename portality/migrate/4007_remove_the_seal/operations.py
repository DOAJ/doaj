from portality import models

def journal_remove_seal(record):
    if "seal" in record.get("admin", {}):
        del record["admin"]["seal"]
    if "has_seal" in record.get("index", {}):
        del record["index"]["has_seal"]
    return record

def journal_remove_orcid(record):
    if "orcid" in record.get("bibjson", {}).get("article", {}):
        del record["bibjson"]["article"]["orcid"]

    return record

def journal_remove_open_citations(record):
    if "i4oc_open_citations" in record.get("bibjson", {}).get("article", {}):
        del record["bibjson"]["article"]["i4oc_open_citations"]

    return record
