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

        peer_review : {
            field : "bibjson.editorial_review.process.exact",
            display : "Peer review"
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
            sort: "desc"
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


    var original = [
        {'field': '_type', 'display': 'Journals vs. Articles'},
        {'field': 'index.classification.exact', 'display': 'Subject'},
        {'field': 'index.language.exact', 'display': 'Journal Language'},
        {'field': 'index.country.exact', 'display': 'Country of publisher'},
        {'field': 'index.publisher.exact', 'display': 'Publisher'},
        {
            'field': 'bibjson.author_pays.exact',
            'display': 'Publication charges?',
            value_function: authorPaysMap
        },
        {'field': 'index.license.exact', 'display': 'Journal License'},
        // Articles
        {'field': 'bibjson.year.exact', 'display': 'Year of publication (Articles)'},
        {'field': 'bibjson.journal.title.exact', 'display': 'Journal title (Articles)'}
    ];

    $('.facetview.journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/journal,article/_search?',

        render_results_metadata: pageSlider,
        post_render_callback: doajPostRender,

        sharesave_link: false,
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
