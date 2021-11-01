def clean(record):
    if record.bibjson().get_journal_license():
        record.bibjson().remove_journal_licences()
    return record
