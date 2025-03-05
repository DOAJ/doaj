from portality import models

def journal_remove_seal(record):
    if "seal" in record.get("admin", {}):
        del record["admin"]["seal"]
    if "has_seal" in record.get("index", {}):
        del record["index"]["has_seal"]
    return record

def journal_remove_plagiarism_url(record):
    if "url" in record.get("bibjson", {}).get("plagiarism", {}):
        del record["bibjson"]["plagiarism"]["url"]

    return record

def journal_remove_license_display_example_url(record):
    if "license_display_example_url" in record.get("bibjson", {}).get("article", {}):
        del record["bibjson"]["article"]["license_display_example_url"]

    return record
