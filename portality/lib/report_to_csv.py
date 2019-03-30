import esprit, codecs

from portality.core import app
from portality.clcsv import UnicodeWriter


def query_result_generator(query, type, page_size=1000, keepalive="1m"):
    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
    for result in esprit.tasks.scroll(conn, type, q=query, page_size=page_size, keepalive=keepalive):
        yield result


def report_to_csv(result_generator, headers, output_map, output_file):
    with codecs.open(output_file, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(headers)

        for result in result_generator:
            record = output_map(result)
            row = []
            for h in headers:
                row.append(record[h])
            writer.writerow(row)