from portality import models, constants
import csv

registry = {}

for journal in models.Journal.iterall_unstable():
    bj = journal.bibjson()
    subjects = bj.subjects()
    for sub in subjects:
        code = sub.get("code")
        term = sub.get("term")

        if code is None:
            print(f"Journal {journal.id} has subject with no code, term '{term}'")
            continue

        if code not in registry:
            registry[code] = {
                "term": term,
                "journals": {
                    "in_doaj": 0,
                    "not_in_doaj": 0
                },
                "applications": {
                    status: 0 for status in constants.APPLICATION_STATUSES_ALL
                }
            }

        if journal.is_in_doaj():
            registry[code]["journals"]["in_doaj"] += 1
        else:
            registry[code]["journals"]["not_in_doaj"] += 1

for application in models.Application.iterall_unstable():
    bj = application.bibjson()
    subjects = bj.subjects()
    for sub in subjects:
        code = sub.get("code")
        term = sub.get("term")

        if code is None:
            print(f"Application {application.id} has subject with no code, term '{term}'")
            continue

        if code not in registry:
            registry[code] = {
                "term": term,
                "journals": {
                    "in_doaj": 0,
                    "not_in_doaj": 0
                },
                "applications": {
                    status: 0 for status in constants.APPLICATION_STATUSES_ALL
                }
            }

        status = application.application_status
        if status not in registry[code]["applications"]:
            print(f"Application {application.id} has unknown status '{status}'")
            continue

        registry[code]["applications"][status] += 1

with open("subject_classifications.csv", "w", newline='', encoding='utf-8') as csvfile:
    fieldnames = ["code", "term", "journals_in_doaj", "journals_not_in_doaj"] + ["application: " + status for status in list(constants.APPLICATION_STATUSES_ALL)]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for code in sorted(registry.keys()):
        entry = registry[code]
        obj = {
            "code": code,
            "term": entry["term"],
            "journals_in_doaj": entry["journals"]["in_doaj"],
            "journals_not_in_doaj": entry["journals"]["not_in_doaj"]
        }
        for status in constants.APPLICATION_STATUSES_ALL:
            obj["application: " + status] = entry["applications"][status]
        writer.writerow(obj)
