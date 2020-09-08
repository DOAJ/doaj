from flask_login import current_user
from portality.core import app
from portality import models

# query sanitisers
##################

def public_query_validator(q):
    # no deep paging
    if q.from_result() > 10000:
        return False

    if q.size() > 200:
        return False

    # if the query has facets, that's fine
    # otherwise, if it has no facets, only allow "count" style
    # queries with zero results returned
    if q.has_facets():
        return True
    else:
        return q.size() == 0


# query filters
###############


def only_in_doaj(q):
    q.clear_match_all()
    q.add_must({"term" : {"admin.in_doaj" : True}})
    return q


def owner(q):
    q.clear_match_all()
    q.add_must({"term" : {"admin.owner.exact" : current_user.id}})
    return q


def update_request(q):
    q.clear_match_all()
    q.add_must({"range" : {"created_date" : {"gte" : app.config.get("UPDATE_REQUEST_SHOW_OLDEST")}}})
    q.add_must({"exists" : {"field" : "admin.current_journal"}})
    return q


def associate(q):
    q.clear_match_all()
    q.add_must({"term" : {"admin.editor.exact" : current_user.id}})
    return q


def editor(q):
    gnames = []
    groups = models.EditorGroup.groups_by_editor(current_user.id)
    for g in groups:
        gnames.append(g.name)
    q.clear_match_all()
    q.add_must({"terms" : {"admin.editor_group.exact" : gnames}})
    return q


def private_source(q):
    q.add_include(["admin.application_status", "suggestion", "admin.ticked",
        "admin.seal", "last_updated", "created_date", "id", "bibjson"])
    return q


def public_source(q):
    q.add_include(["admin.ticked", "admin.seal", "last_updated",
        "created_date", "id", "bibjson"])
    return q


# results filters
#################

def public_result_filter(results, unpacked=False):
    # Dealing with single unpacked result
    if unpacked:
        if "admin" in results:
            for k in list(results["admin"]):
                if k not in ["ticked", "seal"]:
                    del results["admin"][k]
        return results

    # Dealing with a list of es results
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "admin" in hit["_source"]:
                for k in list(hit["_source"]["admin"]):
                    if k not in ["ticked", "seal"]:
                        del hit["_source"]["admin"][k]

    return results


def prune_author_emails(results, unpacked=False):
    # Dealing with single unpacked ES result
    if unpacked:
        if "bibjson" in results:
            if "author" in results["bibjson"]:
                for a in results["bibjson"]["author"]:
                    if "email" in a:
                        del a["email"]
        return results

    # Dealing with a list of ES results
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "bibjson" in hit["_source"]:
                if "author" in hit["_source"]["bibjson"]:
                    for a in hit["_source"]["bibjson"]["author"]:
                        if "email" in a:
                            del a["email"]

    return results


def publisher_result_filter(results, unpacked=False):
    # Dealing with single unpacked ES result
    if unpacked:
        if "admin" in results:
            for k in list(results["admin"]):
                if k not in ["ticked", "seal", "in_doaj", "related_applications", "current_application", "current_journal", "application_status"]:
                    del results["admin"][k]
        return results

    # Dealing with a list of ES results
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "admin" in hit["_source"]:
                for k in list(hit["_source"]["admin"]):
                    if k not in ["ticked", "seal", "in_doaj", "related_applications", "current_application", "current_journal", "application_status"]:
                        del hit["_source"]["admin"][k]

    return results
