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
            sobj = {"scheme": u'LCC', "term": lcc.lookup_code(s['code']), "code": s['code']}
            new_subjects.append(sobj)
        except KeyError:
            # Subject has no code, that's fine, let's have a look at it
            print "Missing code:", s

    bj.set_subjects(new_subjects)
    if bj.subjects() != record.bibjson().subjects():
        print 'WHAT', bj.subjects()
    return record
