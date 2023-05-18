from portality.lib.dates import DEFAULT_TIMESTAMP_VAL
from portality.models import Application, Journal
from portality import constants

def check_query(q):
    res = Application.query(q)
    for bucket in res.get("aggregations", {}).get("type", {}).get("buckets", []):
        print(bucket.get("key"), bucket.get("doc_count"))

    hits = res.get("hits", {}).get("hits", [])
    if len(hits) == 0:
        print("No Example ID Available")
    else:
        print("Example IDs", [h.get("_source", {}).get("id") for h in hits[:5]])


print ("CURRENT JOURNALS")
print("Expecting all to be UR")

CJ = {
    "query" : {
        "bool": {
            "must": [
                {"exists": {"field": "admin.current_journal"}}
            ]
        }
    },
    "aggs" : {
        "type": {
            "terms": {"field": "admin.application_type.exact"}
        }
    }
}

check_query(CJ)

print ("NO CURRENT JOURNAL, NO RELATED JOURNAL")
print("Expecting all to be NA")

NO_CJ_RJ = {
    "query" : {
        "bool": {
            "must_not": [
                {"exists": {"field": "admin.current_journal"}},
                {"exists": {"field": "admin.related_journal"}}
            ]
        }
    },
    "aggs" : {
        "type": {
            "terms": {"field": "admin.application_type.exact"}
        }
    }
}

check_query(NO_CJ_RJ)

print ("RELATED JOURNAL, REJECTED")
print("Expecting all to be UR")

RJ_REJECTED = {
    "query" : {
        "bool": {
            "must": [
                {"exists": {"field": "admin.related_journal"}},
                {"term": {"admin.application_status": constants.APPLICATION_STATUS_REJECTED}}
            ],
            "must_not": [
                {"exists": {"field": "admin.current_journal"}}
            ]
        }
    },
    "aggs" : {
        "type": {
            "terms": {"field": "admin.application_type.exact"}
        }
    }
}

check_query(RJ_REJECTED)



RJ_EXISTS = {
    "query" : {
        "bool": {
            "must": [
                {"exists": {"field": "admin.related_journal"}}
            ],
            "must_not": [
                {"exists": {"field": "admin.current_journal"}},
                {"term": {"admin.application_status": constants.APPLICATION_STATUS_REJECTED}}
            ]
        }
    },
    "aggs" : {
        "type": {
            "terms": {"field": "admin.application_type.exact"}
        }
    }
}

missing_journals = 0
missing_types = {"new_application": 0, "update_request": 0}
missing_example = []

accepted_ca_journals = 0
accepted_ca_types = {"new_application": 0, "update_request": 0}
accepted_ca_example = []

accepted_notca_journals = 0
accepted_notca_types = {"new_application": 0, "update_request": 0}
accepted_notca_example = []

not_accepted_journals = 0
not_accepted_types = {"new_application": 0, "update_request": 0}
not_accepted_example = []

single_journals = 0
single_types = {"new_application": 0, "update_request": 0}
single_example = []

oldest_journals = 0
oldest_types = {"new_application": 0, "update_request": 0}
oldest_example = []

not_oldest_journals = 0
not_oldest_types = {"new_application": 0, "update_request": 0}
not_oldest_example = []

for application in Application.iterate(RJ_EXISTS):
    j = Journal.pull(application.related_journal)
    if j is None:
        missing_journals += 1
        missing_types[application.application_type] += 1
        if len(missing_example) < 5:
            missing_example.append(application.id)
    elif len(j.related_applications) == 0:
        if application.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            if j.current_application == application.id:
                accepted_ca_journals += 1
                accepted_ca_types[application.application_type] += 1
                if len(accepted_ca_example) < 5:
                    accepted_ca_example.append(application.id)
            else:
                accepted_notca_journals += 1
                accepted_notca_types[application.application_type] += 1
                if len(accepted_notca_example) < 5:
                    accepted_notca_example.append(application.id)
        else:
            not_accepted_journals += 1
            not_accepted_types[application.application_type] += 1
            if len(not_accepted_example) < 5:
                not_accepted_example.append(application.id)

    elif len(j.related_applications) == 1:
        single_journals += 1
        single_types[application.application_type] += 1
        if len(single_example) < 5:
            single_example.append(application.id)

    else:
        relaps = j.related_applications
        sorted(relaps, key=lambda x: x.get("date_accepted", DEFAULT_TIMESTAMP_VAL))
        if relaps[-1].get("application_id") == application.id:
            oldest_journals += 1
            oldest_types[application.application_type] += 1
            if len(oldest_example) < 5:
                oldest_example.append(application.id)
        else:
            not_oldest_journals += 1
            not_oldest_types[application.application_type] += 1
            if len(not_oldest_example) < 5:
                not_oldest_example.append(application.id)


print("RELATED JOURNAL MISSING, APP NOT REJECTED")
print("Expecting all to be NA")
print(missing_types)
print("from applicable applications", missing_journals)
print("examples", missing_example)

print("RELATED JOURNAL EXISTS, APP ACCEPTED, IS CURRENT APP")
print("Expecting all to be NA")
print(accepted_ca_types)
print("from applicable applications", accepted_ca_journals)
print("examples", accepted_ca_example)

print("RELATED JOURNAL EXISTS, APP ACCEPTED, NOT CURRENT APP")
print("Expecting all to be NA")
print(accepted_notca_types)
print("from applicable applications", accepted_notca_journals)
print("examples", accepted_notca_example)

print("RELATED JOURNAL EXISTS, APP NOT ACCEPTED")
print("Expecting all to be UR")
print(not_accepted_types)
print("from applicable applications", not_accepted_journals)
print("examples", not_accepted_example)

print("RELATED JOURNAL EXISTS, EXACTLY ONE RA")
print("Expecting all to be NA")
print(single_types)
print("from applicable applications", single_journals)
print("examples", single_example)

print("RELATED JOURNAL EXISTS, MULTIPLE RA, OLDEST")
print("Expecting all to be NA")
print(oldest_types)
print("from applicable applications", oldest_journals)
print("examples", oldest_example)

print("RELATED JOURNAL EXISTS, MULTIPLE RA, NOT OLDEST")
print("Expecting all to be UR")
print(not_oldest_types)
print("from applicable applications", not_oldest_journals)
print("examples", not_oldest_example)