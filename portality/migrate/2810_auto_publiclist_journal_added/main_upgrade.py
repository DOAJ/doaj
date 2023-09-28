import argparse
from pathlib import Path

from openpyxl.reader.excel import load_workbook

from portality.models.datalog_journal_added import DatalogJournalAdded


def has_any(val):
    val = val or ''
    val = bool(val.strip())
    return val


def to_datalog_journal_added(row):
    title, issn, date_added, has_seal, has_continuations, *_ = row
    has_seal = has_any(has_seal)
    has_continuations = has_any(has_continuations)

    obj = DatalogJournalAdded(
        title=title,
        issn=issn,
        date_added=date_added,
        has_seal=has_seal,
        has_continuations=has_continuations,
    )
    obj.data['es_type'] = obj.__type__
    obj.data['id'] = obj.makeid()
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src', type=str, help='path of public list excel file ')

    args = parser.parse_args()

    wb = load_workbook(args.src)
    sheet = wb['Added']

    rows = sheet.values
    rows = (r for r in rows if r[0] is not None)
    while next(rows)[0] != 'Journal Title':
        pass

    records = (to_datalog_journal_added(r) for r in rows)
    records = (r.data for r in records)
    records = list(records)
    DatalogJournalAdded.bulk(records)
    print(f'Total datalog-journal-added [{len(records)}] created')


if __name__ == '__main__':
    main()
