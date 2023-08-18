import csv
import os
from portality import models, constants
from portality.lib import dates


"""This script generates files with the detailed information of applications which are rejected."""

APP_FILE_HANDLES = {}
UR_FILE_HANDLES = {}
APP_RECORD_COUNTER = {}
UR_RECORD_COUNTER = {}
BASE_DIR_PATH = None


def application_query(date_year_from, date_year_to):
    return {
          "query": {
            "bool": {
              "must": [
                {
                  "terms": {
                    "admin.application_type.exact": [constants.APPLICATION_TYPE_NEW_APPLICATION,
                                                     constants.APPLICATION_TYPE_UPDATE_REQUEST]
                  }
                },
                {
                  "range": {
                    "admin.date_applied": {
                      "gte": str(date_year_from) + "-01-01",
                      "lte": str(date_year_to) + "-12-31"
                    }
                  }
                }
              ]
            }
          },
          "track_total_hits": True
        }


def provenance_query(resource_id):
    return {
          "query": {
            "bool": {
              "must": [
                  {
                      "term": {
                          "action": constants.PROVENANCE_STATUS_REJECTED
                      }
                  },
                 {
                      "term": {
                          "resource_id": resource_id
                      }
                }
              ]
            }
          },
          "sort": [
            {
                "last_updated": {
                    "order": "desc"
                }
            }
          ],
          "track_total_hits": True
        }


def get_file_handler(year, application_type):
    global APP_FILE_HANDLES
    global UR_FILE_HANDLES
    # applications file handle
    if application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
        filename = os.path.join(BASE_DIR_PATH, "rejected_applications_" + str(year) + ".csv")
        return csv.writer(APP_FILE_HANDLES.setdefault(year, open(filename, 'w')))
    # update requests file handle
    else:
        filename = os.path.join(BASE_DIR_PATH, "rejected_update_requests_" + str(year) + ".csv")
        return csv.writer(UR_FILE_HANDLES.setdefault(year, open(filename, 'w')))


def get_record_counter(year, application_type):
    global APP_RECORD_COUNTER
    global UR_RECORD_COUNTER
    # applications counter
    if application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
        record_number = APP_RECORD_COUNTER.setdefault(year, 0)
        record_number += 1
        APP_RECORD_COUNTER[year] = record_number
        return record_number
    # Update requests counter
    else:
        record_number = UR_RECORD_COUNTER.setdefault(year, 0)
        record_number += 1
        UR_RECORD_COUNTER[year] = record_number
        return record_number


def write_applications_data_to_file(year, record):

    bibjson = record["bibjson"]
    admin = record["admin"]
    index = record["index"]

    application_type = admin["application_type"]
    writer = get_file_handler(year, application_type)
    record_number = get_record_counter(year, application_type)

    writer.writerow([record_number, "Title", bibjson["title"]])
    writer.writerow(["", "Application Type", admin["application_type"]])
    writer.writerow(["", "last_updated", record["last_updated"]])
    if "notes" in admin:
        writer.writerow(["","Notes",""])
        for note in admin["notes"]:
            writer.writerow(["", note["date"], note["note"]])
    writer.writerow(["", "country", index["country"]])
    writer.writerow(["", "continued", index["continued"]])
    writer.writerow(["", "has_editor_group", index["has_editor_group"]])
    writer.writerow(["", "has_editor", index["has_editor"]])
    writer.writerow(["", "issn", index["issn"]])
    writer.writerow(["", "subject", index["subject"]])
    if "schema_subject" in index:
        writer.writerow(["", "schema_subject", index["schema_subject"]])
    if "classification" in index:
        writer.writerow(["", "classification", index["classification"]])
    writer.writerow(["", "language", index["language"]])
    if "license" in index:
        writer.writerow(["", "license", index["license"]])
    if "classification_paths" in index:
        writer.writerow(["", "classification_paths", index["classification_paths"]])
    if "schema_code" in index:
        writer.writerow(["", "schema_code", index["schema_code"]])
    if "schema_codes_tree" in index:
        writer.writerow(["", "schema_codes_tree", index["schema_codes_tree"]])
    if "boai" in bibjson:
        writer.writerow(["", "boai", bibjson["boai"]])
    if "eissn" in bibjson:
        writer.writerow(["", "eissn", bibjson["eissn"]])
    if "publication_time_weeks" in bibjson:
        writer.writerow(["", "publication_time_weeks", bibjson["publication_time_weeks"]])
    if "oa_start" in bibjson:
        writer.writerow(["", "oa_start", bibjson["oa_start"]])
    if "apc" in bibjson:
        apc = bibjson["apc"]
        if "has_apc" in apc:
            writer.writerow(["", "apc-has_apc", apc["has_apc"]])
        if "url" in apc:
            writer.writerow(["", "apc-url", apc["url"]])
        if "max" in apc:
            for max_data in apc["max"]:
                writer.writerow(["", "apc-max-currency", max_data["currency"]])
                writer.writerow(["", "apc-max-price", max_data.get("price", '')])
    if "article" in bibjson:
        article = bibjson["article"]
        if "license_display_example_url" in article:
            writer.writerow(["", "article-license_display_example_url", article["license_display_example_url"]])
        if "orcid" in article:
            writer.writerow(["", "article-orcid", article["orcid"]])
        if "i4oc_open_citations" in article:
            writer.writerow(["", "article-i4oc_open_citations", article["i4oc_open_citations"]])
        if "license_display_example_url" in article:
            writer.writerow(["", "article-license_display", article["license_display"]])
    if "copyright" in bibjson:
        copyright = bibjson["copyright"]
        if "author_retains" in copyright:
            writer.writerow(["", "copyright-author_retains", copyright["author_retains"]])
            writer.writerow(["", "copyright-url", copyright.get("url", '')])
    if "deposit_policy" in bibjson and "has_policy" in bibjson["deposit_policy"]:
        writer.writerow(["", "deposit_policy-has_policy", bibjson["deposit_policy"]["has_policy"]])
    if "editorial" in bibjson:
        writer.writerow(["", "editorial-review_url", bibjson["editorial"].get("review_url", '')])
        writer.writerow(["", "editorial-board_url", bibjson["editorial"].get("board_url", '')])
        writer.writerow(["", "editorial-review_process", bibjson["editorial"]["review_process"]])
    if "pid_scheme" in bibjson:
        pid_scheme = bibjson["pid_scheme"]["has_pid_scheme"]
        writer.writerow(["", "pid_scheme-has_pid_scheme", "yes" if pid_scheme else "no"])
        if pid_scheme:
            writer.writerow(["", "pid_scheme-scheme", bibjson["pid_scheme"]["scheme"]])
    if "plagiarism" in bibjson:
        writer.writerow(["", "plagiarism-detection", bibjson["plagiarism"]["detection"]])
        writer.writerow(["", "plagiarism-url", bibjson["plagiarism"].get('url', '')])
    has_preservation = bibjson["preservation"]["has_preservation"]
    writer.writerow(["", "preservation-has_preservation", has_preservation])
    writer.writerow(["", "publisher-name", bibjson["publisher"]["name"]])
    writer.writerow(["", "publisher-country", bibjson["publisher"]["country"]])
    writer.writerow(["", "ref-oa_statement", bibjson["ref"]["oa_statement"]])
    writer.writerow(["", "ref-journal", bibjson["ref"]["journal"]])
    writer.writerow(["", "ref-aims_scope", bibjson["ref"]["aims_scope"]])
    writer.writerow(["", "ref-author_instructions", bibjson["ref"]["author_instructions"]])
    writer.writerow(["", "ref-license_terms", bibjson["ref"].get("license_terms", '')])
    if "waiver" in bibjson:
        has_waiver = bibjson["waiver"]["has_waiver"]
        writer.writerow(["", "waiver-has_waiver", has_waiver])
        if has_waiver:
            writer.writerow(["", "waiver-url", bibjson["waiver"]["url"]])
    writer.writerow(["", "keywords", bibjson["keywords"]])
    writer.writerow(["", "language", bibjson["language"]])
    if "license" in bibjson:
        for license_data in bibjson["license"]:
            writer.writerow(["", "license-type", license_data["type"]])
            writer.writerow(["", "license-BY", license_data.get('BY', '')])
            writer.writerow(["", "license-NC", license_data.get('NC', '')])
            writer.writerow(["", "license-ND", license_data.get('ND', '')])
            writer.writerow(["", "license-SA", license_data.get('SA', '')])
            writer.writerow(["", "license-url", license_data.get("url", '')])
    if "subject" in bibjson:
        for subject_data in bibjson["subject"]:
            writer.writerow(["", "subject-code", subject_data["code"]])
            writer.writerow(["", "subject-scheme", subject_data["scheme"]])
            writer.writerow(["", "subject-term", subject_data["term"]])
    if "replaces" in bibjson:
        writer.writerow(["", "replaces", bibjson["replaces"]])
    if "is_replaced_by" in bibjson:
        writer.writerow(["", "is_replaced_by", bibjson["is_replaced_by"]])
    writer.writerow([])
    writer.writerow([])


def execute(args):
    try:
        global BASE_DIR_PATH
        BASE_DIR_PATH = args.out

        # Application id is saved as resource_id in Provenance model
        # Iterate through all the applications and query Provenance with application id and status
        # to get rejected applications
        for record in models.Application.iterate(q=application_query(args.from_year, args.to_year), page_size=20):
            application_year = dates.parse(record["created_date"], dates.FMT_DATETIME_MS_STD).year

            provenance_res = models.Provenance.query(q=provenance_query(record["id"]), size=2)
            if provenance_res["hits"]["total"]["value"] > 0:
                write_applications_data_to_file(application_year, record)

    finally:
        for file_handle in APP_FILE_HANDLES.values():
            file_handle.close()
        for file_handle in UR_FILE_HANDLES.values():
            file_handle.close()


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file directory path", required=True)
    parser.add_argument("-fy", "--from_year", help="from-year to filter by", required=True)
    parser.add_argument("-ty", "--to_year", help="to-year to filter by", required=True)
    args = parser.parse_args()

    execute(args)
