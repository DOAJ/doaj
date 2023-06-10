def blind_to_anonymous_review(obj):
    bib = obj.bibjson()
    processes = bib.editorial_review_process
    if "Blind peer review" in processes:
        bib.remove_editorial_review_process("Blind peer review")
        bib.add_editorial_review_process("Anonymous peer review")
    if "Double blind peer review" in processes:
        bib.remove_editorial_review_process("Double blind peer review")
        bib.add_editorial_review_process("Double anonymous peer review")
    return obj