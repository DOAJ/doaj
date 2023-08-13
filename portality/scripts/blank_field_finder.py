import argparse
from pathlib import Path
from typing import Any, Iterable

from portality.bll.services.journal import JournalService
from portality.lib import csv_utils
from portality.models import Application, Journal


def to_k_v(item: Any, prefix: list = None):
    if prefix is None:
        prefix = []

    if isinstance(item, dict):
        for k, v in item.items():
            yield from to_k_v(v, prefix=prefix + [k])

    elif isinstance(item, list):
        for k, v in enumerate(item):
            yield from to_k_v(v, prefix=prefix + [k])
    else:
        yield '.'.join(map(str, prefix)), str(item)


def tee(txt: str, out_file):
    print(txt)
    out_file.write(txt + '\n')


def write_bad_data_domain_object(domain_object_class: Any, out_path):
    with open(out_path, 'w') as f:
        items = iter(domain_object_class.iterall())
        while True:
            try:
                j = next(items, None)
            except:
                continue

            if j is None:
                break

            for k, v in filter_bad_only(to_k_v(j.data)):
                tee(f'{j.id} {k} [{v}]', f)


def main2():
    with open('/tmp/journals.csv', 'w') as f:
        JournalService._make_journals_csv(f)


def is_bad_str(v: str):
    return isinstance(v, str) and v != v.strip()


def filter_bad_only(row: Iterable):
    return (i for i in row if is_bad_str(i[1]))


def write_bad_data_journals_csv(csv_path, out_path):
    with open(out_path, 'w') as out_file:
        for row in csv_utils.read_all(csv_path, as_dict=True):
            for k, v in filter_bad_only(row.items()):
                tee(f'{k} [{v}]', out_file)


def write_results(journal_csv_path, out_dir):
    # out_dir = Path('/tmp')
    # journal_csv_path = '/home/kk/tmp/journals.csv'
    out_dir = Path(out_dir)
    write_bad_data_domain_object(Application, out_dir / 'bad_app.txt')
    write_bad_data_domain_object(Journal, out_dir / 'bad_journals.txt')
    if journal_csv_path:
        write_bad_data_journals_csv(journal_csv_path, out_dir / 'bad_journals_csv.txt')


def main():
    parser = argparse.ArgumentParser(description='Output file with bad data')
    parser.add_argument('-i', '--input', help='Path of input CSV file', type=str, default=None)
    parser.add_argument('-o', '--output', help='Output directory', type=str, default='.')
    args = parser.parse_args(
        # ['-i', '/home/kk/tmp/journals.csv', '-o', '/tmp']
    )
    write_results(args.input, args.output)


if __name__ == '__main__':
    main()
