jQuery(document).ready(function($) {

    var all_facets = {

        // This is set permanently to articles so the share | embed buton can be configured to only show articles
        journal_article : {
            field : "_type",
            hidden: true
        },

        issn : {
            field: 'index.issn.exact',
            type: 'terms',
            logic: 'OR',
            hidden: true
        },

        volume : {
            field: 'bibjson.journal.volume.exact',
            display: 'Volume',
            disabled: false
        },

        issue : {
            field: 'bibjson.journal.number.exact',
            display: 'Issue',
            disabled: true
        },

        year_published_histogram : {
            type: 'date_histogram',
            field: 'index.date',
            interval: 'year',
            display: 'Year',
            value_function : function(val) {
                return (new Date(parseInt(val))).getUTCFullYear();
            },
            size: false,
            short_display: 15,
            sort: 'desc',
            disabled: false
        },

        month_published_histogram : {
            type: 'date_histogram',
            field: 'index.date_toc_fv_month',
            interval: 'month',
            display: 'Month',
            value_function : function(val) {
                var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                var mi = (new Date(parseInt(val))).getUTCMonth();
                return months[mi]
            },
            size: false,
            short_display: 12,
            sort: 'asc',
            disabled: true
        }
    };

    var natural = [];
    natural.push(all_facets.journal_article);
    natural.push(all_facets.issn);
    natural.push(all_facets.volume);
    natural.push(all_facets.issue);
    natural.push(all_facets.year_published_histogram);
    natural.push(all_facets.month_published_histogram);

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

        // On selection of "Volume" an "Issue" facet will appear.
        if ('bibjson.journal.volume.exact' in options.active_filters) {
            disableFacet(options, 'bibjson.journal.number.exact', false);
        } else {
            disableFacet(options, 'bibjson.journal.number.exact', true);
        }

        // On selection of "Year" an "Month" facet will appear.
        if ('index.date' in options.active_filters) {
            disableFacet(options, 'index.date_toc_fv_month', false)
        } else {
            disableFacet(options, 'index.date_toc_fv_month', true);
        }
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
                    citation += "<a href='/toc/" + issns[0] + "'>" + escapeHtml(ctitle.trim()) + "</a>";
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
        result += "<i style='font-size: 24px' class='fa fa-file'></i>";
        result += "</div>";

        result += "<div class='pull-left' style='width: 90%'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a href='/article/" + resultobj.id + "'>" + escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
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
                    var url = "https://doi.org/" + escapeHtml(doi.substring(tendot));
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

    $('.facetview.journal_toc_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/article/_search?ref=doaj',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        render_active_date_histogram_filter: doajRenderActiveDateHistogramFilter,
        render_result_record: renderPublicArticle,

        pre_search_callback: dynamicFacets,
        post_render_callback: doajPostRender,

        sharesave_link: true,
        url_shortener : bitlyShortener,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: natural,

        // Each ToC is fixed to the correct journal ISSN.
        predefined_filters: {"index.issn.exact" : toc_issns, '_type' : ['article'] },
        exclude_predefined_filters_from_facets : true,

        search_sortby: [
            {'display':'Title','field':'index.unpunctitle.exact'},
            {'display':'Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
        ],

        searchbox_fieldselect: [
            {'display':'Title','field':'bibjson.title'},
            {'display':'Abstract','field':'bibjson.abstract'},
            {'display':'Year','field':'bibjson.year'}
        ],

        page_size : 100,
        from : 0
    });
});
