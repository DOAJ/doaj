def rename_policy(journal_like):
    jbib = journal_like.bibjson()
    if "Sherpa/Romeo" in jbib.deposit_policy:
        jbib.remove_deposit_policy("Sherpa/Romeo")
        jbib.add_deposit_policy("Open Policy Finder")
    return journal_like
