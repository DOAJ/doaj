from portality.models import Article

def amend_identifiers(source: dict):
    bj = source.get("bibjson", {})
    new_identifiers = []
    for identifier in bj.get("identifier", []):
        # lower case the doi type
        if identifier.get("type").lower() == "doi":
            identifier["type"] = "doi"
            new_identifiers.append(identifier)

        # keep any identifiers which have correct types
        elif identifier.get("type").lower() in ["pissn", "eissn", "doi"]:
            new_identifiers.append(identifier)


    # discard any other identifier types by omission from copy
    bj["identifier"] = new_identifiers

    # return an instance, so that save/prep will work, and renormalise any identifiers (the doi specifically)
    return Article(**source)
