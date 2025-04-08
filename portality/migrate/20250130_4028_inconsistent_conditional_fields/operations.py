def enforce_consistency(journal_like):
    if journal_like.bibjson().has_apc is False:
        printable = False
        if journal_like.data["bibjson"].get("apc", {}).get("max") is not None:
            printable=True

        if printable: print(journal_like.id)
        journal_like.bibjson().has_apc = False
        if printable: print(journal_like.data["bibjson"].get("apc", {}))

    if journal_like.bibjson().has_waiver is False:
        journal_like.bibjson().has_waiver = False

    if journal_like.bibjson().has_other_charges is False:
        journal_like.bibjson().has_other_charges = False

    return journal_like
