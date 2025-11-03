from portality import models
from portality.lib import paths
import os, csv

MAPPING_FILE = paths.rel2abs(__file__, "code_mapping.csv")

CRDC = paths.rel2abs(__file__, "..", "..", "..", "cms", "classification", "base")
CRDC_SOURCE = [
    os.path.join(CRDC, "CRDC-CCRD-2020-FOR-DDR-StructureV2-eng.csv"),
    os.path.join(CRDC, "CRDC-CCRD-2020-SEO-OSE-StructureV2-eng.csv"),
    os.path.join(CRDC, "CRDC-CCRD-2020-TOA-TDA-StructureV2-eng.csv")
]

MAPPING = {}
with open(MAPPING_FILE, "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) != 2:
            continue
        lcc_code = row[0].strip()
        crdc_code = row[1].strip()
        MAPPING[lcc_code] = crdc_code

CRDC_LOOKUP = {}
for source in CRDC_SOURCE:
    with open(source, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("Code")
            term = row.get("Class title")
            if code is not None and term is not None:
                CRDC_LOOKUP[code.strip()] = term.strip()


def lcc_to_crdc(journal:models.JournalLikeObject):
    bj = journal.bibjson()
    subjects = bj.subjects()
    new_subjects = []
    for sub in subjects:
        code = sub.get("code")
        if code is None:
            continue
        if code not in MAPPING:
            print(f"Journal {journal.id} has LCC code '{code}' with no CRDC mapping")
            continue

        crdc_code = MAPPING[code]
        crdc_term = CRDC_LOOKUP.get(crdc_code)

        if crdc_term is None:
            print(f"Journal {journal.id} has LCC code '{code}' mapped to CRDC code '{crdc_code}' which has no term value")
            continue

        new_subjects.append({
            "scheme": "LCC",    # FIXME: this is just for review, the real scheme should be "CRDC"
            "code": crdc_code,
            "term": crdc_term
        })

    bj.subject = new_subjects
    return journal