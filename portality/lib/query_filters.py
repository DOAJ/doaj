from flask_login import current_user
from portality.core import app
from portality import models

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


# results filters
#################

def public_result_filter(results):
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "admin" in hit["_source"]:
                for k in hit["_source"]["admin"].keys():
                    if k not in ["ticked", "seal"]:
                        del hit["_source"]["admin"][k]

    return results


def prune_author_emails(results):
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "bibjson" in hit["_source"]:
                if "author" in hit["_source"]["bibjson"]:
                    for a in hit["_source"]["bibjson"]["author"]:
                        del a["email"]


def publisher_result_filter(results):
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "admin" in hit["_source"]:
                for k in hit["_source"]["admin"].keys():
                    if k not in ["ticked", "seal", "in_doaj", "related_applications", "current_application", "current_journal", "application_status"]:
                        del hit["_source"]["admin"][k]

    return results
