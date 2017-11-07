from portality import models


def refresh_subjects(record):
    """ Using the GenericBibjson we can fix the subjects on journals, applications and articles with this function """
    bj = record.bibjson()
    assert isinstance(bj, models.GenericBibJSON)
    old_subjects = bj.subjects()
    bj.remove_subjects()

    new_subjects = []
    for s in old_subjects:
        # Do stuff
        new_subjects.append(s)
    return record
