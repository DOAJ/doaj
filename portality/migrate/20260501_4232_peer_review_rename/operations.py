def peer_review_rename(obj):
    bib = obj.bibjson()
    processes = bib.editorial_review_process

    # Rename "Anonymous peer review" → "Single anonymous peer review"
    if "Anonymous peer review" in processes:
        bib.remove_editorial_review_process("Anonymous peer review")
        if "Single anonymous peer review" not in bib.editorial_review_process:
            bib.add_editorial_review_process("Single anonymous peer review")

    # Remove "Peer review" and record it in the Other free-text slot as "Unspecified peer review"
    if "Peer review" in processes:
        bib.remove_editorial_review_process("Peer review")
        if "Unspecified peer review" not in bib.editorial_review_process:
            bib.add_editorial_review_process("Unspecified peer review")

    return obj
