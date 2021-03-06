import esprit, csv

from portality.core import es_connection
from portality.util import ipt_prefix


def query_result_generator(query, type, page_size=1000, keepalive="1m", wrap=None):
    for result in esprit.tasks.scroll(es_connection, ipt_prefix(type), q=query, page_size=page_size, keepalive=keepalive):
        if wrap is not None:
            result = wrap(result)
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
