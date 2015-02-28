jQuery(document).ready(function($) {

    //function publicSearchResult() {
        // display the result
    //}

    /*
    Function which translates the month - we'll use this in the display of results

    var months_english = {
        '1': 'January',
        '2': 'February',
        '3': 'March',
        '4': 'April',
        '5': 'May',
        '6': 'June',
        '7': 'July',
        '8': 'August',
        '9': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December'
    };

    function expand_month() {
        this.innerHTML = months_english[this.innerHTML.replace(/^0+/,"")];
    }
     */

    function doajSearching(options) {
        return '<div class="progress progress-danger progress-striped active notify_loading" id="search-progress-bar"><div class="bar">Loading, please wait...</div></div>'
    }

    function noBottomFacetOpen(options, context, facet) {
        var el = context.find("#facetview_filter_" + safeId(facet.field));
        var open = facet["open"];
        if (open) {
            el.find(".facetview_filtershow").find("i").removeClass("icon-plus");
            el.find(".facetview_filtershow").find("i").addClass("icon-minus");
            el.find(".facetview_filteroptions").show();
            el.find(".facetview_filtervalue").show();
            el.addClass("no-bottom");
        } else {
            el.find(".facetview_filtershow").find("i").removeClass("icon-minus");
            el.find(".facetview_filtershow").find("i").addClass("icon-plus");
            el.find(".facetview_filteroptions").hide();
            el.find(".facetview_filtervalue").hide();
            el.removeClass("no-bottom");
        }
    }

    function postRender(options, context) {
        // toggle the abstracts
        $('.abstract_text', context).hide();
        $(".abstract_action", context).unbind("click").click(function(event) {
            event.preventDefault();
            var el = $(this);
            var text = el.html();
            var newText = text == "(expand)" ? "(collapse)" : "(expand)";
            el.html(newText);
            $('.abstract_text[rel="' + el.attr("rel") + '"]').fadeToggle(300);
            return true;
        })
    }

    var authorPaysMapping = {
        "N" : "No Charges",
        "Y" : "Has Charges",
        "CON" : "Conditional charges",
        "NY" : "No info available"
    };
    function authorPaysMap(value) {
        if (authorPaysMapping.hasOwnProperty(value)) {
            return authorPaysMapping[value];
        }
        return value;
    }

    $('.facetview.journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/query/journal,article/_search?',

        render_results_metadata: pageSlider,
        render_searching_notification : doajSearching,
        behaviour_toggle_facet_open : noBottomFacetOpen,

        post_render_callback: postRender,

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
            {'field': 'bibjson.journal.title.exact', 'display': 'Journal title (Articles)'},
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

            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
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
            },
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
        ],
    ]


    });
});
