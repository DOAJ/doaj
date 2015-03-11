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

    $('.facetview.journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/journal,article/_search?',

        render_results_metadata: pageSlider,
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
        from : 0,

        // replace all of the below with this eventually
        render_result_record: publicSearchResult
    });
});
