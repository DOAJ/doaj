import csv
from typing import Iterable, Union


def read_all(csv_path, as_dict=False) -> Iterable[Union[list, dict]]:
    reader = csv.DictReader if as_dict else csv.reader
    with open(csv_path, 'r') as f:
        for row in reader(f):
            yield row
