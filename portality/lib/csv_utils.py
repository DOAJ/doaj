import csv
from typing import Iterable


def read_all(csv_path) -> Iterable[list]:
    with open(csv_path, 'r') as f:
        for row in csv.reader(f):
            yield row


def read_all_as_dict(csv_path) -> Iterable[dict]:
    headers = None
    for row in read_all(csv_path):
        if headers is None:
            headers = row
            continue
        row = dict(zip(headers, row))
        yield row
