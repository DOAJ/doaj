from portality import models

batch_size = 1000
total=0

batch = []
suggestion_iterator = models.Suggestion.iterall(page_size=10000)
for s in suggestion_iterator:

    update_deposit_policies = {
        'H\xc3\xa9loise'.decode('utf-8'): 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8'),
        'Diadorum': 'Diadorim'
    }

    changed = False
    for old, new in update_deposit_policies.items():
        try:
            replace_index = s.bibjson().deposit_policy.index(old)
            s.bibjson().deposit_policy[replace_index] = new
            changed = True
        except ValueError:
            pass  # doesn't have the policy we're currently checking for

    if changed:
        s.prep()
        batch.append(s.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print("writing suggestions", len(batch), "; total so far", total)
        models.Suggestion.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print("writing suggestions", len(batch), "; total so far", total)
    models.Suggestion.bulk(batch)


total = 0
batch = []
journal_iterator = models.Journal.iterall(page_size=10000)
for j in journal_iterator:

    update_deposit_policies = {
        'H\xc3\xa9loise'.decode('utf-8'): 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8'),
        'Diadorum': 'Diadorim'
    }

    changed = False
    for old, new in update_deposit_policies.items():
        try:
            replace_index = j.bibjson().deposit_policy.index(old)
            j.bibjson().deposit_policy[replace_index] = new
            changed = True
        except ValueError:
            pass  # doesn't have the policy we're currently checking for

    if changed:
        j.prep()
        batch.append(j.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print("writing journals", len(batch), "; total so far", total)
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print("writing journals", len(batch), "; total so far", total)
    models.Journal.bulk(batch)