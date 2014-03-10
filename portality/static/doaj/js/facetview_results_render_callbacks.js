// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner
fv_author_pays = (function(resultobj) {
    var that = function(resultobj) {
        field = ""
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
                url = resultobj.bibjson.author_pays_url
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
    "NY": {"text": "No info available", "class": ""},
}

fv_created_date = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date(resultobj['created_date']);
    };
    return that;
})();

fv_last_updated = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date_and_time(resultobj['last_updated']);
    };
    return that;
})();


fv_abstract = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj['bibjson']['abstract']) {
            var result = '<a class="abstract_action" href="" rel="';
            result += resultobj['id'];
            result += '">(expand)</a> <span class="abstract_text" rel="';
            result += resultobj['id'];
            result += '">' + '<br>';
            result += resultobj['bibjson']['abstract'];
            result += '</span>';
            return result;
        }
        return false;
    };
    return that;
})();


fv_addthis = (function (resultobj) {
    var that = function(resultobj) {
        var prefix = ''
        if (resultobj.bibjson && resultobj.bibjson.journal) {
            prefix = '[OA Article]'
        }
        else {
            prefix = '[OA Journal]'
        }
        var result = '<a class="addthis_button"';
        result += ' addthis:title="' + prefix + ' ' + resultobj['bibjson']['title'] + '"';
        var query = '{"query":{"query_string":{"query":"' + resultobj['id'] + '"}}}';
        result += ' addthis:url="http://' + document.domain + '/search?source=' + escape(query) + '"';
        result += ' href="http://www.addthis.com/bookmark.php?v=300&amp;pubid=ra-52ae52c34c6f0a3e"><img src="http://s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/></a>';
        return result;
    };
    return that;
})();

fv_journal_license = (function (resultobj) {
    var that = function(resultobj) {
        var title = undefined
        if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
            var lics = resultobj["bibjson"]["journal"]["license"]
            if (lics.length > 0) {
                title = lics[0].title
            }
        }
        else if (resultobj.bibjson && resultobj.bibjson.license) {
            var lics = resultobj["bibjson"]["license"]
            if (lics.length > 0) {
                title = lics[0].title
            }
        }
        
        if (title) {
            if (CC_MAP[title]) {
                urls = CC_MAP[title]
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
    "CC by" : ["/static/doaj/images/cc/by.png", "http://creativecommons.org/licenses/by/3.0/"],
    "CC by-nc" : ["/static/doaj/images/cc/by-nc.png", "http://creativecommons.org/licenses/by-nc/3.0/"],
    "CC by-nc-nd" : ["/static/doaj/images/cc/by-nc-nd.png", "http://creativecommons.org/licenses/by-nc-nd/3.0/"],
    "CC by-nc-sa" : ["/static/doaj/images/cc/by-nc-sa.png", "http://creativecommons.org/licenses/by-nc-sa/3.0/"],
    "CC by-nd" : ["/static/doaj/images/cc/by-nd.png", "http://creativecommons.org/licenses/by-nd/3.0/"],
    "CC by-sa" : ["/static/doaj/images/cc/by-sa.png", "http://creativecommons.org/licenses/by-sa/3.0/"]
}

fv_title_field = (function (resultobj) {
    var that = function(resultobj) {
        var field = '<span class="title">'
        if (resultobj.bibjson && resultobj.bibjson.journal) {
            // this is an article
            field += "<i class='icon icon-file'></i> "
        }
        else if (resultobj.suggestion) {
            // this is a suggestion
            field += "<i class='icon icon-signin' style=\"margin-right: 0.5em;\"></i>"
        } else {
            // this is a journal
            field += "<i class='icon icon-book'></i> "
        }
        if (resultobj.bibjson.title) {
            field += resultobj.bibjson.title + "</span>"
            return field
        } else {
            return false
        }
    };
    return that;
})();

fv_doi_link = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "doi") {
                    var doi = ids[i].id
                    var tendot = doi.indexOf("10.")
                    var url = "http://dx.doi.org/" + doi.substring(tendot)
                    return "<a href='" + url + "'>" + doi.substring(tendot) + "</a>"
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
            var ls = resultobj.bibjson.link
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type
                var label = ''
                if (t == 'fulltext') {
                    label = 'Full text'
                } else if (t == 'homepage') {
                    label = 'Home page'
                } else {
                    label = t.substring(0, 1).toUpperCase() + t.substring(1)
                }
                return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + ls[i].url + "</a>"
            }
        }
        return false;
    };
    return that;
})();

fv_issns = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier
            var issns = []
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                    issns.push(ids[i].id)
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
            var result = '<a class="edit_suggestion_link pull-right" href="';
            result += suggestion_edit_url;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>Edit this suggestion</a>';
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
        field = ""
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
    false: {"text": "No", "class": "red"},
    true: {"text": "Yes", "class": "green"},
}

fv_country_name = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.index && resultobj.index.country) {
            return resultobj.index.country;
        }
        return false
    };
    return that;
})();
