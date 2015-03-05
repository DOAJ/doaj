jQuery(document).ready(function($) {

    $('.facetview.journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/journal,article/_search?',

        render_results_metadata: pageSlider,
        post_render_callback: doajPostRender,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",

        facets: [
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
        ],

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
        //render_result_record: publicSearchResult,

        // these need to be dealt with by the render function
        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date,
            'bibjson.abstract': fv_abstract,
            'addthis-social-share-button': fv_addthis,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "country_name": fv_country_name
        },

        result_display: [
    // Journals
        [
            {
                "field" : "title_field"
            }
            /*
            {
                "pre": '<span class="title">',
                "field": "bibjson.title",
                "post": "</span>"
            }
            */
        ],
        [
            {
                "pre": '<span class="alt_title">Alternative title: ',
                "field": "bibjson.alternative_title",
                "post": "</span>"
            }
        ],
        [
            {
                "pre": "<strong>Subjects</strong>: ",
                "field": "bibjson.subject.term"
            }
        ],
        [
            {
                "pre": "<strong>Publisher</strong>: ",
                "field": "bibjson.publisher"
            }
        ],
        [
            {
                "pre": "<strong>Publication charges?</strong>: ",
                "field": "bibjson.author_pays"
            }
        ],
        [
            {
                "pre": "<strong>Journal Language</strong>: ",
                "field": "bibjson.language"
            }
        ],
// Articles
        [
            {
                "pre": "<strong>Authors</strong>: ",
                "field": "bibjson.author.name"
            }
        ],
        [
            {
                "pre": "<strong>Publisher</strong>: ",
                "field": "bibjson.journal.publisher"
            }
        ],
        [
            {
                "pre":'<strong>Date of publication</strong>: ',
                "field": "bibjson.year"
            },
            {
                "pre":' <span class="date-month">',
                "field": "bibjson.month",
                "post": "</span>"
            }
        ],
        [
            {
                "pre": "<strong>Published in</strong>: ",
                "field": "bibjson.journal.title",
                "notrailingspace": true
            },
            {
                "pre": ", Vol ",
                "field": "bibjson.journal.volume",
                "notrailingspace": true
            },
            {
                "pre": ", Iss ",
                "field": "bibjson.journal.number",
                "notrailingspace": true
            },
            {
                "pre": ", Pp ",
                "field": "bibjson.start_page",
                "notrailingspace": true
            },
            {
                "pre": "-",
                "field": "bibjson.end_page"
            },
            {
                "pre" : "(",
                "field": "bibjson.year",
                "post" : ")"
            }
        ],
        [
            {
                "pre" : "<strong>ISSN(s)</strong>: ",
                "field" : "issns"
            }
        ],
        [
            {
                "pre": "<strong>Keywords</strong>: ",
                "field": "bibjson.keywords"
            }
        ],
        [
            {
                "pre": "<strong>DOI</strong>: ",
                "field": "doi_link"
            }
        ],
        [
            {
                "field" : "links"
            }
            /*
            {
                "pre": "<strong>More information - ",
                "field": "bibjson.link.type",
                "post": "</strong>: ",
            },
            {
                "field": "bibjson.link.url",
            },
            */
        ],
        [
            {
                "pre": "<strong>Journal Language(s)</strong>: ",
                "field": "bibjson.journal.language"
            }
        ],
        [
            {
                "pre": "<strong>Journal License</strong>: ",
                "field": "journal_license"
            }
        ],
        [
            {
                "pre": "<strong>Country of publisher</strong>: ",
                "field": "country_name"
            }
        ],
        [
            {
                "pre": '<strong>Abstract</strong>: ',
                "field": "bibjson.abstract"
            }
        ],

// Share Button
        [
            {
                "field": "addthis-social-share-button"
            }
        ]
    ]


    });
});
