def enforce_consistency(journal_like):
    if journal_like.bibjson().has_apc is False:
        journal_like.bibjson().has_apc = False

    if journal_like.bibjson().has_waiver is False:
        journal_like.bibjson().has_waiver = False

    if journal_like.bibjson().has_other_charges is False:
        journal_like.bibjson().has_other_charges = False

    return journal_like
