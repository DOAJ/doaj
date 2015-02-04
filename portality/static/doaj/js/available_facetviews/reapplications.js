jQuery(document).ready(function ($) {

    var status_mapping = {
        "reapplication" : {"text" : "pending" }
    };

    function doCustomise() {
        // do the standard results customisation
        customise_facetview_results();

        // application status
        // 1. facet itself
        $('#facetview_admin_application_status_exact .facetview_filterchoice_text').each(
            function () {
                var thespan = $(this);
                if (status_mapping.hasOwnProperty(thespan.html())) {
                    var meaning = status_mapping[thespan.html()];
                    if (meaning.hasOwnProperty('text') && meaning['text']) {
                        thespan.html(meaning['text']);
                    }
                }
            }
        );

        // application status
        // 2. don't forget filter buttons
        $('a.facetview_filterselected[rel="admin.application_status.exact"] > .facetview_filterselected_text').each(
            function () {
                var thespan = $(this);
                if (status_mapping.hasOwnProperty(thespan.html())) {
                    var meaning = status_mapping[thespan.html()];
                    if (meaning.hasOwnProperty('text') && meaning['text']) {
                        thespan.html(meaning['text']);
                    }
                }
            }
        );

    }

    $('.facetview.reapplications').each(function () {
        $(this).facetview({
            search_url: es_scheme + '//' + es_domain + '/publisher_reapp_query/suggestion/_search?',
            search_index: 'elasticsearch',
            sharesave_link: false,
            searchbox_shade: 'none',
            pager_on_top: true,
            pager_slider: true,
            display_images: false,
            pre_search_callback: customise_facetview_presearch,
            post_search_callback: doCustomise,
            post_init_callback: customise_facetview_init,
            freetext_submit_delay: "1000",
            results_render_callbacks: {
                'bibjson.author_pays': fv_author_pays,
                'created_date': fv_created_date,
                'last_updated': fv_last_updated,
                'journal_license': fv_journal_license,
                "title_field": fv_title_field,
                "doi_link": fv_doi_link,
                "links": fv_links,
                "issns": fv_issns,
                "country_name": fv_country_name,
                'suggested_on': fv_suggested_on,
                "view_reapplication": fv_view_reapplication
            },
            hide_inactive_facets: true,
            facets: [
                {'field': 'admin.application_status.exact', 'display': 'Status'},
                {'field': 'suggestion.suggested_by_owner.exact', 'display': 'Application by owner?'},
                {'field': 'index.classification.exact', 'display': 'Subject'},
                {'field': 'index.language.exact', 'display': 'Journal Language'},
                {'field': 'index.country.exact', 'display': 'Country of publisher'},
                {'field': 'index.subject.exact', 'display': 'Subject'},
                {'field': 'bibjson.provider.exact', 'display': 'Provider'},
                {'field': 'bibjson.author_pays.exact', 'display': 'Publication charges?'},
                {'field': 'index.license.exact', 'display': 'Journal License'},
                {'field': 'bibjson.oa_start.exact', 'display': 'Started publishing OA content (year)'},
                {'field': 'bibjson.oa_end.exact', 'display': 'Stopped publishing OA content (year)'},
            ],
            search_sortby: [
                {'display': 'Date added to DOAJ', 'field': 'created_date'},
                {'display': 'Last updated', 'field': 'last_updated'},
                {'display': 'Title', 'field': 'index.title.exact'},
            ],
            searchbox_fieldselect: [
                {'display': 'Title', 'field': 'index.title'},
                {'display': 'Journal: Alternative Title', 'field': 'bibjson.alternative_title'},
                {'display': 'Subject', 'field': 'index.subject'},
                {'display': 'Classification', 'field': 'index.classification'},
                {'display': 'ISSN', 'field': 'index.issn.exact'},
                {'display': 'Country of publisher', 'field': 'index.country'},
                {'display': 'Journal Language', 'field': 'index.language'},
                {'display': 'Publisher', 'field': 'index.publisher'},
                {'display': 'Journal: Provider', 'field': 'bibjson.provider'},
            ],
            paging: {
                from: 0,
                size: 10
            },
            default_operator: "AND",
            result_display: [
                [
                    {
                        "field": "title_field"
                    }
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
                        "pre": "<strong>Date applied</strong>: ",
                        "field": "suggested_on",
                    }
                ],
                [
                    {
                        "pre": "<strong>Last updated</strong>: ",
                        "field": "last_updated",
                    }
                ],
                [
                    {
                        "pre": "<strong>ISSN(s)</strong>: ",
                        "field": "issns"
                    }
                ],
                [
                    {
                        "pre": "<strong>Application status</strong>: ",
                        "field": "admin.application_status"
                    }
                ],
                [
                    {
                        "pre": "<strong>Description</strong>: ",
                        "field": "suggestion.description"
                    }
                ],
                [
                    {
                        "pre": "<strong>Contact</strong>: ",
                        "field": "admin.contact.name"
                    },
                    {
                        "field": "admin.contact.email"
                    }
                ],
                [
                    {
                        "pre": "<strong>Application by</strong>: ",
                        "field": "suggestion.suggester.name"
                    },
                    {
                        "field": "suggestion.suggester.email"
                    }
                ],
                [
                    {
                        "pre": "<strong>Application by owner?</strong>: ",
                        "field": "suggestion.suggested_by_owner"
                    }
                ],
                [
                    {
                        "pre": "<strong>Subjects</strong>: ",
                        "field": "index.subject",
                    }
                ],
                [
                    {
                        "pre": "<strong>Keywords</strong>: ",
                        "field": "bibjson.keywords",
                    }
                ],
                [
                    {
                        "pre": "<strong>Publisher</strong>: ",
                        "field": "bibjson.publisher",
                    }
                ],
                [
                    {
                        "pre": "<strong>Provider</strong>: ",
                        "field": "bibjson.provider",
                    }
                ],
                [
                    {
                        "pre": "<strong>Publication charges?</strong>: ",
                        "field": "bibjson.author_pays",
                    }
                ],
                [
                    {
                        "pre": "<strong>Started publishing Open Access content in</strong>: ",
                        "field": "bibjson.oa_start.year",
                    }
                ],
                [
                    {
                        "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                        "field": "bibjson.oa_end.year",
                    }
                ],
                [
                    {
                        "pre": "<strong>Country of publisher</strong>: ",
                        "field": "country_name",
                    }
                ],
                [
                    {
                        "pre": "<strong>Journal Language</strong>: ",
                        "field": "bibjson.language",
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
                        "field": "links"
                    }
                ],
                [
                    {
                        "field": "view_reapplication"
                    }
                ],
            ],
        });
    });
});
