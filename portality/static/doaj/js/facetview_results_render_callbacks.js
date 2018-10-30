// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner
fv_author_pays = (function(resultobj) {
    var that = function(resultobj) {
        var field = "";
        if (resultobj.bibjson && resultobj.bibjson.author_pays) {
            if(that.mapping[resultobj['bibjson']['author_pays']]) {
                var result = '<span class=' + that.mapping[resultobj['bibjson']['author_pays']]['class'] + '>';
                result += that.mapping[resultobj['bibjson']['author_pays']]['text'];
                result += '</span>';
                field += result;
            } else {
                field += resultobj['bibjson']['author_pays'];
            }
            if (resultobj.bibjson && resultobj.bibjson.author_pays_url) {
                var url = resultobj.bibjson.author_pays_url;
                field += " (see <a href='" + url + "'>" + url + "</a>)"
            }
            if (field === "") {
                return false
            }
            return field
        }
        return false;
    };
    return that;
})();

fv_author_pays.mapping = {
    "Y": {"text": "Has charges", "class": "red"},
    "N": {"text": "No charges", "class": "green"},
    "CON": {"text": "Conditional charges", "class": "blue"},
    "NY": {"text": "No info available", "class": ""}
};

fv_application_status = (function(resultobj) {
    var that = function(resultobj) {
        return that.mapping[resultobj['admin']['application_status']];
    };
    return that;
})();

// This must be updated in line with the list in formcontext/choices.py
// FIXME: eventually, JS config needs to come through from the python back-end
fv_application_status.mapping = {
    'update_request' : 'Update Request',
    'revisions_required' : 'Revisions Required',
    'pending' : 'Pending',
    'in progress' : 'In Progress',
    'completed' : 'Completed',
    'on hold' : 'On Hold',
    'ready' : 'Ready',
    'rejected' : 'Rejected',
    'accepted' : 'Accepted'
};

fv_created_date = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date(resultobj['created_date']);
    };
    return that;
})();

fv_created_date_with_time = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date_and_time(resultobj['created_date']);
    };
    return that;
})();

fv_last_updated = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date_and_time(resultobj['last_updated']);
    };
    return that;
})();

fv_last_manual_update = (function (resultobj) {
    var that = function(resultobj) {
        var man_update = resultobj['last_manual_update'];
        if (man_update == '1970-01-01T00:00:00Z')
        {
            return 'Never'
        } else {
            return iso_datetime2date_and_time(man_update);
        }
    };
    return that;
})();

fv_suggested_on = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj && resultobj['suggestion'] && resultobj['suggestion']['suggested_on']) {
            return iso_datetime2date_and_time(resultobj['suggestion']['suggested_on']);
        } else {
            return false;
        }
    };
    return that;
})();


fv_abstract = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj['bibjson']['abstract']) {
            var result = '<a class="abstract_action" href="" rel="';
            result += resultobj['id'];
            result += '">(show/hide)</a> <span class="abstract_text" rel="';
            result += resultobj['id'];
            result += '">' + '<br>';
            result += escapeHtml(resultobj['bibjson']['abstract']);
            result += '</span>';
            return result;
        }
        return false;
    };
    return that;
})();


fv_addthis = (function (resultobj) {
    var that = function(resultobj) {
        var prefix = '';
        if (resultobj.bibjson && resultobj.bibjson.journal) {
            prefix = '[OA Article]'
        }
        else {
            prefix = '[OA Journal]'
        }
        var result = '<a class="addthis_button"';
        result += ' addthis:title="' + prefix + ' ' + resultobj['bibjson']['title'] + '"';
        var query = '{"query":{"query_string":{"query":"' + resultobj['id'] + '"}}}';
        // the http: or https: scheme comes from the es_scheme global var
        result += ' addthis:url="' + es_scheme + '//' + document.domain + '/search?source=' + escape(query) + '"';
        result += ' href="' + es_scheme + '//www.addthis.com/bookmark.php?v=300&amp;pubid=ra-52ae52c34c6f0a3e"><img src="' + es_scheme + '//s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/></a>';
        return result;
    };
    return that;
})();

fv_journal_license = (function (resultobj) {
    var that = function(resultobj) {
        var title = undefined;
        if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
            var lics = resultobj["bibjson"]["journal"]["license"];
            if (lics.length > 0) {
                title = lics[0].title
            }
        }
        else if (resultobj.bibjson && resultobj.bibjson.license) {
            var lics = resultobj["bibjson"]["license"];
            if (lics.length > 0) {
                title = lics[0].title
            }
        }
        
        if (title) {
            if (CC_MAP[title]) {
                var urls = CC_MAP[title];
                // i know i know, i'm not using styles.  the attrs still work and are easier.
                return "<a href='" + urls[1] + "' title='" + title + "' target='blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + title + "'></a>"
            } else {
                return title
            }
        }
        
        return false;
    };
    return that;
})();

CC_MAP = {
    "CC BY" : ["/static/doaj/images/cc/by.png", "https://creativecommons.org/licenses/by/4.0/"],
    "CC BY-NC" : ["/static/doaj/images/cc/by-nc.png", "https://creativecommons.org/licenses/by-nc/4.0/"],
    "CC BY-NC-ND" : ["/static/doaj/images/cc/by-nc-nd.png", "https://creativecommons.org/licenses/by-nc-nd/4.0/"],
    "CC BY-NC-SA" : ["/static/doaj/images/cc/by-nc-sa.png", "https://creativecommons.org/licenses/by-nc-sa/4.0/"],
    "CC BY-ND" : ["/static/doaj/images/cc/by-nd.png", "https://creativecommons.org/licenses/by-nd/4.0/"],
    "CC BY-SA" : ["/static/doaj/images/cc/by-sa.png", "https://creativecommons.org/licenses/by-sa/4.0/"]
};

fv_title_field = (function (resultobj) {
    var that = function(resultobj) {
        var field = '<span class="title">';
        var isjournal = false;
        if (resultobj.bibjson && resultobj.bibjson.journal) {
            // this is an article
            field += "<i class='fa fa-file'></i>";
        }
        else if (resultobj.suggestion) {
            // this is a suggestion
            field += "<i class='fa fa-sign-in' style=\"margin-right: 0.5em;\"></i>";
        } else {
            // this is a journal
            field += "<i class='fa fa-book'></i>";
            isjournal = true;
        }
        if (resultobj.bibjson.title) {
            if (isjournal) {
                field += "&nbsp<a href='/toc/" + journal_toc_id(resultobj) + "'>" + escapeHtml(resultobj.bibjson.title) + "</a>";
            } else {
                field += "&nbsp" + escapeHtml(resultobj.bibjson.title);
            }
            if (resultobj.admin && resultobj.admin.ticked) {
                field += "&nbsp<img src='/static/doaj/images/tick_short.png' width='16px' height='16px' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​";
            }
            if (resultobj.admin && resultobj.admin.seal) {
                field += "&nbsp<img src='/static/doaj/images/seal_short.png' width='16px' height='16px' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal' style='padding-bottom: 3px'>​​";
            }
            return field + "</span>"
        } else {
            return false;
        }
    };
    return that;
})();

fv_doi_link = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "doi") {
                    var doi = ids[i].id;
                    var tendot = doi.indexOf("10.");
                    var url = "https://doi.org/" + doi.substring(tendot);
                    return "<a href='" + url + "'>" + escapeHtml(doi.substring(tendot)) + "</a>"
                }
            }
        }
        return false
    };
    return that;
})();

fv_links = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                var label = '';
                if (t == 'fulltext') {
                    label = 'Full text'
                } else if (t == 'homepage') {
                    label = 'Home page'
                } else {
                    label = t.substring(0, 1).toUpperCase() + t.substring(1)
                }
                return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + escapeHtml(ls[i].url) + "</a>"
            }
        }
        return false;
    };
    return that;
})();

fv_issns = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            var issns = [];
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                    issns.push(escapeHtml(ids[i].id))
                }
            }
            return issns.join(", ")
        }
        return false
    };
    return that;
})();

fv_edit_suggestion = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj['suggestion']) {
            // determine the link name
            var linkName = "Review application";
            if (resultobj.admin.application_status === 'accepted' || resultobj.admin.application_status === 'rejected') {
                linkName = "View finished application";
                if (resultobj.admin.related_journal) {
                    linkName = "View finished update";
                }
            } else if (resultobj.admin.current_journal) {
                linkName = "Review update";
            }

            var result = '<a class="edit_suggestion_link pull-right" href="';
            result += suggestion_edit_url;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>' + linkName + '</a>';
            return result;
        }
        return false;
    };
    return that;
})();

fv_readonly_journal = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.admin && resultobj.admin.current_journal) {
            var result = '<a class="readonly_journal_link pull-right" href="';
            result += readonly_journal_url;
            result += resultobj.admin.current_journal;
            result += '" target="_blank"';
            result += '>View journal being updated</a>';
            return result;
        }
        return false;
    };
    return that;
})();


fv_delete_article = (function (resultobj) {
    var that = function(resultobj) {
        if (!resultobj.suggestion && resultobj.bibjson.journal) {
            // if it's not a suggestion or a journal .. (it's an article!)
            // we really need to expose _type ...
            var result = '<a class="delete_article_link pull-right" href="';
            result += "/admin/article/";
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>Delete this article</a>';
            return result;
        }
        return false;
    };
    return that;
})();

fv_edit_journal = (function (resultobj) {
    var that = function(resultobj) {
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            // if it's not a suggestion or an article .. (it's a
            // journal!)
            // we really need to expose _type ...
            var result = '<a class="edit_journal_link pull-right" href="';
            result += journal_edit_url;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>Edit this journal</a>';
            return result;
        }
        return false;
    };
    return that;
})();

fv_make_continuation = (function (resultobj) {
    var that = function(resultobj) {
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            // if it's not a suggestion or an article .. (it's a
            // journal!)
            // we really need to expose _type ...
            var result = '<a class="edit_journal_link pull-right" href="';
            result += journal_edit_url;
            result += resultobj['id'];
            result += '/continue?type=is_replaced_by" target="_blank"';
            result += '>Make a succeeding continuation</a>';

            result += "<span class='pull-right'>&nbsp;|&nbsp;</span>";

            result += '<a class="edit_journal_link pull-right" href="';
            result += journal_edit_url;
            result += resultobj['id'];
            result += '/continue?type=replaces" target="_blank"';
            result += '>Make a preceding continuation</a>';

            return result;
        }
        return false;
    };
    return that;
})();

fv_edit_user = (function (resultobj) {
    var that = function(resultobj) {
        var result = '<a class="edit_user_link pull-right" href="';
        result += user_edit_url;
        result += resultobj['id'];
        result += '" target="_blank"';
        result += '>Edit this user</a>';
        return result;
    };
    return that;
})();


fv_in_doaj = (function(resultobj) {
    var that = function(resultobj) {
        var field = "";
        if (resultobj.admin && resultobj.admin.in_doaj !== undefined) {
            if(that.mapping[resultobj['admin']['in_doaj']]) {
                var result = '<span class=' + that.mapping[resultobj['admin']['in_doaj']]['class'] + '>';
                result += that.mapping[resultobj['admin']['in_doaj']]['text'];
                result += '</span>';
                field += result;
            } else {
                field += resultobj['admin']['in_doaj'];
            }
            if (field === "") {
                return false
            }
            return field
        }
        return false;
    };
    return that;
})();

fv_in_doaj.mapping = {
    "false": {"text": "No", "class": "red"},
    "true": {"text": "Yes", "class": "green"}
};

fv_country_name = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.index && resultobj.index.country) {
            return escapeHtml(resultobj.index.country);
        }
        return false
    };
    return that;
})();

fv_owner = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.admin && resultobj.admin.owner !== undefined && resultobj.admin.owner !== "") {
            var own = resultobj.admin.owner;
            return '<a href="/account/' + own + '">' + escapeHtml(own) + '</a>'
        }
        return false
    };
    return that;
})();

fv_user_journals = (function (resultobj) {
    var that = function(resultobj) {
        var q = {
            "query":{
                "filtered":{
                    "filter":{
                        "bool":{
                            "must":[{"term":{"admin.owner.exact":resultobj.id}}]
                        }
                    },
                    "query":{"match_all":{}}
                }
            }
        };
        // var q = {"query" : {"bool" : {"must" : [{"term" : {"admin.owner.exact" : resultobj.id}}]}}};
        return '<a class="pull-right" style="margin-left: 10px; margin-right: 10px" href="/admin/journals?source=' + encodeURIComponent(JSON.stringify(q)) + '">View Journals</a>'
    };
    return that;
})();


fv_linked_associates = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.associates) {
            var frag = "Associate Editors: ";
            for (var i = 0; i < resultobj.associates.length; i++) {
                if (i > 0) {
                    frag += ", "
                }
                var ass = resultobj.associates[i];
                frag += '<a href="/account/' + ass + '">' + escapeHtml(ass) + '</a>'
            }
            return frag
        }
        return false
    };
    return that;
})();

fv_edit_editor_group = (function (resultobj) {
    var that = function(resultobj) {
        var result = '<a style="padding-left: 10px; padding-right: 10px" class="edit_editor_group_link pull-right" href="';
        result += editor_group_edit_url;
        result += resultobj['id'];
        result += '" target="_blank"';
        result += '>Edit this group</a>';
        return result;
    };
    return that;
})();

fv_delete_editor_group = (function (resultobj) {
    var that = function(resultobj) {
        var result = '<a class="delete_editor_group_link pull-right" href="';
        result += editor_group_edit_url;
        result += resultobj['id'];
        result += '" target="_blank"';
        result += '>Delete this group</a>';
        return result;
    };
    return that;
})();

fv_edit_update_request = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj['suggestion']) {
            if (resultobj.admin && resultobj.admin.application_status) {
                var status = resultobj.admin.application_status;
                var result = "";
                var view = '(<a href="' + update_request_readonly_url + resultobj['id'] + '">view request</a>)';
                if (status === "update_request" || status == "revisions_required") {
                    var actionUrl = update_request_edit_url + resultobj.admin.current_journal;
                    result = '<span class="pull-right"><a class="edit_suggestion_link" href="' + actionUrl;
                    result += '"';
                    result += '>Edit this update request</a> | <a href="' + actionUrl + '" class="delete_suggestion_link">Delete this update request</a></span>';
                } else  if (status !== "rejected" && status !== "accepted") {
                    result = '<span class="pull-right">This update request is currently being reviewed by an Editor ' + view + '.</span>';
                } else if (status === "rejected") {
                    result = '<span class="pull-right">This update request has been rejected ' + view + '.</span>';
                } else if (status === "accepted") {
                    result = '<span class="pull-right">This update request has been accepted, and your journal in DOAJ updated ' + view + '.</span>';
                }
                return result;
            }
        }
        return false;
    };
    return that;
})();

fv_make_update_request = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.admin && resultobj.admin.hasOwnProperty("in_doaj")) {
            if (resultobj.admin.in_doaj === false) {
                return ""
            }
        }
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            // if it's not a suggestion or an article .. (it's a
            // journal!)
            // we really need to expose _type ...
            var result = "";
            if (resultobj.admin && resultobj.admin.current_application) {
                var idquery = '%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22' + resultobj['id'] + '%22%7D%7D%7D';
                result = '<a class="edit_journal_link pull-right" href="' + journal_update_requests_url + "?source=" + idquery + '">View current update request</a>';
            } else {
                result = '<a class="edit_journal_link pull-right" href="';
                result += journal_update_url;
                result += resultobj['id'] + '"';
                result += '>Submit an update</a>';
            }
            return result;
        }
        return false;
    };
    return that;
})();

fv_related_applications = (function (resultobj) {
    var that = function(resultobj) {
        var result = "";
        if (resultobj.admin) {
            if (resultobj.admin.current_application) {
                var fvurl = applications_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_application + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                result += "<strong>Current Update Request</strong>: <a href='" + fvurl + "'>" + resultobj.admin.current_application + "</a>";
            }
            if (resultobj.admin.related_applications && resultobj.admin.related_applications.length > 0) {
                if (result != "") {
                    result += "<br>";
                }
                result += "<strong>Related Records</strong>: ";
                for (var i = 0; i < resultobj.admin.related_applications.length; i++) {
                    if (i > 0) {
                        result += ", ";
                    }
                    var ra = resultobj.admin.related_applications[i];
                    var fvurl = applications_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + ra.application_id + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    var linkName = ra.date_accepted;
                    if (!linkName) {
                        linkName = ra.application_id;
                    }
                    result += "<a href='" + fvurl + "'>" + linkName + "</a>";
                }
            }
        }
        return result;
    };
    return that;
})();

fv_related_journal = (function (resultobj) {
    var that = function(resultobj) {
        var result = "";
        if (resultobj.admin) {
            if (resultobj.admin.current_journal) {
                var fvurl = journals_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_journal + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                result += "<strong>Update Request For</strong>: <a href='" + fvurl + "'>" + resultobj.admin.current_journal + '</a>';
            }
            if (resultobj.admin.related_journal) {
                 var fvurl = journals_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.related_journal + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                if (result != "") {
                    result += "<br>";
                }
                result += "<strong>Produced Journal</strong>: <a href='" + fvurl + "'>" + resultobj.admin.related_journal + '</a>';
            }
        }
        return result;
    };
    return that;
})();
