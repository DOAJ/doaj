import csv
import os
from portality import models, constants
from portality.lib import dates
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.forms.application_forms import FieldDefinitions as field


"""This script generates files with the detailed information of applications which are rejected."""

APP_FILE_HANDLES = {}
UR_FILE_HANDLES = {}
APP_WRITERS = {}
UR_WRITERS = {}
APP_RECORD_COUNTER = {}
UR_RECORD_COUNTER = {}
BASE_DIR_PATH = None
FIELDS = [
    field.TITLE,
    {"name": "application_type", "label": "Type", "input": "text"},
    {"name": "last_updated", "label": "Date", "input": "text"},
    {"name": "notes", "label": "Notes", "input": "text"},
    field.BOAI, field.OA_STATEMENT_URL, field.ALTERNATIVE_TITLE, field.JOURNAL_URL, field.PISSN, field.EISSN,
    field.KEYWORDS, field.LANGUAGE, field.PUBLISHER_NAME, field.PUBLISHER_COUNTRY, field.INSTITUTION_NAME,
    field.INSTITUTION_COUNTRY, field.LICENSE, field.LICENSE_TERMS_URL, field.LICENSE_DISPLAY,
    field.LICENSE_DISPLAY_EXAMPLE_URL,
    field.COPYRIGHT_AUTHOR_RETAINS, field.COPYRIGHT_URL, field.REVIEW_PROCESS, field.REVIEW_URL,
    field.PLAGIARISM_DETECTION, field.PLAGIARISM_URL, field.AIMS_SCOPE_URL, field.EDITORIAL_BOARD_URL,
    field.AUTHOR_INSTRUCTIONS_URL, field.PUBLICATION_TIME_WEEKS, field.APC, field.APC_CHARGES,
    field.APC_URL, field.HAS_WAIVER, field.WAIVER_URL, field.HAS_OTHER_CHARGES, field.OTHER_CHARGES_URL,
    field.PRESERVATION_SERVICE, field.PRESERVATION_SERVICE_URL, field.DEPOSIT_POLICY, field.DEPOSIT_POLICY_OTHER,
    field.DEPOSIT_POLICY_URL, field.PERSISTENT_IDENTIFIERS, field.ORCID_IDS, field.OPEN_CITATIONS,
    {"name": "id", "label": "Id", "input": "text"},
]
FIELD_NAMES = {"application_type":"admin.application_type", "last_updated":"last_updated", "notes":"admin.notes",
               "publisher_name":"bibjson.publisher.name", "publisher_country": "bibjson.publisher.country",
               "institution_name" : "bibjson.institution.name", "institution_country" : "bibjson.institution.country",
                "other_charges_url": "bibjson.other_charges.url", "deposit_policy" : "bibjson.deposit_policy.has_policy"
               }

COLUMN_HEADINGS = [""]

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
    global APP_WRITERS
    global UR_WRITERS
    # applications file handle
    if application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
        if year not in APP_WRITERS:
            filename = os.path.join(BASE_DIR_PATH, "rejected_applications_" + str(year) + ".csv")
            file_handle = open(filename, 'w')
            APP_FILE_HANDLES[year] = file_handle
            csv_writer = csv.writer(file_handle)
            csv_writer.writerow(COLUMN_HEADINGS)
            APP_WRITERS[year] = csv_writer
        return APP_WRITERS[year]
    else:
        if year not in UR_WRITERS:
            filename = os.path.join(BASE_DIR_PATH, "rejected_update_requests_" + str(year) + ".csv")
            file_handle = open(filename, 'w')
            UR_FILE_HANDLES[year] = file_handle
            csv_writer = csv.writer(file_handle)
            csv_writer.writerow(COLUMN_HEADINGS)
            UR_WRITERS[year] = csv_writer
        return UR_WRITERS[year]

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

def get_param_obj(obj, param):
    if isinstance(obj, list):
        value = ""
        for k in obj:
            if param in k:
                value += str(k[param]) + ","
        return value
    elif param in obj:
        return obj[param]
    else:
        return None

def get_value(obj, key_field):

    param_with_sub_fields = ""
    if isinstance(key_field, list):
        for k in key_field:
            param_value = obj
            params = k.split(".")
            for param in params:
                param_value = get_param_obj(param_value, param)
                if param_value is None:
                    param_value = ""
            param_with_sub_fields += str(param_value) + " "
        return param_with_sub_fields
    else:
        param_value = obj
        params = key_field.split(".")
        for param in params:
            param_value = get_param_obj(param_value, param)
            if param_value is None:
                return ""

        return param_value

def get_notes(record):
    admin = record["admin"]
    notes = ""
    if "notes" in admin:
        for note in admin["notes"]:
            notes += note["date"] + " : " + note["note"] + "\n"
    return notes

def get_field_value(record, field_obj):
    if "name" in field_obj:
        name = field_obj["name"]
        sub_field_names = []
        if "subfields" in field_obj:
            sub_field_names = field_obj["subfields"]
        sub_fields = []
        if name == "notes":
            return get_notes(record)
        if name in FIELD_NAMES:
            field_name = FIELD_NAMES[name]
        else:
            field_name = ApplicationFormXWalk.formField2objectField(name)
            for sub_field in sub_field_names:
                sub_fields.append(ApplicationFormXWalk.formField2objectField(name+"."+sub_field))
        key_field = sub_fields if len(sub_fields) > 0 else field_name
        field_value = get_value(record, key_field)
        if isinstance(field_value, bool):
            return "Yes" if field_value else "No"
        return field_value
    raise Exception("Field name not found")

def create_header():
    for f in FIELDS:
        COLUMN_HEADINGS.append(f["label"])

def write_applications_data_to_file(year, record):

    application_type = record["admin"]["application_type"]
    writer = get_file_handler(year, application_type)
    record_number = get_record_counter(year, application_type)

    row = [record_number]
    for f in FIELDS:
        row.append(get_field_value(record, f))
    writer.writerow(row)

def execute(args):
    try:
        global BASE_DIR_PATH
        BASE_DIR_PATH = args.out

        # create file header
        create_header()

        # Application id is saved as resource_id in Provenance model
        # Iterate through all the applications and query Provenance with application id and status
        # to get rejected applications
        for record in models.Application.iterate(q=application_query(args.from_year, args.to_year), page_size=20):
            application_year = dates.parse(record["admin"]["date_applied"], dates.FMT_DATETIME_MS_STD).year

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
