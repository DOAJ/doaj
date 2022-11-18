import csv

from portality.core import es_connection
from portality.util import ipt_prefix


def query_result_generator(query, model, page_size=1000, keepalive="1m", wrap=False):
    for result in model.iterate(q=query, page_size=page_size, keepalive=keepalive, wrap=wrap):
        yield result


def report_to_csv(result_generator, headers, output_map, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for result in result_generator:
            record = output_map(result)
            row = []
            for h in headers:
                row.append(record[h])
            writer.writerow(row)
