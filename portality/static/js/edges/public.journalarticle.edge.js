$.extend(true, doaj, {

    publicSearch : {
        activeEdges : {},

        dynamicFacets : {
            journal : [
                "country_publisher",
                "apc",
                "peer_review",
                "year_added"
            ],
            article : [
                "archiving_policy",
                "journal_title",
                "year_published"
            ]
        },

        embedSnippet : function(renderer) {
            var snip = '<script type="text/javascript">!window.jQuery && document.write("<scr" + "ipt type=\"text/javascript\" src=\"http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js\"></scr" + "ipt>"); </script><script type="text/javascript">var doaj_url="https://doaj.org"; var SEARCH_CONFIGURED_OPTIONS={{QUERY}}</script><script src="https://doaj.org/static/widget/fixed_query.js" type="text/javascript"></script><div id="doaj-fixed-query-widget"></div></div>';
            var query = renderer.component.edge.currentQuery.objectify({
                        include_query_string : true,
                        include_filters : true,
                        include_paging : true,
                        include_sort : true,
                        include_fields : false,
                        include_aggregations : false
                    });
            snip = snip.replace(/{{QUERY}}/g, JSON.stringify(query));
            return snip;
        },

        displayYearPeriod : function(params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var display = (new Date(parseInt(from))).getUTCFullYear();
            return {to: to, toType: "lt", from: from, fromType: "gte", display: display}
        },

        newPublicSearchResultRenderer : function(params) {
            if (!params) { params = {} }
            doaj.publicSearch.PublicSearchResultRenderer.prototype = edges.newRenderer(params);
            return new doaj.publicSearch.PublicSearchResultRenderer(params);
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
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "doi") {
                            var doi = ids[i].id;
                            var tendot = doi.indexOf("10.");
                            var url = "https://doi.org/" + edges.escapeHtml(doi.substring(tendot));
                            result += " DOI <a href='" + url + "'>" + edges.escapeHtml(doi.substring(tendot)) + "</a>";
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

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#public-search";
            var search_url = current_scheme + "//" + current_domain + doaj.publicSearchConfig.publicSearchPath;

            countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id : "journal_article",
                    category: "facet",
                    field: "_type",
                    display: "Journals vs. Articles",
                    size: 2,
                    orderBy: "term",
                    orderDir: "desc",
                    valueMap : {
                        "journal" : "Journals",
                        "article" : "Articles"
                    },
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: false,
                        open: true,
                        togglable: false,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "subject",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Subject",
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "apc",
                    category: "facet",
                    field: "index.has_apc.exact",
                    display: "Article processing charges (APCs)",
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true,
                        tooltipText: "What do these figures mean?",
                        tooltip: 'For more information see this <a href="https://doajournals.wordpress.com/2015/05/11/historical-apc-data-from-before-the-april-upgrade/" target="_blank">blog post</a> (opens in new window).'
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "journal_title",
                    category: "facet",
                    field: "bibjson.journal.title.exact",
                    display: "Journal title",
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "seal",
                    category: "facet",
                    field: "index.has_seal.exact",
                    display: "DOAJ Seal",
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "journal_licence",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Journal License",
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "publisher",
                    category: "facet",
                    field: "index.publisher.exact",
                    display: "Publisher",
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "country_publisher",
                    category: "facet",
                    field: "index.country.exact",
                    display: "Country of Publisher",
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        hideInactive: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Fulltext Language",
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "peer_review",
                    category: "facet",
                    field: "bibjson.editorial_review.process.exact",
                    display: "Peer review",
                    ignoreEmptyString: true,
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newDateHistogramSelector({
                    id : "year_added",
                    category: "facet",
                    field: "created_date",
                    interval: "year",
                    display: "Date added to DOAJ",
                    active: false,
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer : edges.bs3.newDateHistogramSelectorRenderer({
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newDateHistogramSelector({
                    id : "year_published",
                    category: "facet",
                    field: "index.date",
                    interval: "year",
                    display: "Year of publication",
                    active: false,
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer : edges.bs3.newDateHistogramSelectorRenderer({
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true,
                        shortDisplay: 15
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions : [
                        {'display':'Date added to DOAJ','field':'created_date'},
                        {'display':'Title','field':'index.unpunctitle.exact'},
                        {'display':'Article: Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
                    ],
                    fieldOptions : [
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
                        {'display':'Article: Author','field':'bibjson.author.name'},

                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
                    ],
                    defaultOperator : "AND",
                    urlShortener : doaj.bitlyShortener,
                    embedSnippet : doaj.publicSearch.embedSnippet,
                    renderer : edges.bs3.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search DOAJ",
                        shareLink: true,
                        shareLinkText : "share | embed"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : edges.bs3.newPagerRenderer({
                        sizeOptions : [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : edges.bs3.newPagerRenderer({
                        sizeOptions : [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.publicSearch.newPublicSearchResultRenderer()
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays : {
                        "_type" : "Showing",
                        "index.classification.exact" : "Medicine",
                        "index.has_apc.exact" : "Article processing charges (APCs)",
                        "index.has_seal.exact" : "DOAJ Seal",
                        "index.license.exact" : "Journal license",
                        "index.publisher.exact" : "Publisher",
                        "index.country.exact" : "Country of Publisher",
                        "index.language.exact" : "Fulltext Language",
                        "bibjson.editorial_review.process.exact" : "Peer review",
                        "created_date" : "Date added to DOAJ",
                        "bibjson.journal.title.exact" : "Journal title",
                        "index.date" : "Year of publication"
                    },
                    valueMaps : {
                        "_type" : {
                            "journal" : "Journals",
                            "article" : "Articles"
                        }
                    },
                    rangeFunctions : {
                        "created_date" : doaj.publicSearch.displayYearPeriod
                    }
                }),

                // the standard searching notification
                edges.newSearchingNotification({
                    id: "searching-notification",
                    category: "searching-notification"
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl : true,
                components : components
            });
            doaj.publicSearch.activeEdges[selector] = e;

            $(selector).on("edges:pre-render", function() {
                var journal_article = e.getComponent({id: "journal_article"});

                var deactivate = [];
                var activate = [];
                if (journal_article.filters.length === 0) {
                    deactivate = [].concat(doaj.publicSearch.dynamicFacets.journal).concat(doaj.publicSearch.dynamicFacets.article);
                } else {
                    var term = journal_article.filters[0].term;
                    if (term === "journal") {
                        deactivate = doaj.publicSearch.dynamicFacets.article;
                        activate = doaj.publicSearch.dynamicFacets.journal;
                    } else if (term === "article") {
                        activate = doaj.publicSearch.dynamicFacets.article;
                        deactivate = doaj.publicSearch.dynamicFacets.journal;
                    }
                }

                for (var i = 0; i < e.components.length; i++) {
                    var component = e.components[i];
                    if ($.inArray(component.id, deactivate) !== -1) {
                        component.active = false;
                    } else if ($.inArray(component.id, activate) !== -1) {
                        component.active = true;
                    }
                }
            });

            $(selector).on("edges:pre-query", function() {
                var journal_article = e.getComponent({id: "journal_article"});
                var musts = e.currentQuery.listMust(es.newTermFilter({field: journal_article.field}));
                var deactivate = [];
                if (musts.length === 0) {
                    deactivate = [].concat(doaj.publicSearch.dynamicFacets.journal).concat(doaj.publicSearch.dynamicFacets.article);
                } else {
                    var term = musts[0].value;
                    if (term === "journal") {
                        deactivate = doaj.publicSearch.dynamicFacets.article;
                    } else if (term === "article") {
                        deactivate = doaj.publicSearch.dynamicFacets.journal;
                    }
                }

                for (var i = 0; i < e.components.length; i++) {
                    var component = e.components[i];
                    if ($.inArray(component.id, deactivate) !== -1) {
                        // remove the filters
                        component.clearFilters({triggerQuery: false});
                    }
                }
            });
        }
    }

});

doaj.publicSearch.init();
