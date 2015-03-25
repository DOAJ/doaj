jQuery(document).ready(function($) {

    var all_facets = {
        journal_article : {
            field : "_type",
            display: "Journals vs Articles",
            size : 2,
            order : "reverse_term",
            controls: false,
            open: true,
            value_function : function(val) {
                if (val === "journal") {return "Journal"}
                else if (val === "article") { return "Article" }
                return val
            }
        },
        subject : {
            field: 'index.classification.exact',
            display: 'Subject'
        },
        licence : {
            field: "index.license.exact",
            display: "Journal license"
        },
        publisher : {
            field: "index.publisher.exact",
            display: "Publisher"
        },
        country_publisher : {
            field: "index.country.exact",
            display: "Country of publisher"
        },
        language : {
            field : "index.language.exact",
            display: "Fulltext language"
        },

        // journal facets
        peer_review : {
            field : "bibjson.editorial_review.process.exact",
            display : "Peer review",
            disabled: true
        },
        year_added : {
            type: "date_histogram",
            field: "created_date",
            interval: "year",
            display: "Date added to DOAJ",
            value_function : function(val) {
                return (new Date(parseInt(val))).getFullYear();
            },
            size: false,
            sort: "desc",
            disabled: true
        },

        // article facets
        journal_title : {
            field : "bibjson.journal.title.exact",
            display: "Journal",
            disabled: true
        },
        year_published : {
            field : "bibjson.year.exact",
            display: "Year of publication",
            order: "reverse_term",
            disabled: true
        }
    };

    var natural = [];
    natural.push(all_facets.journal_article);
    natural.push(all_facets.subject);
    natural.push(all_facets.licence);
    natural.push(all_facets.publisher);
    natural.push(all_facets.country_publisher);
    natural.push(all_facets.language);
    natural.push(all_facets.peer_review);
    natural.push(all_facets.year_added);
    natural.push(all_facets.journal_title);
    natural.push(all_facets.year_published);

    function dynamicFacets(options, context) {
        function disableFacet(options, field, disable) {
            for (var i = 0; i < options.facets.length; i++) {
                var facet = options.facets[i];
                if (facet.field === field) {
                    facet.disabled = disable;
                    return;
                }
            }
        }


        if ("_type" in options.active_filters) {
            // add the type specific facets to the query, and remove any
            // type specific facets from the other type, along with any filters
            // it may have set
            var ts = options.active_filters["_type"];
            if (ts.length > 0) {
                var t = ts[0];  // "journal" or "article"
                if (t === "journal") {
                    // disable the article facets
                    disableFacet(options, "bibjson.journal.title.exact", true);
                    disableFacet(options, "bibjson.year.exact", true);

                    // enable the journal facets
                    disableFacet(options, "bibjson.editorial_review.process.exact", false);
                    disableFacet(options, "created_date", false);

                    // FIXME: do we need to do something about filters here too?
                } else if (t === "article") {
                    // disable the journal facets
                    disableFacet(options, "bibjson.editorial_review.process.exact", true);
                    disableFacet(options, "created_date", true);

                    // enable the article facets
                    disableFacet(options, "bibjson.journal.title.exact", false);
                    disableFacet(options, "bibjson.year.exact", false);

                    // FIXME: do we need to do something about filters here too?
                }
            }

        } else {
            // ensure the type specific facets are not in the query

            // disable the article facets
            disableFacet(options, "bibjson.journal.title.exact", true);
            disableFacet(options, "bibjson.year.exact", true);

            // disable the journal facets
            disableFacet(options, "bibjson.editorial_review.process.exact", true);
            disableFacet(options, "created_date", true);
        }
    }

    function bitlyShortener(query, callback) {

        function callbackWrapper(data) {
            callback(data.url);
        }

        function errorHandler() {
            alert("Sorry, we're unable to generate short urls at this time");
            callback();
        }

        var postdata = JSON.stringify(query);

        $.ajax({
            type: "POST",
            contentType: "application/json",
            dataType: "jsonp",
            url: "/service/shorten",
            data : postdata,
            success: callbackWrapper,
            error: errorHandler
        });
    }

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

        // add the journal icon
        result += "<div class='span1'>";
        result += "<i style='font-size: 24px' class='icon icon-book'></i>";
        result += "</div>";

        // start the main box that all the details go in
        result += "<div class='span9'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a href='/toc/" + resultobj.id + "'>" + resultobj.bibjson.title + "</a></span><br>";
        }

        // set the alternative title
        if (resultobj.bibjson.alternative_title) {
            result += "<span class='alternative_title' style='color: #aaaaaa'>" + resultobj.bibjson.alternative_title + "</span><br>";
        }

        // set the issn
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            var issns = [];
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                    issns.push(ids[i].id)
                }
            }
            if (issns.length > 0) {
                result += "ISSN: " + issns.join(", ") + "<br>"
            }
        }

        // set the homepage url
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                if (t == 'homepage') {
                    result += "<a href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
                }
            }
        }

        // add the subjects
        if (resultobj.index && resultobj.index.classification_paths && resultobj.index.classification_paths.length > 0) {
            result += "<strong>Subjects:</strong>&nbsp;";
            result += resultobj.index.classification_paths.join(" | ");
        }

        // close the main details box
        result += "</div>";

        // start the journal properties side-bar
        result += "<div class='span2'>";

        // set the tick if it is relevant
        if (resultobj.admin && resultobj.admin.ticked) {
            result += "<img src='/static/doaj/images/tick_long.png' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​<br>";
        }

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
                    result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
                } else {
                    result += "<strong>License: " + ltitle + "</strong><br>"
                }
            }
        }

        // peer review type
        if (resultobj.bibjson.editorial_review && resultobj.bibjson.editorial_review.process) {
            var proc = resultobj.bibjson.editorial_review.process;
            if (proc === "None") {
                proc = "No peer review"
            }
            result += "<strong>" + proc + "</strong><br>"
        }

        // APC
        if (resultobj.bibjson.apc) {
            if (resultobj.bibjson.apc.currency || resultobj.bibjson.apc.average_price) {
                result += "<strong>APC: ";
                if (resultobj.bibjson.apc.average_price) {
                    result += resultobj.bibjson.apc.average_price;
                } else {
                    result += "price unknown ";
                }
                if (resultobj.bibjson.apc.currency) {
                    result += resultobj.bibjson.apc.currency
                } else {
                    result += " currency unknown";
                }
                result += "</strong>";
            } else {
                result += "<strong>No APC</strong>";
            }
        }

        // close the journal properties side-bar
        result += "</div>";

        // close off the result with the ending strings, and then return
        result += "</div>";
        result += options.resultwrap_end;
        return result;
    }

    function renderPublicArticle(options, resultobj) {

        function makeCitation(record) {
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
                        issns.push(ids[i].id)
                    }
                }
            }

            var citation = "";
            if (ctitle) {
                if (issns.length > 0) {
                    citation += "<a href='/toc/" + issns[0] + "'>" + ctitle + "</a>";
                } else {
                    citation += ctitle;
                }
            }

            if (cvol) {
                if (citation !== "") { citation += ", " }
                citation += "Vol " + cvol;
            }

            if (ciss) {
                if (citation !== "") { citation += ", " }
                citation += "Iss " + ciss;
            }

            if (cstart || cend) {
                if (citation !== "") { citation += ", " }
                if ((cstart && !cend) || (!cstart && cend)) {
                    citation += "p ";
                } else {
                    citation += "Pp ";
                }
                if (cstart) {
                    citation += cstart;
                }
                if (cend) {
                    if (cstart) {
                        citation += "-"
                    }
                    citation += cend;
                }
            }

            if (cyear) {
                if (citation !== "") { citation += " " }
                citation += "(" + cyear + ")";
            }

            return citation;
        }

        // start off the string to be rendered
        var result = options.resultwrap_start;
        result += "<div class='row-fluid'>";

        // add the journal icon
        result += "<div class='span1'>";
        result += "<i style='font-size: 24px' class='icon icon-file'></i>";
        result += "</div>";

        // start the main box that all the details go in
        result += "<div class='span9'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a href='/article/" + resultobj.id + "'>" + resultobj.bibjson.title + "</a></span><br>";
        }

        // set the doi
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "doi") {
                    var doi = ids[i].id;
                    var tendot = doi.indexOf("10.");
                    var url = "http://dx.doi.org/" + doi.substring(tendot);
                    result += "DOI: <a href='" + url + "'>" + doi.substring(tendot) + "</a><br>";
                }
            }
        }

        // set the citation
        var cite = makeCitation(resultobj);
        if (cite) {
            result += cite + "<br>";
        }

        // set the fulltext
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                if (t == 'fulltext') {
                    result += "Fulltext: <a href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
                }
            }
        }

        // close the main details box
        result += "</div>";

        // start the journal properties side-bar
        result += "<div class='span2'>";

        // set the tick if it is relevant
        if (resultobj.admin && resultobj.admin.ticked) {
            result += "<img src='/static/doaj/images/tick_long.png' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​<br>";
        }

        // licence
        if (resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
            var ltitle = undefined;
            var lics = resultobj.bibjson.journal.license;
            if (lics.length > 0) {
                ltitle = lics[0].title
            }
            if (ltitle) {
                if (licenceMap[ltitle]) {
                    var urls = licenceMap[ltitle];
                    result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
                } else {
                    result += "<strong>License: " + ltitle + "</strong><br>"
                }
            }
        }

        // close the article properties side-bar
        result += "</div>";

        // close off the main result
        result += "</div>";

        // create the abstract section if desired
        if (resultobj.bibjson.abstract) {
            // start the abstract section
            result += "<div class='row-fluid'><div class='span1'>&nbsp;</div><div class='span11'>";

            result += "<strong>Abstract</strong>&nbsp;&nbsp;";
            result += '<a class="abstract_action" href="" rel="' + resultobj.id + '">(expand)</a><br>';
            result += '<div class="abstract_text" rel="' + resultobj.id + '">' + resultobj.bibjson.abstract + '</div>';

            // close off the abstract section
            result += "</div></div>";
        }

        // close off the result and return
        result += options.resultwrap_end;
        return result;
    }


    $('.facetview.journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/journal,article/_search?',

        render_results_metadata: doajPager,
        render_result_record: publicSearchResult,

        pre_search_callback: dynamicFacets,
        post_render_callback: doajPostRender,

        sharesave_link: true,
        url_shortener : bitlyShortener,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: natural,

        search_sortby: [
            {'display':'Date added to DOAJ','field':'created_date'},
            {'display':'Title','field':'bibjson.title.exact'},

            // check that this works in fv2
            {'display':'Article: Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
        ],

        searchbox_fieldselect: [
            {'display':'Title','field':'bibjson.title'},
            {'display':'Keywords','field':'bibjson.keywords'},
            {'display':'Subject','field':'index.classification'},
            {'display':'ISSN', 'field':'index.issn.exact'},
            {'display':'DOI', 'field' : 'bibjson.identifier.id'},
            {'display':'Country of publisher','field':'index.country'},
            {'display':'Journal Language','field':'index.language'},
            {'display':'Publisher','field':'index.publisher'},

            {'display':'Article: Abstract','field':'bibjson.abstract'},
            {'display':'Article: Year','field':'bibjson.year'},
            {'display':'Article: Journal Title','field':'bibjson.journal.title'},

            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
        ],

        page_size : 10,
        from : 0
    });
});
