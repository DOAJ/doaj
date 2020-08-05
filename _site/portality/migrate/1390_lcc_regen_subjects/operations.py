from portality import models, lcc


def refresh_subjects(record):
    """ Using the GenericBibjson we can fix the subjects on journals, applications and articles with this function """
    bj = record.bibjson()
    assert isinstance(bj, models.GenericBibJSON)
    old_subjects = bj.subjects()
    bj.remove_subjects()

    new_subjects = []
    for s in old_subjects:
        try:
            sobj = {"scheme": 'LCC', "term": lcc.lookup_code(s['code']), "code": s['code']}
            new_subjects.append(sobj)
        except KeyError:
            # Carry over the DOAJ schema subjects
            if 'scheme' in s and s['scheme'] == 'DOAJ':
                new_subjects.append(s)
            else:
                print("Missing code:", s)

    bj.set_subjects(new_subjects)
    if old_subjects != record.bibjson().subjects():
        print('{0} Changed.\nold: {1}\nnew: {2}'.format(record['id'], old_subjects, record.bibjson().subjects()))
    return record
