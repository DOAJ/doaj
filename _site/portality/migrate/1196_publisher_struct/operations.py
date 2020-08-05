from portality import models

def clear_journal_index_fields(record):
    if "index" in record:
        del record["index"]
    return models.Journal(**record)

def clear_suggestion_index_fields(record):
    if "index" in record:
        del record["index"]
    return models.Suggestion(**record)