import csv
from typing import Iterable, Union


def read_all(csv_path, as_dict=False) -> Iterable[Union[list, dict]]:
    reader = csv.DictReader if as_dict else csv.reader
    with open(csv_path, 'r') as f:
        for row in reader(f):
            yield row


def is_empty_row(row: dict) -> bool:
    """ True if every cell in a DictReader row is blank, including any overflow cells stored under the None key """
    for v in row.values():
        cells = v if isinstance(v, list) else [v]
        if any(c is not None and c.strip() for c in cells):
            return False
    return True


def trim_trailing_empty_rows(rows: Iterable[dict]) -> list:
    """ Read all rows, discarding any empty rows at the end (e.g. spreadsheet exports padded with blank lines) """
    rows = list(rows)
    while rows and is_empty_row(rows[-1]):
        rows.pop()
    return rows
