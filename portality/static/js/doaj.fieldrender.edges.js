$.extend(true, doaj, {
    valueMaps : {
        // This must be updated in line with the list in formcontext/choices.py
        applicationStatus : {
            'update_request' : 'Update Request',
            'revisions_required' : 'Revisions Required',
            'pending' : 'Pending',
            'in progress' : 'In Progress',
            'completed' : 'Completed',
            'on hold' : 'On Hold',
            'ready' : 'Ready',
            'rejected' : 'Rejected',
            'accepted' : 'Accepted'
        }
    },

    renderers : {
        newPublicSearchResultRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublicSearchResultRenderer, params, edges.newRenderer);
        },
        PublicSearchResultRenderer : function(params) {
            this.namespace = "doaj-public-search";

            this.draw = function () {
                var frag = "No results found that match your search criteria.  Try removing some of the filters you have set, or modifying the text in the search box.";
                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // list the css classes we'll require
                    var recordClasses = edges.css_classes(this.namespace, "record", this);

                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        var rec = this._renderResult(results[i]);
                        frag += '<div class="row"><div class="col-md-12"><div class="' + recordClasses + '">' + rec + '</div></div></div>';
                    }
                }

                // finally stick it all together into the container
                var containerClasses = edges.css_classes(this.namespace, "container", this);
                var container = '<div class="' + containerClasses + '">' + frag + '</div>';
                this.component.context.html(container);

                // now bind the abstract expander
                var abstractAction = edges.css_class_selector(this.namespace, "abstractaction", this);
                edges.on(abstractAction, "click", this, "toggleAbstract");
            };

            this.toggleAbstract = function(element) {
                var el = $(element);
                var abstractText = edges.css_class_selector(this.namespace, "abstracttext", this);
                var at = this.component.jq(abstractText).filter('[rel="' + el.attr("rel") + '"]');
                at.slideToggle(300);
            };

            this._renderResult = function(resultobj) {
                if (resultobj.bibjson && resultobj.bibjson.journal) {
                    // it is an article
                    return this._renderPublicArticle(resultobj);
                } else {
                    // it is a journal
                    return this._renderPublicJournal(resultobj);
                }
            };

            this._renderPublicJournal = function(resultobj) {

                // start off the string to be rendered
                var result = "<div class='row'>";

                // start the main box that all the details go in
                result += "<div class='col-md-12'>";

                // add the journal icon
                result += "<div class='pull-left' style='width: 4%'>";
                result += "<i style='font-size: 24px' class='fas fa-book-open'></i>";
                result += "</div>";

                result += "<div class='pull-left' style='width: 93%'>";

                result += "<div class='row'><div class='col-md-10'>";

                // set the title
                if (resultobj.bibjson.title) {
                    result += "<span class='title'><a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + edges.escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
                }

                // set the alternative title
                if (resultobj.bibjson.alternative_title) {
                    result += "<span class='alternative_title' style='color: #aaaaaa'>" + edges.escapeHtml(resultobj.bibjson.alternative_title) + "</span><br>";
                }

                // set the issn
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    var pissns = [];
                    var eissns = [];
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "pissn") {
                            pissns.push(edges.escapeHtml(ids[i].id))
                        } else if (ids[i].type === "eissn") {
                            eissns.push(edges.escapeHtml(ids[i].id))
                        }
                    }
                    if (pissns.length > 0 || eissns.length > 0) {
                        result += "ISSN: ";
                        if (pissns.length > 0) {
                            result += pissns.join(", ") + "&nbsp;(Print)";
                        }
                        if (eissns.length > 0) {
                            if (pissns.length > 0) {
                                result += "; ";
                            }
                            result += eissns.join(", ") + "&nbsp;(Online)";
                        }
                        result += "<br>";
                    }
                }

                // set the homepage url
                // FIXME: how to escape the html here?
                if (resultobj.bibjson && resultobj.bibjson.link) {
                    var ls = resultobj.bibjson.link;
                    for (var i = 0; i < ls.length; i++) {
                        var t = ls[i].type;
                        if (t == 'homepage') {
                            result += "<a href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
                        }
                    }
                }

                // peer review type
                if (resultobj.bibjson.editorial_review && resultobj.bibjson.editorial_review.process) {
                    var proc = resultobj.bibjson.editorial_review.process;
                    if (proc === "None") {
                        proc = "No peer review"
                    }
                    result += proc + "<br>";
                }

                // add the subjects
                if (resultobj.index && resultobj.index.classification_paths && resultobj.index.classification_paths.length > 0) {
                    result += "<strong>Subject:</strong>&nbsp;";
                    result += resultobj.index.classification_paths.join(" | ") + "<br>";
                }

                // add the date added to doaj
                if (resultobj.created_date) {
                    result += "<strong>Date added to DOAJ</strong>:&nbsp;";
                    result += doaj.humanDate(resultobj.created_date) + "<br>";
                }

                if (resultobj.last_manual_update && resultobj.last_manual_update !== '1970-01-01T00:00:00Z') {
                    result += "<strong>Record Last Updated</strong>:&nbsp;";
                    result += doaj.humanDate(resultobj.last_manual_update);
                }

                // close the main details box
                result += "</div>";

                // start the journal properties side-bar
                result += "<div class='col-md-2' align='right'>";

                // licence
                if (resultobj.bibjson.license) {
                    var ltitle = undefined;
                    var lics = resultobj.bibjson.license;
                    if (lics.length > 0) {
                        ltitle = lics[0].title
                    }
                    if (ltitle) {
                        if (doaj.licenceMap[ltitle]) {
                            var urls = doaj.licenceMap[ltitle];
                            result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
                        } else {
                            result += "<strong>License: " + edges.escapeHtml(ltitle) + "</strong><br>"
                        }
                    }
                }

                // set the tick if it is relevant
                if (resultobj.admin && resultobj.admin.ticked) {
                    result += "<img src='/static/doaj/images/tick_short.png' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014'>​​<br>";
                }

                // show the seal if it's set
                if (resultobj.admin && resultobj.admin.seal) {
                    result += "<img src='/static/doaj/images/seal_short.png' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal'>​​<br>";
                }

                // APC
                if (resultobj.bibjson.apc) {
                    if (resultobj.bibjson.apc.currency || resultobj.bibjson.apc.average_price) {
                        result += "<strong>APC: ";
                        if (resultobj.bibjson.apc.average_price) {
                            result += edges.escapeHtml(resultobj.bibjson.apc.average_price);
                        } else {
                            result += "price unknown ";
                        }
                        if (resultobj.bibjson.apc.currency) {
                            result += edges.escapeHtml(resultobj.bibjson.apc.currency);
                        } else {
                            result += " currency unknown";
                        }
                        result += "</strong>";
                    } else {
                        result += "<strong>No APC</strong>";
                    }
                    result += "<br>";
                }

                // discontinued date
                var isreplaced = resultobj.bibjson.is_replaced_by && resultobj.bibjson.is_replaced_by.length > 0;
                if (resultobj.bibjson.discontinued_date || isreplaced) {
                    result += "<strong>Discontinued</strong>";
                }

                // close the journal properties side-bar
                result += "</div>";

                // close off the result with the ending strings, and then return
                result += "</div></div>";
                return result;
            };

            this._renderPublicArticle = function(resultobj) {

                function makeCitation(record) {
                    // Journal name. YYYY;32(4):489-98

                    // get all the relevant citation properties
                    var ctitle = record.bibjson.journal ? record.bibjson.journal.title : undefined;
                    var cvol = record.bibjson.journal ? record.bibjson.journal.volume : undefined;
                    var ciss = record.bibjson.journal ? record.bibjson.journal.number: undefined;
                    var cstart = record.bibjson.start_page;
                    var cend = record.bibjson.end_page;
                    var cyear = record.bibjson.year;

                    // we're also going to need the issn
                    var issns = [];
                    if (resultobj.bibjson && resultobj.bibjson.identifier) {
                        var ids = resultobj.bibjson.identifier;
                        for (var i = 0; i < ids.length; i++) {
                            if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                                issns.push(edges.escapeHtml(ids[i].id))
                            }
                        }
                    }

                    var citation = "";

                    // journal title
                    if (ctitle) {
                        if (issns.length > 0) {
                            citation += "<a href='/toc/" + issns[0] + "'>" + edges.escapeHtml(ctitle.trim()) + "</a>";
                        } else {
                            citation += edges.escapeHtml(ctitle.trim());
                        }
                        citation += ". ";
                    }

                    // year
                    if (cyear) {
                        citation += edges.escapeHtml(cyear) + ";";
                    }

                    // volume
                    if (cvol) {
                        citation += edges.escapeHtml(cvol);
                    }

                    if (ciss) {
                        citation += "(" + edges.escapeHtml(ciss) + ")";
                    }

                    if (cstart || cend) {
                        if (citation !== "") { citation += ":" }
                        if (cstart) {
                            citation += edges.escapeHtml(cstart);
                        }
                        if (cend) {
                            if (cstart) {
                                citation += "-"
                            }
                            citation += edges.escapeHtml(cend);
                        }
                    }

                    return citation;
                }

                // start off the string to be rendered
                var result = "<div class='row'>";

                // start the main box that all the details go in
                result += "<div class='col-md-12'>";

                // add the article icon
                result += "<div class='pull-left' style='width: 4%'>";
                result += "<i style='font-size: 24px' class='far fa-file-alt'></i>";
                result += "</div>";

                result += "<div class='pull-left' style='width: 90%'>";

                result += "<div class='row'><div class='col-md-10'>";

                // set the title
                if (resultobj.bibjson.title) {
                    result += "<span class='title'><a href='/article/" + resultobj.id + "'>" + edges.escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
                }

                // set the authors
                if (resultobj.bibjson && resultobj.bibjson.author && resultobj.bibjson.author.length > 0) {
                    var anames = [];
                    var authors = resultobj.bibjson.author;
                    for (var i = 0; i < authors.length; i++) {
                        var author = authors[i];
                        if (author.name) {
                            anames.push(edges.escapeHtml(author.name));
                        }
                    }
                    result += "<em>" + anames.join(", ") + "</em><br>";
                }

                // set the citation
                var cite = makeCitation(resultobj);
                if (cite) {
                    result += cite;
                }

                // set the doi
                var doi_url = false;
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "doi") {
                            var doi = ids[i].id;
                            var tendot = doi.indexOf("10.");
                            doi_url = "https://doi.org/" + edges.escapeHtml(doi.substring(tendot));
                            result += " DOI <a href='" + doi_url + "'>" + edges.escapeHtml(doi.substring(tendot)) + "</a>";
                        }
                    }
                }

                result += "<br>";

                // extract the fulltext link if there is one
                var ftl = false;
                if (resultobj.bibjson && resultobj.bibjson.link && resultobj.bibjson.link.length !== 0) {
                    var ls = resultobj.bibjson.link;
                    for (var i = 0; i < ls.length; i++) {
                        var t = ls[i].type;
                        if (t === 'fulltext') {
                            ftl = ls[i].url;
                        }
                    }
                } else if (doi_url) {
                    ftl = doi_url;
                }

                // create the abstract section if desired
                if (resultobj.bibjson.abstract || ftl) {
                    if (resultobj.bibjson.abstract) {
                        var abstractAction = edges.css_classes(this.namespace, "abstractaction", this);
                        result += '<a class="' + abstractAction + '" href="#" rel="' + resultobj.id + '"><strong>Abstract</strong></a>';
                    }
                    if (ftl) {
                        if (resultobj.bibjson.abstract) {
                            result += " | ";
                        }
                        result += "<a href='" + ftl + "'>Full Text</a>";
                    }

                    if (resultobj.bibjson.abstract) {
                        var abstractText = edges.css_classes(this.namespace, "abstracttext", this);
                        result += '<div class="' + abstractText + '" rel="' + resultobj.id + '" style="display:none">' + edges.escapeHtml(resultobj.bibjson.abstract) + '</div>';
                    }
                }

                // close the main details box
                result += "</div>";

                // start the journal properties side-bar
                result += "<div class='col-md-2' align='right'>";

                // show the seal if it's set
                if (resultobj.admin && resultobj.admin.seal) {
                    result += "<img src='/static/doaj/images/seal_short.png' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal'>​​<br>";
                }

                // close the journal properties side-bar
                result += "</div>";

                // close off the main result
                result += "</div></div>";

                // close off the result and return
                return result;
            };
        },
    },

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

        inDoaj : function(val, resultobj, renderer) {
            var mapping = {
                "false": {"text": "No", "class": "red"},
                "true": {"text": "Yes", "class": "green"}
            };
            var field = "";
            if (resultobj.admin && resultobj.admin.in_doaj !== undefined) {
                if(mapping[resultobj['admin']['in_doaj']]) {
                    var result = '<span class=' + mapping[resultobj['admin']['in_doaj']]['class'] + '>';
                    result += mapping[resultobj['admin']['in_doaj']]['text'];
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
        },

        owner : function (val, resultobj, renderer) {
            if (resultobj.admin && resultobj.admin.owner !== undefined && resultobj.admin.owner !== "") {
                var own = resultobj.admin.owner;
                return '<a href="/account/' + own + '">' + edges.escapeHtml(own) + '</a>'
            }
            return false
        },

        createdDateWithTime : function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['created_date']);
        },

        lastManualUpdate : function (val, resultobj, renderer) {
            var man_update = resultobj['last_manual_update'];
            if (man_update === '1970-01-01T00:00:00Z')
            {
                return 'Never'
            } else {
                return doaj.iso_datetime2date_and_time(man_update);
            }
        },

        suggestedOn : function (val, resultobj, renderer) {
            if (resultobj && resultobj['suggestion'] && resultobj['suggestion']['suggested_on']) {
                return doaj.iso_datetime2date_and_time(resultobj['suggestion']['suggested_on']);
            } else {
                return false;
            }
        },

        applicationStatus : function(val, resultobj, renderer) {
            return doaj.valueMaps.applicationStatus[resultobj['admin']['application_status']];
        },

        editSuggestion : function(params) {
            return function (val, resultobj, renderer) {
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

                    var result = '<a class="edit_suggestion_link" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>' + linkName + '</a>';
                    return result;
                }
                return false;
            }
        },

        readOnlyJournal : function(params) {
            return function (val, resultobj, renderer) {
                if (resultobj.admin && resultobj.admin.current_journal) {
                    var result = '<a style="margin-left: 10px; margin-right: 10px" class="readonly_journal_link" href="';
                    result += params.readOnlyJournalUrl;
                    result += resultobj.admin.current_journal;
                    result += '" target="_blank"';
                    result += '>View journal being updated</a>';
                    return result;
                }
                return false;
            }
        },

        editJournal : function(params) {
            return function (val, resultobj, renderer) {
                if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                    // if it's not a suggestion or an article .. (it's a
                    // journal!)
                    // we really need to expose _type ...
                    var result = '<a class="edit_journal_link" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>Edit this journal</a>';
                    return result;
                }
                return false;
            }
        },
    }

});