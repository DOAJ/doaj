jQuery(document).ready(function($) {

    var all_facets = {
        journal_article : {
            field : "_type",
            hidden: true
        },
        subject : {
            field: 'index.classification.exact',
            hidden: true
        },
        licence : {
            field: "index.license.exact",
            hidden: true
        },
        publisher : {
            field: "index.publisher.exact",
            hidden: true
        },
        country_publisher : {
            field: "index.country.exact",
            hidden: true
        },
        language : {
            field : "index.language.exact",
            hidden: true
        },

        // journal facets
        apc : {
            field : "index.has_apc.exact",
            hidden: true
        },
        seal : {
            field : "index.has_seal.exact",
            hidden: true
        },
        peer_review : {
            field : "bibjson.editorial_review.process.exact",
            hidden: true
        },
        year_added : {
            type: "date_histogram",
            field: "created_date",
            interval: "year",
            hidden: true
        },
        archiving_policy : {
            field : "bibjson.archiving_policy.policy.exact",
            hidden: true
        },

        // article facets
        journal_title : {
            field : "bibjson.journal.title.exact",
            hidden: true
        },
        year_published_histogram : {
            type: "date_histogram",
            field: "index.date",
            interval: "year",
            hidden: true
        },

        // toc facets
        issn : {
            field: 'index.issn.exact',
            hidden: true
        },

        volume : {
            field: 'bibjson.journal.volume.exact',
            hidden: true
        },

        issue : {
            field: 'bibjson.journal.number.exact',
            hidden: true
        },

        month_published_histogram : {
            type: 'date_histogram',
            field: 'index.date_toc_fv_month',
            interval: 'month',
            hidden: true}
    };

    var facet_list = [];
    facet_list.push(all_facets.journal_article);
    facet_list.push(all_facets.subject);
    facet_list.push(all_facets.journal_title);
    facet_list.push(all_facets.apc);
    facet_list.push(all_facets.seal);
    facet_list.push(all_facets.licence);
    facet_list.push(all_facets.publisher);
    facet_list.push(all_facets.country_publisher);
    facet_list.push(all_facets.language);
    facet_list.push(all_facets.peer_review);
    facet_list.push(all_facets.year_added);
    facet_list.push(all_facets.year_published_histogram);
    facet_list.push(all_facets.archiving_policy);
    facet_list.push(all_facets.issn);
    facet_list.push(all_facets.volume);
    facet_list.push(all_facets.issue);
    facet_list.push(all_facets.month_published_histogram);

    function publicSearchResult(options, resultobj) {
        if (resultobj.bibjson && resultobj.bibjson.journal) {
            // it is an article
            return renderPublicArticle(options, resultobj);
        } else {
            // it is a journal
            return renderPublicJournal(options, resultobj);
        }
    }

    function renderPublicJournal(options, resultobj) {

        // start off the string to be rendered
        var result = options.resultwrap_start;
        result += "<div class='row-fluid'>";

        // start the main box that all the details go in
        result += "<div class='span12'>";

        // add the journal icon
        result += "<div class='pull-left' style='width: 4%'>";
        result += "<i style='font-size: 24px' class='icon icon-book'></i>";
        result += "</div>";

        result += "<div class='pull-left' style='width: 93%'>";

        result += "<div class='row-fluid'><div class='span10'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a href='"+ doaj_url + "/toc/" + journal_toc_id(resultobj) + "'>" + escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
        }

        // set the alternative title
        if (resultobj.bibjson.alternative_title) {
            result += "<span class='alternative_title' style='color: #aaaaaa'>" + escapeHtml(resultobj.bibjson.alternative_title) + "</span><br>";
        }

        // set the issn
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            var pissns = [];
            var eissns = [];
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn") {
                    pissns.push(escapeHtml(ids[i].id))
                } else if (ids[i].type === "eissn") {
                    eissns.push(escapeHtml(ids[i].id))
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

        // close the main details box
        result += "</div>";

        // start the journal properties side-bar
        result += "<div class='span2' align='right'>";

        // licence
        if (resultobj.bibjson.license) {
            var ltitle = undefined;
            var lics = resultobj.bibjson.license;
            if (lics.length > 0) {
                ltitle = lics[0].title
            }
            if (ltitle) {
                if (licenceMap[ltitle]) {
                    var urls = licenceMap[ltitle];
                    result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + doaj_url + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
                } else {
                    result += "<strong>License: " + escapeHtml(ltitle) + "</strong><br>"
                }
            }
        }

        // show the seal if it's set
        if (resultobj.admin && resultobj.admin.seal) {
            result += "<img src='" + doaj_url + "/static/doaj/images/seal_short.png' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal'>​​<br>";
        }

        // close the journal properties side-bar
        result += "</div>";

        // close off the result with the ending strings, and then return
        result += "</div></div>";
        result += options.resultwrap_end;
        return result;
    }

    function renderPublicArticle(options, resultobj) {

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
                        issns.push(escapeHtml(ids[i].id))
                    }
                }
            }

            var citation = "";

            // journal title
            if (ctitle) {
                if (issns.length > 0) {
                    citation += "<a href='"+ doaj_url + "/toc/" + issns[0] + "'>" + escapeHtml(ctitle.trim()) + "</a>";
                } else {
                    citation += escapeHtml(ctitle.trim());
                }
                citation += ". ";
            }

            // year
            if (cyear) {
                // if (citation !== "") { citation += " " }
                citation += escapeHtml(cyear) + ";";
            }

            // volume
            if (cvol) {
                // if (citation !== "") { citation += "" }
                citation += escapeHtml(cvol);
            }

            if (ciss) {
                // if (citation !== "") { citation += ", " }
                citation += "(" + escapeHtml(ciss) + ")";
            }

            if (cstart || cend) {
                if (citation !== "") { citation += ":" }
                /*
                if ((cstart && !cend) || (!cstart && cend)) {
                    citation += "p ";
                } else {
                    citation += "Pp ";
                }
                */
                if (cstart) {
                    citation += escapeHtml(cstart);
                }
                if (cend) {
                    if (cstart) {
                        citation += "-"
                    }
                    citation += escapeHtml(cend);
                }
            }

            return citation;
        }

        // start off the string to be rendered
        var result = options.resultwrap_start;
        result += "<div class='row-fluid'>";

        // start the main box that all the details go in
        result += "<div class='span12'>";

        // add the article icon
        result += "<div class='pull-left' style='width: 4%'>";
        result += "<i style='font-size: 24px' class='icon icon-file'></i>";
        result += "</div>";

        result += "<div class='pull-left' style='width: 90%'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a href='"+ doaj_url + "/article/" + resultobj.id + "'>" + escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
        }

        // set the authors
        if (resultobj.bibjson && resultobj.bibjson.author && resultobj.bibjson.author.length > 0) {
            var anames = [];
            var authors = resultobj.bibjson.author;
            for (var i = 0; i < authors.length; i++) {
                var author = authors[i];
                if (author.name) {
                    anames.push(escapeHtml(author.name));
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
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "doi") {
                    var doi = ids[i].id;
                    var tendot = doi.indexOf("10.");
                    var url = "http://dx.doi.org/" + escapeHtml(doi.substring(tendot));
                    result += " DOI <a href='" + url + "'>" + escapeHtml(doi.substring(tendot)) + "</a>";
                }
            }
        }

        result += "<br>";

        // extract the fulltext link if there is one
        var ftl = false;
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                if (t == 'fulltext') {
                    ftl = ls[i].url;
                }
            }
        }

        // create the abstract section if desired
        if (resultobj.bibjson.abstract || ftl) {
            if (resultobj.bibjson.abstract) {
                result += '<a class="abstract_action" href="" rel="' + resultobj.id + '"><strong>Abstract</strong></a>';
            }
            if (ftl) {
                if (resultobj.bibjson.abstract) {
                    result += " | ";
                }
                result += "<a href='" + ftl + "'>Full Text</a>";
            }

            if (resultobj.bibjson.abstract) {
                result += '<div class="abstract_text" rel="' + resultobj.id + '">' + escapeHtml(resultobj.bibjson.abstract) + '</div>';
            }
        }

        // close the main details box
        result += "</div></div>";

        // close off the main result
        result += "</div>";

        // close off the result and return
        result += options.resultwrap_end;
        return result;
    }

    $('.facetview.journals_and_articles').facetview($.extend({
        search_url: doaj_url + '/query/journal,article/_search?ref=fqw',
        pushstate: false,                      // Do not use the url state, this may interfere with the host website
        render_results_metadata: doajPager,
        render_result_record: publicSearchResult,
        render_search_options: $.noop,         // The fixed query widget does not require the search box or its accoutrements
        render_facet_list: $.noop,
        behaviour_set_selected_filters : $.noop,
        post_render_callback: doajFixedQueryWidgetPostRender,
        facets: facet_list,
        default_operator : "AND"              // This can be overridden by the properties we extend from widget_fv_opts

        /* The following are the user-configurable settings for the widget, bundled in widget_fv_opts via QUERY_OPTIONS
             page_size
             from
             q
             searchfield
             sort
             default_operator
             predefined_filters
        */
    }, widget_fv_opts));
});

function iso_datetime2date(isodate_str) {
    /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
     * "2003-04-03"
     */
    return isodate_str.substring(0,10);
}

function iso_datetime2date_and_time(isodate_str) {
    /* >>> "2013-12-13T22:35:42Z".replace('T',' ').replace('Z','')
     * "2013-12-13 22:35:42"
     */
    if (!isodate_str) { return "" }
    return isodate_str.replace('T',' ').replace('Z','')
}

function journal_toc_id(journal) {
    // if e-issn is available, use that
    // if not, but a p-issn is available, use that
    // if neither ISSN is available, use the internal ID
    var ids = journal.bibjson.identifier;
    var pissns = [];
    var eissns = [];
    for (var i = 0; i < ids.length; i++) {
        if (ids[i].type === "pissn") {
            pissns.push(ids[i].id)
        } else if (ids[i].type === "eissn") {
            eissns.push(ids[i].id)
        }
    }

    var toc_id = undefined;
    if (eissns.length > 0) { toc_id = eissns[0]; }
    if (!toc_id && pissns.length > 0) { toc_id = pissns[0]; }
    if (!toc_id) { toc_id = journal.id; }

    return toc_id;
}
