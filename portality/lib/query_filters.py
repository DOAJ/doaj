from flask_login import current_user
from portality.core import app
from portality import models, constants
from copy import deepcopy

# General utilities
###################


def remove_fields(query: dict, fields_to_remove: list):
    q = deepcopy(query)
    for del_attr in fields_to_remove:
        if del_attr in q:
            del q[del_attr]
    return q


# query sanitisers
##################

def public_query_validator(q):
    # no deep paging
    if (q.from_result()+q.size()) > 10000:
        return False

    return True


def non_public_fields_validator(q):
    exclude_fields = app.config.get("PUBLIC_QUERY_VALIDATOR__EXCLUDED_FIELDS", {})
    context = q.get_field_context()
    if context:
        if "default_field" in context:
            field_value = context["default_field"]
            if field_value in exclude_fields:
                return False
    return True

# query filters
###############

def remove_search_limits(query: dict):
    return remove_fields(query, ['size', 'from'])


def only_in_doaj(q):
    q.clear_match_all()
    q.add_must_filter({"term": {"admin.in_doaj": True}})
    return q


def search_all_meta(q):
    """Search by all_meta field, which is a concatenation of all the fields in the record"""
    q.add_default_field("all_meta")
    return q


def journal_article_filter(q):
    """Search by all_meta field for journal and all fields for article"""
    search_text = None
    context = q.get_field_context()
    if isinstance(context, list):
        for item in context:
            if "query_string" in item:
                search_text = item["query_string"]["query"]
                if "default_field" in item["query_string"]:
                    return q
    elif isinstance(context, dict):
        if "query_string" in context:
            search_text = context["query_string"]["query"]
            if "default_field" in context["query_string"]:
                return q
    q.convert_to_bool()
    if search_text:
        filter = [{"bool": {"must": [{"term": {"es_type.exact": "article"}},
                            {"query_string": {"default_field": "*", "query": search_text}}]}},
                  {"bool": {"must": [{"term": {"es_type.exact": "journal"}},
                            {"query_string": {"default_field": "all_meta", "query": search_text}}]}}]
        q.add_should(filter)
    return q


def owner(q):
    q.clear_match_all()
    q.add_must_filter({"term" : {"admin.owner.exact" : current_user.id}})
    return q


def update_request(q):
    q.clear_match_all()
    q.add_must_filter({"range" : {"admin.date_applied" : {"gte" : app.config.get("UPDATE_REQUESTS_SHOW_OLDEST")}}})
    q.add_must_filter({"term" : {"admin.application_type.exact" : constants.APPLICATION_TYPE_UPDATE_REQUEST}})
    return q


def not_update_request(q):
    q.clear_match_all()
    q.add_must_filter({"term" : {"admin.application_type.exact" : constants.APPLICATION_TYPE_NEW_APPLICATION}})
    return q


def associate(q):
    q.clear_match_all()
    q.add_must_filter({"term" : {"admin.editor.exact" : current_user.id}})
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
    q.add_include(["admin.application_status", "admin.ticked",
        "last_updated", "created_date", "id", "bibjson"])
    return q


def public_source(q):
    q.add_include(["admin.ticked", "last_updated",
        "created_date", "id", "bibjson"])
    return q


def strip_facets(q):
    q.clear_facets()
    return q


def es_type_fix(q):
    # FIXME: document this and will need attention for ES 7 upgrade
    ctx = q.as_dict()
    if "query" not in ctx:
        return q
    ctx = ctx["query"]
    if "filtered" not in ctx:
        return q
    ctx = ctx["filtered"]
    if "filter" not in ctx:
        return q
    ctx = ctx["filter"]
    if "bool" not in ctx:
        return q
    ctx = ctx["bool"]
    if "must" not in ctx:
        return q
    ctx = ctx["must"]
    for m in ctx:
        if "term" in m and "_type" in m["term"]:
            m["term"] = {"es_type" : m["term"]["_type"]}
    return q


def last_update_fallback(q):
    s = q.sort()
    if s is None or len(s) == 0:
        return q

    add_created_sort = False
    sort_order = None
    for sortby in s:
        if "last_manual_update" in sortby:
            sort_order = sortby["last_manual_update"].get("order")
            add_created_sort = True
            break

    if add_created_sort:
        params = {}
        if sort_order is not None:
            params["order"] = sort_order
        s.append({"created_date" : params})

    q.set_sort(s)
    return q


# ~~WhoCurrentUser:Query~~
def who_current_user(q):
    q.clear_match_all()
    q.add_must_filter({"term": {"who.exact": current_user.id}})
    return q

# results filters
#################

def public_result_filter(results, unpacked=False):
    # Dealing with single unpacked result
    if unpacked:
        if "admin" in results:
            for k in list(results["admin"]):
                if k not in ["ticked"]:
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
                    if k not in ["ticked"]:
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
    allowed_admin = ["ticked", "in_doaj", "related_applications", "current_application", "current_journal", "application_status"]
    # Dealing with single unpacked ES result
    if unpacked:
        if "admin" in results:
            for k in list(results["admin"]):
                if k not in allowed_admin:
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
                    if k not in allowed_admin:
                        del hit["_source"]["admin"][k]

    return results


def add_fqw_facets(results, unpacked=False):
    if unpacked:
        return results

    facets = {
        "index.license.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "bibjson.journal.title.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "bibjson.archiving_policy.policy.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "created_date": {
            "_type": "date_histogram",
            "entries": []
        },
        "index.country.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.date": {
            "_type": "date_histogram",
            "entries": []
        },
        "bibjson.journal.volume.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.publisher.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.has_apc.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "bibjson.editorial_review.process.exact": {
            "_type": "match",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.language.exact": {
            "_type": "match",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "bibjson.journal.number.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.date_toc_fv_month": {
            "_type": "date_histogram",
            "entries": []
        },
        "index.classification.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "_type": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        },
        "index.issn.exact": {
            "_type": "terms",
            "missing": 0,
            "total": 0,
            "other": 0,
            "terms": []
        }
    }

    results["aggregations"] = facets
    return results


def fqw_back_compat(results, unpacked=False):
    if unpacked:
        return results

    # Dealing with a list of ES results
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if hit.get("_source").get("es_type") != "journal":
            continue

        identifiers = []
        bj = hit.get("_source", {}).get("bibjson", {})
        if bj.get("pissn"):
            identifiers.append({"type" : "pissn", "id" : bj.get("pissn")})
        if bj.get("eissn"):
            identifiers.append({"type" : "eissn", "id" : bj.get("eissn")})

        bj["identifier"] = identifiers

    return results