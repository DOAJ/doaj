$.extend(true, doaj, {

    fieldRender: {
        titleField : function (val, resultobj, renderer) {
            var field = '<span class="title">';
            var isjournal = false;
            if (resultobj.bibjson && resultobj.bibjson.journal) {
                // this is an article
                field += "<i class='far fa-file-alt'></i>";
            }
            else if (resultobj.suggestion) {
                // this is a suggestion
                field += "<i class='fas fa-sign-in-alt'></i>";
            } else {
                // this is a journal
                field += "<i class='fas fa-book-open'></i>";
                isjournal = true;
            }
            if (resultobj.bibjson.title) {
                if (isjournal) {
                    field += "&nbsp<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + edges.escapeHtml(resultobj.bibjson.title) + "</a>";
                } else {
                    field += "&nbsp" + edges.escapeHtml(resultobj.bibjson.title);
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
        },

        authorPays : function(val, resultobj, renderer) {
            var mapping = {
                "Y": {"text": "Has charges", "class": "red"},
                "N": {"text": "No charges", "class": "green"},
                "CON": {"text": "Conditional charges", "class": "blue"},
                "NY": {"text": "No info available", "class": ""}
            };
            var field = "";
            if (resultobj.bibjson && resultobj.bibjson.author_pays) {
                if(mapping[resultobj['bibjson']['author_pays']]) {
                    var result = '<span class=' + mapping[resultobj['bibjson']['author_pays']]['class'] + '>';
                    result += mapping[resultobj['bibjson']['author_pays']]['text'];
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
        },

        abstract : function (val, resultobj, renderer) {
            if (resultobj['bibjson']['abstract']) {
                var result = '<a class="abstract_action" href="#" rel="';
                result += resultobj['id'];
                result += '">(show/hide)</a> <span class="abstract_text" style="display:none" rel="';
                result += resultobj['id'];
                result += '">' + '<br>';
                result += edges.escapeHtml(resultobj['bibjson']['abstract']);
                result += '</span>';
                return result;
            }
            return false;
        },

        journalLicense : function (val, resultobj, renderer) {
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
                if (doaj.licenceMap[title]) {
                    var urls = doaj.licenceMap[title];
                    // i know i know, i'm not using styles.  the attrs still work and are easier.
                    return "<a href='" + urls[1] + "' title='" + title + "' target='blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + title + "'></a>"
                } else {
                    return title
                }
            }

            return false;
        },

        doiLink : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.identifier) {
                var ids = resultobj.bibjson.identifier;
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i].type === "doi") {
                        var doi = ids[i].id;
                        var tendot = doi.indexOf("10.");
                        var url = "https://doi.org/" + doi.substring(tendot);
                        return "<a href='" + url + "'>" + edges.escapeHtml(doi.substring(tendot)) + "</a>"
                    }
                }
            }
            return false
        },

        links : function (val, resultobj, renderer) {
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
                    return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + edges.escapeHtml(ls[i].url) + "</a>"
                }
            }
            return false;
        },

        issns : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.identifier) {
                var ids = resultobj.bibjson.identifier;
                var issns = [];
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                        issns.push(edges.escapeHtml(ids[i].id))
                    }
                }
                return issns.join(", ")
            }
            return false
        },

        countryName : function (val, resultobj, renderer) {
            if (resultobj.index && resultobj.index.country) {
                return edges.escapeHtml(resultobj.index.country);
            }
            return false
        },
    }

});