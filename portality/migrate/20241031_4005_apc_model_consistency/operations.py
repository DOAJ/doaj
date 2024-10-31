def reset_apc(journal_like):
    bj = journal_like.bibjson()
    # the `has_apc` setter has been updated to correct the state of the journal/application, so just re-running
    # the setter with straighted out the state
    if bj.has_apc is False:
        bj.has_apc = False
    return journal_like
