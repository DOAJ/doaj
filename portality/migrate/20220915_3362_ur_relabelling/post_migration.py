from portality.models import Application, Journal

def check_query(q):
    res = Application.query(q)
    for bucket in res.get("aggregations", {}).get("type", {}).get("buckets", []):
        print(bucket.get("key"), bucket.get("doc_count"))

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
                {"term": {"admin.application_status": "rejected"}}
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
                {"term": {"admin.application_status": "rejected"}}
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

accepted_ca_journals = 0
accepted_ca_types = {"new_application": 0, "update_request": 0}

accepted_notca_journals = 0
accepted_notca_types = {"new_application": 0, "update_request": 0}

not_accepted_journals = 0
not_accepted_types = {"new_application": 0, "update_request": 0}

single_journals = 0
single_types = {"new_application": 0, "update_request": 0}

oldest_journals = 0
oldest_types = {"new_application": 0, "update_request": 0}

not_oldest_journals = 0
not_oldest_types = {"new_application": 0, "update_request": 0}

for application in Application.iterate(RJ_EXISTS):
    j = Journal.pull(application.related_journal)
    if j is None:
        missing_journals += 1
        missing_types[application.application_type] += 1
    elif len(j.related_applications) == 0:
        if application.application_status == "accepted":
            if j.current_application == application.id:
                accepted_ca_journals += 1
                accepted_ca_types[application.application_type] += 1
            else:
                accepted_notca_journals += 1
                accepted_notca_types[application.application_type] += 1
        else:
            not_accepted_journals += 1
            not_accepted_types[application.application_type] += 1

    elif len(j.related_applications) == 1:
        single_journals += 1
        single_types[application.application_type] += 1

    else:
        relaps = j.related_applications
        sorted(relaps, key=lambda x: x.get("date_accepted", "1970-01-01T00:00:00Z"))
        if relaps[-1].get("application_id") == application.id:
            oldest_journals += 1
            oldest_types[application.application_type] += 1
        else:
            not_oldest_journals += 1
            not_oldest_types[application.application_type] += 1


print("RELATED JOURNAL MISSING, APP NOT REJECTED")
print("Expecting all to be NA")
print(missing_types)
print("from applicable applications", missing_journals)

print("RELATED JOURNAL EXISTS, APP ACCEPTED, IS CURRENT APP")
print("Expecting all to be NA")
print(accepted_ca_types)
print("from applicable applications", accepted_ca_journals)

print("RELATED JOURNAL EXISTS, APP ACCEPTED, NOT CURRENT APP")
print("Expecting all to be NA")
print(accepted_notca_types)
print("from applicable applications", accepted_notca_journals)

print("RELATED JOURNAL EXISTS, APP NOT ACCEPTED")
print("Expecting all to be UR")
print(not_accepted_types)
print("from applicable applications", not_accepted_journals)

print("RELATED JOURNAL EXISTS, EXACTLY ONE RA")
print("Expecting all to be NA")
print(single_types)
print("from applicable applications", single_journals)

print("RELATED JOURNAL EXISTS, MULTIPLE RA, OLDEST")
print("Expecting all to be NA")
print(oldest_types)
print("from applicable applications", oldest_journals)

print("RELATED JOURNAL EXISTS, MULTIPLE RA, NOT OLDEST")
print("Expecting all to be UR")
print(not_oldest_types)
print("from applicable applications", not_oldest_journals)