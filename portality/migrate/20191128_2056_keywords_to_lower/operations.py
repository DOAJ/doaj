def rewrite_keywords(journal_like):
    bib = journal_like.bibjson()
    kwords = [k.lower() for k in bib.keywords]
    bib.set_keywords(kwords)
    return journal_like
