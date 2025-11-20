from portality import models
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
                "journals": 0,
                "applications": 0
            }

        registry[code]["journals"] += 1

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
                "journals": 0,
                "applications": 0
            }

        registry[code]["applications"] += 1

with open("subject_classifications.csv", "w", newline='', encoding='utf-8') as csvfile:
    fieldnames = ["code", "term", "journals", "applications"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for code in sorted(registry.keys()):
        entry = registry[code]
        writer.writerow({
            "code": code,
            "term": entry["term"],
            "journals": entry["journals"],
            "applications": entry["applications"]
        })
