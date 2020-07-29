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
        },

        displayYearPeriod : function(params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var display = (new Date(parseInt(from))).getUTCFullYear();
            return {to: to, toType: "lt", from: from, fromType: "gte", display: display}
        }
    },

    templates : {
        newPublicSearch: function (params) {
            return edges.instantiate(doaj.templates.PublicSearch, params, edges.newTemplate);
        },
        PublicSearch: function (params) {
            this.namespace = "doajpublicsearch";

            this.title = edges.getParam(params.title, "");

            this.draw = function (edge) {
                this.edge = edge;

                var frag = '<header class="search__header" style="background-image: url(\'/static/doaj/images/search-background.jpg\')"> \
                        <p class="label">Search</p>\n \
                        <h1>' + this.title + ' \
                            <span data-feather="help-circle" aria-hidden="true" data-toggle="modal" data-target="#modal-help" type="button"></span><span class="sr-only">Help</span> \
                        </h1> \
                        <div class="row">\
                            <div id="search-journal-bar" class="col-md-9"></div>\
                        </div>\
                    </header>\
                    <h2 id="result-count"></h2>\
                    <div class="row">\
                        <div class="col-md-3">\
                            <aside class="filters">\
                                <h2 class="label label--underlined filters__heading" type="button" data-toggle="collapse" data-target="#filters" aria-expanded="false">\
                                    <span data-feather="sliders" aria-hidden="true"></span> Refine search results <span data-feather="chevron-down" aria-hidden="true"></span>\
                                </h2>\
                                <ul class="collapse filters__list" id="filters" aria-expanded="false">\
                                    {{FACETS}}\
                                </ul>\
                                <p class="input-group" id="share_embed"></p>\
                        </div>\
                            \
                        <div class="col-md-9">\
                            <nav class="search-options">\
                                <h3 class="sr-only">Display options</h3>\
                                <div class="row">\
                                    <div class="col-xs-6" id="sort_by"></div>\
                                    <div class="col-xs-6 search-options__right" id="rpp"></div>\
                                </div>\
                            </nav>\
                            <aside id="selected-filters"></aside>\
                            <nav class="pagination" id="top-pager"></nav>\
                            <ol class="search-results" id="results"></ol>\
                            <nav class="pagination" id="bottom-pager"></nav>\
                        </div>\
                    </div>';

                // add the facets dynamically
                var facets = edge.category("facet");
                var facetContainers = "";
                for (var i = 0; i < facets.length; i++) {
                    facetContainers += '<li class="filter" id="' + facets[i].id + '"></li>';
                }
                frag = frag.replace(/{{FACETS}}/g, facetContainers);

                /*
                // the classes we're going to need
                var containerClass = edges.css_classes(this.namespace, "container");
                var facetsClass = edges.css_classes(this.namespace, "facets");
                var facetClass = edges.css_classes(this.namespace, "facet");
                var panelClass = edges.css_classes(this.namespace, "panel");
                var controllerClass = edges.css_classes(this.namespace, "search-controller");
                var selectedFiltersClass = edges.css_classes(this.namespace, "selected-filters");
                var pagerClass = edges.css_classes(this.namespace, "pager");
                var searchingClass = edges.css_classes(this.namespace, "searching");
                var resultsClass = edges.css_classes(this.namespace, "results");

                // the facet view object to be appended to the page
                var thefacetview = '<div class="' + containerClass + '"><div class="row">';

                // if there are facets, give them span3 to exist, otherwise, take up all the space
                var facets = edge.category("facet");
                var facetContainers = "";

                if (facets.length > 0) {
                    thefacetview += '<div class="col-md-3">\
                        <div class="' + facetsClass + '">{{FACETS}}</div>\
                    </div>';
                    thefacetview += '<div class="col-md-9" class="' + panelClass + '">';

                    for (var i = 0; i < facets.length; i++) {
                        facetContainers += '<div class="' + facetClass + '"><div id="' + facets[i].id + '"></div></div>';
                    }
                } else {
                    thefacetview += '<div class="col-md-12" class="' + panelClass + '">';
                }

                // make space for the search options container at the top
                var controller = edge.category("controller");
                if (controller.length > 0) {
                    thefacetview += '<div class="row"><div class="col-md-12"><div class="' + controllerClass + '"><div id="' + controller[0].id + '"></div></div></div></div>';
                }

                // make space for the selected filters
                var selectedFilters = edge.category("selected-filters");
                if (selectedFilters.length > 0) {
                    thefacetview += '<div class="row">\
                                            <div class="col-md-12">\
                                                <div class="' + selectedFiltersClass + '"><div id="' + selectedFilters[0].id + '"></div></div>\
                                            </div>\
                                        </div>';
                }

                // make space at the top for the page
                var topPagers = edge.category("top-pager");
                if (topPagers.length > 0) {
                    thefacetview += '<div class="row"><div class="col-md-12"><div class="' + pagerClass + '"><div id="' + topPagers[0].id + '"></div></div></div></div>';
                }

                // loading notification (note that the notification implementation is responsible for its own visibility)
                var loading = edge.category("searching-notification");
                if (loading.length > 0) {
                    thefacetview += '<div class="row"><div class="col-md-12"><div class="' + searchingClass + '"><div id="' + loading[0].id + '"></div></div></div></div>'
                }

                // insert the frame within which the results actually will go
                var results = edge.category("results");
                if (results.length > 0) {
                    for (var i = 0; i < results.length; i++) {
                        thefacetview += '<div class="row"><div class="col-md-12"><div class="' + resultsClass + '" dir="auto"><div id="' + results[i].id + '"></div></div></div></div>';
                    }
                }

                // make space at the bottom for the pager
                var bottomPagers = edge.category("bottom-pager");
                if (bottomPagers.length > 0) {
                    thefacetview += '<div class="row"><div class="col-md-12"><div class="' + pagerClass + '"><div id="' + bottomPagers[0].id + '"></div></div></div></div>';
                }

                // close off all the big containers and return
                thefacetview += '</div></div></div>';

                thefacetview = thefacetview.replace(/{{FACETS}}/g, facetContainers);
                */

                edge.context.html(frag);
            };
        }
    },

    renderers : {
        // FIXME: this is probably obsolete
        newFullSearchControllerRenderer: function (params) {
            return edges.instantiate(doaj.renderers.FullSearchControllerRenderer, params, edges.newRenderer);
        },
        FullSearchControllerRenderer: function (params) {
            // enable the search button
            this.searchButton = edges.getParam(params.searchButton, false);

            // text to include on the search button.  If not provided, will just be the magnifying glass
            this.searchButtonText = edges.getParam(params.searchButtonText, false);

            // should the clear button be rendered
            this.clearButton = edges.getParam(params.clearButton, true);

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            // enable the share/save link feature
            this.shareLink = edges.getParam(params.shareLink, false);
            this.shareLinkText = edges.getParam(params.shareLinkText, "share");

            ////////////////////////////////////////
            // state variables

            this.shareBoxOpen = false;

            this.showShortened = false;

            this.focusSearchBox = false;

            this.namespace = "doaj-bs3-search-controller";

            this.draw = function () {
                // reset these on each draw
                this.shareBoxOpen = false;
                this.showShortened = false;

                var comp = this.component;

                var shareButtonFrag = "";
                var shareFrag = "";
                if (this.shareLink) {
                    var shareButtonClass = edges.css_classes(this.namespace, "toggle-share", this);
                    shareButtonFrag = '<button class="' + shareButtonClass + ' btn btn-default btn-sm">' + this.shareLinkText + '</button>';
                    var shorten = "";
                    if (this.component.urlShortener) {
                        var shortenClass = edges.css_classes(this.namespace, "shorten", this);
                        shorten = '<div class="' + shortenClass + '">Share a link to this search <button class="btn btn-default btn-xs"><span class="glyphicon glyphicon-resize-small"></span>shorten url</button></div>'
                    }
                    var embed = "";
                    if (this.component.embedSnippet) {
                        var embedClass = edges.css_classes(this.namespace, "embed", this);
                        embed = '<div class="row">\
                            <div class="col-md-12">\
                                Embed this search in your webpage\
                            </div>\
                        </div>\
                        <div class="row">\
                            <div class="col-md-12">\
                                <textarea readonly class="' + embedClass + '"></textarea>\
                            </div>\
                        </div>';
                    }
                    var shareBoxClass = edges.css_classes(this.namespace, "share", this);
                    var closeClass = edges.css_classes(this.namespace, "close-share", this);
                    var shareUrlClass = edges.css_classes(this.namespace, "share-url", this);
                    shareFrag = '<div class="' + shareBoxClass + '" style="display:none">\
                        <div class="row">\
                            <div class="col-md-11">\
                                ' + shorten + '\
                            </div>\
                            <div class="col-md-1">\
                                <a href="#" class="' + closeClass + ' pull-right"><span class="glyphicon glyphicon-remove"></span></a>\
                            </div>\
                        </div>\
                        <div class="row">\
                            <div class="col-md-12">\
                                <textarea readonly class="' + shareUrlClass + '"></textarea>\
                            </div>\
                        </div>\
                        ' + embed + '\
                    </div>';
                }

                var clearClass = edges.css_classes(this.namespace, "reset", this);
                var clearFrag = "";
                if (this.clearButton) {
                    clearFrag = '<button type="button" class="btn btn-danger btn-sm ' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                            <span class="glyphicon glyphicon-remove"></span> \
                        </button>';
                }

                // if sort options are provided render the orderer and the order by
                var sortOptions = "";
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    // classes that we'll use
                    var sortClasses = edges.css_classes(this.namespace, "sort", this);
                    var directionClass = edges.css_classes(this.namespace, "direction", this);
                    var sortFieldClass = edges.css_classes(this.namespace, "sortby", this);

                    sortOptions = '<div class="form-inline ' + sortClasses + '"> \
                            <div class="form-group"> \
                                <div class="input-group"> \
                                    <span class="input-group-btn"> \
                                        <button type="button" class="btn btn-default btn-sm ' + directionClass + '" title="" href="#"></button> \
                                    </span> \
                                    <select class="' + sortFieldClass + ' form-control input-sm"> \
                                        <option value="_score">Relevance</option>';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        sortOptions += '<option value="' + field + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += ' </select> \
                                </div> \
                            </div> \
                        </div>';
                }

                // select box for fields to search on
                var field_select = "";
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    // classes that we'll use
                    var searchFieldClass = edges.css_classes(this.namespace, "field", this);

                    field_select += '<select class="' + searchFieldClass + ' form-control input-sm">';
                    field_select += '<option value="">search all</option>';

                    for (var i = 0; i < comp.fieldOptions.length; i++) {
                        var obj = comp.fieldOptions[i];
                        field_select += '<option value="' + obj['field'] + '">' + edges.escapeHtml(obj['display']) + '</option>';
                    }
                    field_select += '</select>';
                }

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);
                var searchClass = edges.css_classes(this.namespace, "search", this);

                // text search box id
                var textId = edges.css_id(this.namespace, "text", this);

                var searchFrag = "";
                if (this.searchButton) {
                    var text = '<span class="glyphicon glyphicon-white glyphicon-search"></span>';
                    if (this.searchButtonText !== false) {
                        text = this.searchButtonText;
                    }
                    searchFrag = '<span class="input-group-btn"> \
                        <button type="button" class="btn btn-info btn-sm ' + searchClass + '"> \
                            ' + text + ' \
                        </button> \
                    </span>';
                }

                var searchClasses = edges.css_classes(this.namespace, "searchcombo", this);
                var searchBox = '<div class="form-inline ' + searchClasses + '"> \
                        <div class="form-group"> \
                            <div class="input-group"> \
                                ' + field_select + '\
                                <input type="text" id="' + textId + '" class="' + textClass + ' form-control input-sm" name="q" value="" placeholder="' + this.searchPlaceholder + '"/> \
                                ' + searchFrag + ' \
                            </div> \
                        </div> \
                    </div>';

                if (shareButtonFrag !== "") {
                    shareButtonFrag = '<div class="col-md-2 col-xs-12">' + shareButtonFrag + "</div>";
                }
                if (clearFrag !== "") {
                    clearFrag = '<div class="col-md-1 col-xs-12">' + clearFrag + "</div>";
                }
                if (sortOptions !== "") {
                    sortOptions = '<div class="col-md-3 col-xs-12">' + sortOptions + "</div>";
                }
                if (searchBox !== "") {
                    searchBox = '<div class="col-md-6 col-xs-12">' + searchBox + "</div>";
                }

                // caclulate all the div widths
                var shareMd = "2";
                var sortMd = "4";
                var shareXs = "6";
                var sortXs = "6";

                var frag = shareFrag + '<div class="row">' + shareButtonFrag + clearFrag + sortOptions + searchBox + '</div>';

                comp.context.html(frag);

                // now populate all the dynamic bits
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    this.setUISortDir();
                    this.setUISortField();
                }
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    this.setUISearchField();
                }
                this.setUISearchText();

                // attach all the bindings
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                    var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                    edges.on(directionSelector, "click", this, "changeSortDir");
                    edges.on(sortSelector, "change", this, "changeSortBy");
                }
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                    edges.on(fieldSelector, "change", this, "changeSearchField");
                }
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                if (this.freetextSubmitDelay > -1) {
                    edges.on(textSelector, "keyup", this, "setSearchText", this.freetextSubmitDelay);
                } else {
                    function onlyEnter(event) {
                        var code = (event.keyCode ? event.keyCode : event.which);
                        return code === 13;
                    }

                    edges.on(textSelector, "keyup", this, "setSearchText", false, onlyEnter);
                }

                var resetSelector = edges.css_class_selector(this.namespace, "reset", this);
                edges.on(resetSelector, "click", this, "clearSearch");

                var searchSelector = edges.css_class_selector(this.namespace, "search", this);
                edges.on(searchSelector, "click", this, "doSearch");

                if (this.shareLink) {
                    var shareSelector = edges.css_class_selector(this.namespace, "toggle-share", this);
                    edges.on(shareSelector, "click", this, "toggleShare");

                    var closeShareSelector = edges.css_class_selector(this.namespace, "close-share", this);
                    edges.on(closeShareSelector, "click", this, "toggleShare");

                    if (this.component.urlShortener) {
                        var shortenSelector = edges.css_class_selector(this.namespace, "shorten", this);
                        edges.on(shortenSelector, "click", this, "toggleShorten");
                    }
                }

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISortDir = function () {
                // get the selector we need
                var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                var el = this.component.jq(directionSelector);
                if (this.component.sortDir === 'asc') {
                    el.html('sort <i class="glyphicon glyphicon-arrow-up"></i> by');
                    el.attr('title', 'Current order ascending. Click to change to descending');
                } else {
                    el.html('sort <i class="glyphicon glyphicon-arrow-down"></i> by');
                    el.attr('title', 'Current order descending. Click to change to ascending');
                }
            };

            this.setUISortField = function () {
                if (!this.component.sortBy) {
                    return;
                }
                // get the selector we need
                var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                var el = this.component.jq(sortSelector);
                el.val(this.component.sortBy);
            };

            this.setUISearchField = function () {
                if (!this.component.searchField) {
                    return;
                }
                // get the selector we need
                var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                var el = this.component.jq(fieldSelector);
                el.val(this.component.searchField);
            };

            this.setUISearchText = function () {
                if (!this.component.searchString) {
                    return;
                }
                // get the selector we need
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                var el = this.component.jq(textSelector);
                el.val(this.component.searchString);
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSortDir = function (element) {
                this.component.changeSortDir();
            };

            this.changeSortBy = function (element) {
                var val = this.component.jq(element).val();
                this.component.setSortBy(val);
            };

            this.changeSearchField = function (element) {
                var val = this.component.jq(element).val();
                this.component.setSearchField(val);
            };

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val);
            };

            this.clearSearch = function (element) {
                this.component.clearSearch();
            };

            this.doSearch = function (element) {
                var textId = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textId).val();
                this.component.setSearchText(text);
            };

            this.toggleShare = function(element) {
                var shareSelector = edges.css_class_selector(this.namespace, "share", this);
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var el = this.component.jq(shareSelector);
                var textarea = this.component.jq(shareUrlSelector);
                if (this.shareBoxOpen) {
                    el.hide();
                    textarea.val("");
                    if (this.component.embedSnippet) {
                        var embedSelector = edges.css_class_selector(this.namespace, "embed", this);
                        var embedTextarea = this.component.jq(embedSelector);
                        embedTextarea.val("");
                    }
                    this.shareBoxOpen = false;
                } else {
                    el.show();
                    if (this.showShortened) {
                        textarea.val(this.component.shortUrl);
                    } else {
                        textarea.val(this.component.edge.fullUrl());
                    }
                    if (this.component.embedSnippet) {
                        var embedSelector = edges.css_class_selector(this.namespace, "embed", this);
                        var embedTextarea = this.component.jq(embedSelector);
                        embedTextarea.val(this.component.embedSnippet(this));
                    }
                    this.shareBoxOpen = true;
                }
            };

            this.toggleShorten = function(element) {
                if (!this.component.shortUrl) {
                    var callback = edges.objClosure(this, "updateShortUrl");
                    this.component.generateShortUrl(callback);
                } else {
                    this.updateShortUrl();
                }
            };

            this.updateShortUrl = function() {
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var shortenSelector = edges.css_class_selector(this.namespace, "shorten", this);
                var textarea = this.component.jq(shareUrlSelector);
                var button = this.component.jq(shortenSelector).find("button");
                if (this.showShortened) {
                    textarea.val(this.component.edge.fullUrl());
                    button.html('<span class="glyphicon glyphicon-resize-small"></span>shorten url');
                    this.showShortened = false;
                } else {
                    textarea.val(this.component.shortUrl);
                    button.html('<span class="glyphicon glyphicon-resize-full"></span>original url');
                    this.showShortened = true;
                }
            };
        },

        newPageSizeRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PageSizeRenderer, params, edges.newRenderer);
        },
        PageSizeRenderer: function (params) {
            this.sizeOptions = edges.getParam(params.sizeOptions, [10, 25, 50, 100]);

            this.sizeLabel = edges.getParam(params.sizeLabel, "");

            this.namespace = "doaj-pagesize";

            this.draw = function () {
                // classes we'll need
                var sizeSelectClass = edges.css_classes(this.namespace, "size", this);
                var sizeSelectId = edges.css_classes(this.namespace, "page-size", this);

                // the number of records per page
                var sizer = '<label for="">' + this.sizeLabel + '</label><select class="' + sizeSelectClass + '" name="' + sizeSelectId + '">{{SIZES}}</select>';
                var sizeopts = "";
                var optarr = this.sizeOptions.slice(0);
                if (this.component.pageSize && $.inArray(this.component.pageSize, optarr) === -1) {
                    optarr.push(this.component.pageSize)
                }
                optarr.sort(function (a, b) {
                    return a - b
                });  // sort numerically
                for (var i = 0; i < optarr.length; i++) {
                    var so = optarr[i];
                    var selected = "";
                    if (so === this.component.pageSize) {
                        selected = "selected='selected'";
                    }
                    sizeopts += '<option name="' + so + '" ' + selected + '>' + so + '</option>';
                }
                sizer = sizer.replace(/{{SIZES}}/g, sizeopts);

                this.component.context.html(sizer);

                var sizeSelector = edges.css_class_selector(this.namespace, "size", this);
                edges.on(sizeSelector, "change", this, "changeSize");

            };

            this.changeSize = function (element) {
                var size = $(element).val();
                this.component.setSize(size);
            };
        },

        newShareEmbedRenderer: function (params) {
            return edges.instantiate(doaj.renderers.ShareEmbedRenderer, params, edges.newRenderer);
        },
        ShareEmbedRenderer: function (params) {
            // enable the share/save link feature
            this.shareLinkText = edges.getParam(params.shareLinkText, "share");

            ////////////////////////////////////////
            // state variables

            this.shareBoxOpen = false;

            this.showShortened = false;

            this.namespace = "doaj-share-embed";

            this.draw = function () {
                // reset these on each draw
                this.shareBoxOpen = false;
                this.showShortened = false;

                var comp = this.component;

                var shareButtonFrag = "";
                var shareButtonClass = edges.css_classes(this.namespace, "toggle-share", this);
                var modalId = edges.css_id(this.namespace, "modal", this);
                shareButtonFrag = '<button href="#" data-toggle="modal" data-target="#' + modalId + '" class="' + shareButtonClass + ' input_group__input" type="button">' + this.shareLinkText + '</button>';

                var shorten = "";
                if (this.component.urlShortener) {
                    var shortenClass = edges.css_classes(this.namespace, "shorten", this);
                    shorten = '<div class="' + shortenClass + '">Share a link to this search</div>'
                }
                var embed = "";
                if (this.component.embedSnippet) {
                    var embedClass = edges.css_classes(this.namespace, "embed", this);
                    embed = '<div class="row">\
                        <div class="col-md-12">\
                            Embed this search in your webpage\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-12">\
                            <textarea style="width: 100%; height: 150px" readonly class="' + embedClass + '"></textarea>\
                        </div>\
                    </div>';
                }
                var shareBoxClass = edges.css_classes(this.namespace, "share", this);
                var shareUrlClass = edges.css_classes(this.namespace, "share-url", this);
                var shortenButtonClass = edges.css_classes(this.namespace, "shorten-url", this);
                var shareFrag = '<div class="' + shareBoxClass + '">\
                    <div class="row">\
                        <div class="col-md-11">\
                            ' + shorten + '\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-md-12">\
                            <textarea style="width: 100%; height: 150px" readonly class="' + shareUrlClass + '"></textarea>\
                            <button class="input_group__input ' + shortenButtonClass + '">shorten url</button>\
                        </div>\
                    </div>\
                    ' + embed + '\
                </div>';

                var modal = '<section class="modal" id="' + modalId + '" tabindex="-1" role="dialog">\
                    <div class="modal__dialog" role="document">\
                        <form class="quick-search__form" role="search">\
                            <h2 class="modal__title">' + this.shareLinkText + '</h2>\
                            ' + shareFrag + '\
                        </form>\
                    </div>\
                </section>';

                var frag = shareButtonFrag + modal;

                comp.context.html(frag);
                feather.replace();

                var shareSelector = edges.css_class_selector(this.namespace, "toggle-share", this);
                edges.on(shareSelector, "click", this, "toggleShare");

                if (this.component.urlShortener) {
                    var shortenSelector = edges.css_class_selector(this.namespace, "shorten-url", this);
                    edges.on(shortenSelector, "click", this, "toggleShorten");
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.toggleShare = function(element) {
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var textarea = this.component.jq(shareUrlSelector);
                if (this.shareBoxOpen) {
                    textarea.val("");
                    if (this.component.embedSnippet) {
                        var embedSelector = edges.css_class_selector(this.namespace, "embed", this);
                        var embedTextarea = this.component.jq(embedSelector);
                        embedTextarea.val("");
                    }
                    this.shareBoxOpen = false;
                } else {
                    if (this.showShortened) {
                        textarea.val(this.component.shortUrl);
                    } else {
                        textarea.val(this.component.edge.fullUrl());
                    }
                    if (this.component.embedSnippet) {
                        var embedSelector = edges.css_class_selector(this.namespace, "embed", this);
                        var embedTextarea = this.component.jq(embedSelector);
                        embedTextarea.val(this.component.embedSnippet(this));
                    }
                    this.shareBoxOpen = true;
                }
            };

            this.toggleShorten = function(element) {
                if (!this.component.shortUrl) {
                    var callback = edges.objClosure(this, "updateShortUrl");
                    this.component.generateShortUrl(callback);
                } else {
                    this.updateShortUrl();
                }
            };

            this.updateShortUrl = function() {
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var shortenSelector = edges.css_class_selector(this.namespace, "shorten", this);
                var textarea = this.component.jq(shareUrlSelector);
                var button = this.component.jq(shortenSelector).find("button");
                if (this.showShortened) {
                    textarea.val(this.component.edge.fullUrl());
                    button.html('<span class="glyphicon glyphicon-resize-small"></span>shorten url');
                    this.showShortened = false;
                } else {
                    textarea.val(this.component.shortUrl);
                    button.html('<span class="glyphicon glyphicon-resize-full"></span>original url');
                    this.showShortened = true;
                }
            };
        },

        newSearchBarRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchBarRenderer, params, edges.newRenderer);
        },
        SearchBarRenderer: function (params) {
            // enable the search button
            this.searchButton = edges.getParam(params.searchButton, false);

            // text to include on the search button.  If not provided, will just be the magnifying glass
            this.searchButtonText = edges.getParam(params.searchButtonText, false);

            // should the clear button be rendered
            this.clearButton = edges.getParam(params.clearButton, true);

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            ////////////////////////////////////////
            // state variables

            this.namespace = "doaj-bs3-search-controller";

            this.draw = function () {
                var comp = this.component;

                // FIXME: leaving this in in case we need to add it in production
                //var clearClass = edges.css_classes(this.namespace, "reset", this);
                //var clearFrag = "";
                //if (this.clearButton) {
                //    clearFrag = '<button type="button" class="btn btn-danger btn-sm ' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                //            <span class="glyphicon glyphicon-remove"></span> \
                //        </button>';
                //}

                // select box for fields to search on
                var field_select = "";
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    // classes that we'll use
                    var searchFieldClass = edges.css_classes(this.namespace, "field", this);
                    var searchFieldId = edges.css_id(this.namespace, "fields", this);

                    field_select += '<select class="' + searchFieldClass + ' input-group__input" name="fields" id="' + searchFieldId + '">';
                    field_select += '<option value="">All fields</option>';

                    for (var i = 0; i < comp.fieldOptions.length; i++) {
                        var obj = comp.fieldOptions[i];
                        field_select += '<option value="' + obj['field'] + '">' + edges.escapeHtml(obj['display']) + '</option>';
                    }
                    field_select += '</select>';
                }

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);

                var searchFrag = "";
                if (this.searchButton) {
                    var text = '<span class="glyphicon glyphicon-white glyphicon-search"></span>';
                    if (this.searchButtonText !== false) {
                        text = this.searchButtonText;
                    }
                    searchFrag = '<span class="input-group-btn"> \
                        <button type="button" class="btn btn-info btn-sm ' + searchClass + '"> \
                            ' + text + ' \
                        </button> \
                    </span>';
                }

                var textId = edges.css_id(this.namespace, "text", this);
                var searchBox = '<input type="text" id="' + textId + '" class="' + textClass + ' input-group__input" name="q" value="" placeholder="' + this.searchPlaceholder + '"/>';

                var searchClass = edges.css_classes(this.namespace, "search", this);
                var button = '<button class="' + searchClass + ' input-group__input" type="submit">\
                        <span data-feather="search" aria-hidden="true"></span><span class="sr-only"> Search</span>\
                    </button>';

                // if (clearFrag !== "") {
                //     clearFrag = '<div class="col-md-1 col-xs-12">' + clearFrag + "</div>";
                //}

                var sr1 = '<label for="keywords" class="sr-only">Search by keywords:</label>';
                var sr2 = '<label for="fields" class="sr-only">In the field:</label>';
                var frag = '<div class="input-group">' + sr1 + searchBox + sr2 + field_select + button + '</div>';

                comp.context.html(frag);

                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    this.setUISearchField();
                }
                this.setUISearchText();

                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                    edges.on(fieldSelector, "change", this, "changeSearchField");
                }
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                if (this.freetextSubmitDelay > -1) {
                    edges.on(textSelector, "keyup", this, "setSearchText", this.freetextSubmitDelay);
                } else {
                    function onlyEnter(event) {
                        var code = (event.keyCode ? event.keyCode : event.which);
                        return code === 13;
                    }

                    edges.on(textSelector, "keyup", this, "setSearchText", false, onlyEnter);
                }

                //var resetSelector = edges.css_class_selector(this.namespace, "reset", this);
                //edges.on(resetSelector, "click", this, "clearSearch");

                var searchSelector = edges.css_class_selector(this.namespace, "search", this);
                edges.on(searchSelector, "click", this, "doSearch");

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISearchField = function () {
                if (!this.component.searchField) {
                    return;
                }
                // get the selector we need
                var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                var el = this.component.jq(fieldSelector);
                el.val(this.component.searchField);
            };

            this.setUISearchText = function () {
                if (!this.component.searchString) {
                    return;
                }
                // get the selector we need
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                var el = this.component.jq(textSelector);
                el.val(this.component.searchString);
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSearchField = function (element) {
                var val = this.component.jq(element).val();
                this.component.setSearchField(val);
            };

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val);
            };

            this.clearSearch = function (element) {
                this.component.clearSearch();
            };

            this.doSearch = function (element) {
                var textId = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textId).val();
                this.component.setSearchText(text);
            };
        },

        newFacetFilterSetterRenderer: function (params) {
            return edges.instantiate(doaj.renderers.FacetFilterSetterRenderer, params, edges.newRenderer);
        },
        FacetFilterSetterRenderer: function (params) {
            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            // whether the facet can be opened and closed
            this.togglable = edges.getParam(params.togglable, true);

            // whether the count should be displayed along with the term
            // defaults to false because count may be confusing to the user in an OR selector
            this.showCount = edges.getParam(params.showCount, true);

            // The display title for the facet
            this.facetTitle = edges.getParam(params.facetTitle, "Untitled");

            this.openIcon = edges.getParam(params.openIcon, "glyphicon glyphicon-plus");

            this.closeIcon = edges.getParam(params.closeIcon, "glyphicon glyphicon-minus");

            // namespace to use in the page
            this.namespace = "doaj-facet-filter-setter";

            this.draw = function () {
                // for convenient short references ...
                var comp = this.component;
                var namespace = this.namespace;

                var checkboxClass = edges.css_classes(namespace, "selector", this);

                var filters = "";
                for (var i = 0; i < comp.filters.length; i++) {
                    var filter = comp.filters[i];
                    var id = filter.id;
                    var display = filter.display;
                    var count = comp.filter_counts[id];
                    var active = comp.active_filters[id];

                    if (count === undefined) {
                        count = 0;
                    }

                    var checked = "";
                    if (active) {
                        checked = ' checked="checked" ';
                    }
                    filters += '<li>\
                            <input class="' + checkboxClass + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                            <label for="' + id + '" class="filter__label">' + display + '</label>\
                        </li>';
                }

                var frag = '<h3 class="filter__heading">' + this.facetTitle + '</h3>\
                    <ul class="filter__choices">{{FILTERS}}</ul>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, filters);

                // now render it into the page
                comp.context.html(frag);

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                var openBits = this.openIcon.split(" ");
                var closeBits = this.closeIcon.split(" ");

                if (this.open) {
                    var i = toggle.find("i");
                    for (var j = 0; j < openBits.length; j++) {
                        i.removeClass(openBits[j]);
                    }
                    for (var j = 0; j < closeBits.length; j++) {
                        i.addClass(closeBits[j]);
                    }
                    results.show();
                } else {
                    var i = toggle.find("i");
                    for (var j = 0; j < closeBits.length; j++) {
                        i.removeClass(closeBits[j]);
                    }
                    for (var j = 0; j < openBits.length; j++) {
                        i.addClass(openBits[j]);
                    }
                    results.hide();
                }
            };

            this.filterToggle = function(element) {
                var filter_id = this.component.jq(element).attr("id");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.addFilter(filter_id);
                } else {
                    this.component.removeFilter(filter_id);
                }
            };

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newORTermSelectorRenderer: function (params) {
            return edges.instantiate(doaj.renderers.ORTermSelectorRenderer, params, edges.newRenderer);
        },
        ORTermSelectorRenderer: function (params) {
            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            this.togglable = edges.getParam(params.togglable, true);

            // whether the count should be displayed along with the term
            // defaults to false because count may be confusing to the user in an OR selector
            this.showCount = edges.getParam(params.showCount, false);

            // whether counts of 0 should prevent the value being rendered
            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            // namespace to use in the page
            this.namespace = "doaj-or-term-selector";

            this.draw = function () {
                // for convenient short references ...
                var ts = this.component;
                var namespace = this.namespace;

                // sort out all the classes that we're going to be using
                var resultClass = edges.css_classes(namespace, "result", this);
                var valClass = edges.css_classes(namespace, "value", this);
                var filterRemoveClass = edges.css_classes(namespace, "filter-remove", this);
                var facetClass = edges.css_classes(namespace, "facet", this);
                var headerClass = edges.css_classes(namespace, "header", this);
                var selectionsClass = edges.css_classes(namespace, "selections", this);
                var bodyClass = edges.css_classes(namespace, "body", this);
                var countClass = edges.css_classes(namespace, "count", this);

                var checkboxClass = edges.css_classes(namespace, "selector", this);

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results
                var results = "<li>Loading...</li>";

                // render a list of the values
                if (ts.terms.length > 0) {
                    results = "";

                    for (var i = 0; i < ts.terms.length; i++) {
                        var val = ts.terms[i];
                        if (val.count === 0 && this.hideEmpty) {
                            continue
                        }

                        var active = $.inArray(val.term.toString(), ts.selected) > -1;
                        var checked = "";
                        if (active) {
                            checked = ' checked="checked" ';
                        }
                        var count = "";
                        if (this.showCount) {
                            count = ' <span class="' + countClass + '">(' + val.count + ')</span>';
                        }
                        var id = edges.safeId(val.term);
                        results += '<li>\
                                <input class="' + checkboxClass + '" data-key="' + edges.escapeHtml(val.term) + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                                <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + count + '</label>\
                            </li>';
                    }

                    /*
                    // render each value, if it is not also a filter that has been set
                    for (var i = 0; i < ts.terms.length; i++) {
                        var val = ts.terms[i];
                        // should we ignore the empty counts
                        if (val.count === 0 && this.hideEmpty) {
                            continue
                        }
                        // otherwise, render any that aren't selected already
                        if ($.inArray(val.term.toString(), ts.selected) === -1) {   // the toString() helps us normalise other values, such as integers
                            results += '<div class="' + resultClass + '"><a href="#" class="' + valClass + '" data-key="' + edges.escapeHtml(val.term) + '">' +
                                edges.escapeHtml(val.display) + "</a>";
                            if (this.showCount) {
                                results += ' <span class="' + countClass + '">(' + val.count + ')</span>';
                            }
                            results += "</div>";
                        }
                    }*/
                }

                /*
                // if we want the active filters, render them
                var filterFrag = "";
                if (ts.selected.length > 0) {
                    for (var i = 0; i < ts.selected.length; i++) {
                        var filt = ts.selected[i];
                        var def = this._getFilterDef(filt);
                        if (def) {
                            filterFrag += '<div class="' + resultClass + '"><strong>' + edges.escapeHtml(def.display);
                            if (this.showCount) {
                                filterFrag += " (" + def.count + ")";
                            }
                            filterFrag += '&nbsp;<a href="#" class="' + filterRemoveClass + '" data-key="' + edges.escapeHtml(def.term) + '">';
                            filterFrag += '<i class="glyphicon glyphicon-black glyphicon-remove"></i></a>';
                            filterFrag += "</strong></a></div>";
                        }
                    }
                }*/

                /*
                // render the overall facet
                var frag = '<div class="' + facetClass + '">\
                        <div class="' + headerClass + '"><div class="row"> \
                            <div class="col-md-12">\
                                ' + header + '\
                            </div>\
                        </div></div>\
                        <div class="' + bodyClass + '">\
                            <div class="row" style="display:none" id="' + resultsId + '">\
                                <div class="col-md-12">\
                                    {{SELECTED}}\
                                </div>\
                                <div class="col-md-12"><div class="' + selectionsClass + '">\
                                    {{RESULTS}}\
                                </div>\
                            </div>\
                        </div>\
                        </div></div>';
                */

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var frag = '<h3 class="filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, results);

                // now render it into the page
                ts.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");
                /*
                // sort out the selectors we're going to be needing
                var valueSelector = edges.css_class_selector(namespace, "value", this);
                var filterRemoveSelector = edges.css_class_selector(namespace, "filter-remove", this);
                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);

                // for when a value in the facet is selected
                edges.on(valueSelector, "click", this, "termSelected");
                // for when the open button is clicked
                edges.on(toggleSelector, "click", this, "toggleOpen");
                // for when a filter remove button is clicked
                edges.on(filterRemoveSelector, "click", this, "removeFilter");
                 */
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < openBits.length; j++) {
                    //    i.removeClass(openBits[j]);
                   // }
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.addClass(closeBits[j]);
                    //}
                    //results.show();

                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.removeClass(closeBits[j]);
                   // }
                    //for (var j = 0; j < openBits.length; j++) {
                     //   i.addClass(openBits[j]);
                    //}
                    //results.hide();

                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function(element) {
                var term = this.component.jq(element).attr("data-key");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.selectTerm(term);
                } else {
                    this.component.removeFilter(term);
                }
            };

            /*
            this.termSelected = function (element) {
                var term = this.component.jq(element).attr("data-key");
                this.component.selectTerm(term);
            };

            this.removeFilter = function (element) {
                var term = this.component.jq(element).attr("data-key");
                this.component.removeFilter(term);
            };*/

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newDateHistogramSelectorRenderer: function (params) {
            return edges.instantiate(doaj.renderers.DateHistogramSelectorRenderer, params, edges.newRenderer);
        },
        DateHistogramSelectorRenderer: function (params) {

            ///////////////////////////////////////
            // parameters that can be passed in

            // whether to hide or just disable the facet if not active
            this.hideInactive = edges.getParam(params.hideInactive, false);

            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            this.togglable = edges.getParam(params.togglable, true);

            // whether to display selected filters
            this.showSelected = edges.getParam(params.showSelected, true);

            this.showCount = edges.getParam(params.showCount, true);

            // formatter for count display
            this.countFormat = edges.getParam(params.countFormat, false);

            // whether to suppress display of date range with no values
            this.hideEmptyDateBin = params.hideEmptyDateBin || true;

            // namespace to use in the page
            this.namespace = "doaj-datehistogram-selector";

            this.draw = function () {
                // for convenient short references ...
                var ts = this.component;
                var namespace = this.namespace;

                if (!ts.active && this.hideInactive) {
                    ts.context.html("");
                    return;
                }

                // sort out all the classes that we're going to be using
                var resultsListClass = edges.css_classes(namespace, "results-list", this);
                var resultClass = edges.css_classes(namespace, "result", this);
                var valClass = edges.css_classes(namespace, "value", this);
                var filterRemoveClass = edges.css_classes(namespace, "filter-remove", this);
                var facetClass = edges.css_classes(namespace, "facet", this);
                var headerClass = edges.css_classes(namespace, "header", this);
                var selectedClass = edges.css_classes(namespace, "selected", this);
                var checkboxClass = edges.css_classes(namespace, "selector", this);
                var countClass = edges.css_classes(namespace, "count", this);

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results
                var results = "<li>Loading...</li>";
                if (ts.values !== false) {
                    results = "<li>No data available</li>";
                }

                // render a list of the values
                if (ts.values && ts.values.length > 0) {
                    results = "";

                    // get the terms of the filters that have already been set
                    var filterTerms = [];
                    for (var i = 0; i < ts.filters.length; i++) {
                        filterTerms.push(ts.filters[i].display);
                    }

                    // render each value, if it is not also a filter that has been set
                    for (var i = 0; i < ts.values.length; i++) {
                        var val = ts.values[i];
                        if ($.inArray(val.display, filterTerms) === -1) {

                            var ltData = "";
                            if (val.lt) {
                                ltData = ' data-lt="' + edges.escapeHtml(val.lt) + '" ';
                            }
                            //results += '<div class="' + resultClass + ' ' + myLongClass + '" '  + styles +  '><a href="#" class="' + valClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + '>' +
                            //    edges.escapeHtml(val.display) + "</a> (" + count + ")</div>";

                            var count = "";
                            if (this.showCount) {
                                count = val.count;
                                if (this.countFormat) {
                                    count = this.countFormat(count)
                                }
                                count = ' <span class="' + countClass + '">(' + count + ')</span>';
                            }
                            var id = edges.safeId(val.display.toString());
                            results += '<li>\
                                    <input class="' + checkboxClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + ' id="' + id + '" type="checkbox" name="' + id + '">\
                                    <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + count + '</label>\
                                </li>';
                        }
                    }
                }

                // if we want the active filters, render them
                var filterFrag = "";
                if (ts.filters.length > 0 && this.showSelected) {
                    for (var i = 0; i < ts.filters.length; i++) {
                        var filt = ts.filters[i];
                        var ltData = "";
                        if (filt.lt) {
                            ltData = ' data-lt="' + edges.escapeHtml(filt.lt) + '" ';
                        }
                        filterFrag += '<li>\
                                    <input checked="checked" class="' + checkboxClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + ' id="' + id + '" type="checkbox" name="' + id + '">\
                                    <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + '</label>\
                                </li>';

                        /*
                        filterFrag += '<div class="' + resultClass + '"><strong>' + edges.escapeHtml(filt.display) + "&nbsp;";
                        filterFrag += '<a href="#" class="' + filterRemoveClass + '" data-gte="' + edges.escapeHtml(filt.gte) + '"' + ltData + '>';
                        filterFrag += '<i class="glyphicon glyphicon-black glyphicon-remove"></i></a>';
                        filterFrag += "</strong></a></div>";
                         */
                    }
                }

                /*
                // render the toggle capability
                var tog = ts.display;
                if (this.togglable) {
                    tog = '<a href="#" id="' + toggleId + '"><i class="glyphicon glyphicon-plus"></i>&nbsp;' + tog + "</a>";
                }

                // render the overall facet
                var frag = '<div class="' + facetClass + '">\
                        <div class="' + headerClass + '"><div class="row"> \
                            <div class="col-md-12">\
                                ' + tog + '\
                            </div>\
                        </div></div>\
                        ' + tooltipFrag + '\
                        <div class="row" style="display:none" id="' + resultsId + '">\
                            <div class="col-md-12">\
                                <div class="' + selectedClass + '">{{SELECTED}}</div>\
                                <div class="' + resultsListClass + '">{{RESULTS}}</div>\
                            </div>\
                        </div></div>';
                */

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var frag = '<h3 class="filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, filterFrag + results);

                // now render it into the page
                ts.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");

                /*
                // sort out the selectors we're going to be needing
                var valueSelector = edges.css_class_selector(namespace, "value", this);
                var filterRemoveSelector = edges.css_class_selector(namespace, "filter-remove", this);
                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                var tooltipSelector = edges.css_id_selector(namespace, "tooltip-toggle", this);
                var shortLongToggleSelector = edges.css_id_selector(namespace, "sl-toggle", this);

                // for when a value in the facet is selected
                edges.on(valueSelector, "click", this, "termSelected");
                // for when the open button is clicked
                edges.on(toggleSelector, "click", this, "toggleOpen");
                // for when a filter remove button is clicked
                edges.on(filterRemoveSelector, "click", this, "removeFilter");
                // toggle the full tooltip
                edges.on(tooltipSelector, "click", this, "toggleTooltip");
                // toggle show/hide full list
                edges.on(shortLongToggleSelector, "click", this, "toggleShortLong");

                 */
            };

            /////////////////////////////////////////////////////
            // UI behaviour functions

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < openBits.length; j++) {
                    //    i.removeClass(openBits[j]);
                   // }
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.addClass(closeBits[j]);
                    //}
                    //results.show();

                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.removeClass(closeBits[j]);
                   // }
                    //for (var j = 0; j < openBits.length; j++) {
                     //   i.addClass(openBits[j]);
                    //}
                    //results.hide();

                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

            this.filterToggle = function(element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.selectRange({gte: gte, lt: lt});
                } else {
                    this.component.removeFilter({gte: gte, lt: lt});
                }
            };

            /*
            this.termSelected = function (element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                this.component.selectRange({gte: gte, lt: lt});
            };

            this.removeFilter = function (element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                this.component.removeFilter({gte: gte, lt: lt});
            };

             */

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newSelectedFiltersRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SelectedFiltersRenderer, params, edges.newRenderer);
        },
        SelectedFiltersRenderer: function (params) {

            this.showFilterField = edges.getParam(params.showFilterField, true);

            this.showSearchString = edges.getParam(params.showSearchString, false);

            this.ifNoFilters = edges.getParam(params.ifNoFilters, false);

            this.namespace = "doaj-selected-filters";

            this.draw = function () {
                // for convenient short references
                var sf = this.component;
                var ns = this.namespace;

                // sort out the classes we are going to use
                var fieldClass = edges.css_classes(ns, "field", this);
                var fieldNameClass = edges.css_classes(ns, "fieldname", this);
                var valClass = edges.css_classes(ns, "value", this);
                var relClass = edges.css_classes(ns, "rel", this);
                var containerClass = edges.css_classes(ns, "container", this);

                var filters = "";

                if (this.showSearchString && sf.searchString) {
                    var field = sf.searchField;
                    var text = sf.searchString;
                    filters += '<span class="' + fieldClass + '">';
                    if (field) {
                        if (field in sf.fieldDisplays) {
                            field = sf.fieldDisplays[field];
                        }
                        filters += '<span class="' + fieldNameClass + '">' + field + ':</span>';
                    }
                    filters += '<span class="' + valClass + '">"' + text + '"</span>';
                    filters += '</span>';
                }

                var fields = Object.keys(sf.mustFilters);
                for (var i = 0; i < fields.length; i++) {
                    var field = fields[i];
                    var def = sf.mustFilters[field];

                    for (var j = 0; j < def.values.length; j++) {
                        var val = def.values[j];
                        filters += '<li class="tag ' + valClass + '">';

                        // the remove block looks different, depending on the kind of filter to remove
                        var removeClass = edges.css_classes(ns, "remove", this);
                        if (def.filter == "term" || def.filter === "terms") {
                            filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" data-value="' + val.val + '" alt="Remove" title="Remove">';
                            filters += def.display + ": " + val.display;
                            filters += ' <span data-feather="x" aria-hidden="true"></span>';
                            filters += "</a>";
                        } else if (def.filter === "range") {
                            var from = val.from ? ' data-' + val.fromType + '="' + val.from + '" ' : "";
                            var to = val.to ? ' data-' + val.toType + '="' + val.to + '" ' : "";
                            filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" ' + from + to + ' alt="Remove" title="Remove">';
                            filters += def.display + ": " + val.display;
                            filters += ' <span data-feather="x" aria-hidden="true"></span>';
                            filters += "</a>";
                        }

                        filters += "</li>";
                    }
                    filters += "</span>";
                }

                if (filters === "" && this.ifNoFilters) {
                    filters = this.ifNoFilters;
                }

                if (filters !== "") {
                    var frag = '<ul class="tags ' + containerClass + '">{{FILTERS}}</ul>';
                    frag = frag.replace(/{{FILTERS}}/g, filters);
                    sf.context.html(frag);
                    feather.replace();

                    // click handler for when a filter remove button is clicked
                    var removeSelector = edges.css_class_selector(ns, "remove", this);
                    edges.on(removeSelector, "click", this, "removeFilter");
                } else {
                    sf.context.html("");
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

            this.removeFilter = function (element) {
                var el = this.component.jq(element);
                var field = el.attr("data-field");
                var ft = el.attr("data-filter");
                var bool = el.attr("data-bool");

                var value = false;
                if (ft === "terms" || ft === "term") {
                    value = el.attr("data-value");
                } else if (ft === "range") {
                    value = {};

                    var from = el.attr("data-gte");
                    var fromType = "gte";
                    if (!from) {
                        from = el.attr("data-gt");
                        fromType = "gt";
                    }

                    var to = el.attr("data-lt");
                    var toType = "lt";
                    if (!to) {
                        to = el.attr("data-lte");
                        toType = "lte";
                    }

                    if (from) {
                        value["from"] = parseInt(from);
                        value["fromType"] = fromType;
                    }
                    if (to) {
                        value["to"] = parseInt(to);
                        value["toType"] = toType;
                    }
                }

                this.component.removeFilter(bool, ft, field, value);
            };
        },

        newPagerRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PagerRenderer, params, edges.newRenderer);
        },
        PagerRenderer: function (params) {

            this.scroll = edges.getParam(params.scroll, true);

            this.scrollSelector = edges.getParam(params.scrollSelector, "body");

            this.numberFormat = edges.getParam(params.numberFormat, false);

            this.namespace = "doaj-pager";

            this.draw = function () {
                if (this.component.total === false || this.component.total === 0) {
                    this.component.context.html("");
                    return;
                }

                // classes we'll need
                var navClass = edges.css_classes(this.namespace, "nav", this);
                var firstClass = edges.css_classes(this.namespace, "first", this);
                var prevClass = edges.css_classes(this.namespace, "prev", this);
                var pageClass = edges.css_classes(this.namespace, "page", this);
                var nextClass = edges.css_classes(this.namespace, "next", this);

                var first = '<li><span data-feather="chevrons-left" aria-hidden="true"></span> <a href="#" class="' + firstClass + '">First</a></li>';
                var prev = '<li><span data-feather="chevron-left" aria-hidden="true"></span> <a href="#" class="' + prevClass + '">Prev</a></li>';
                if (this.component.page === 1) {
                    first = '<li><span data-feather="chevrons-left" aria-hidden="true"></span> First</li>';
                    prev = '<li><span data-feather="chevron-left" aria-hidden="true"></span> Prev</li>';
                }

                var next = '<li><a href="#" class="' + nextClass + '">Next <span data-feather="chevron-right" aria-hidden="true"></span></a></li>';
                if (this.component.page === this.component.totalPages) {
                    next = '<li>Next <span data-feather="chevron-right" aria-hidden="true"></span></li>';
                }

                var pageNum = this.component.page;
                var totalPages = this.component.totalPages;
                if (this.numberFormat) {
                    pageNum = this.numberFormat(pageNum);
                    totalPages = this.numberFormat(totalPages);
                }
                var nav = '<h3 class="sr-only">Jump to&hellip;</h3><ul class="' + navClass + '">' + first + prev +
                    '<li class="' + pageClass + '"><strong>Page ' + pageNum + ' of ' + totalPages + '</strong></li>' +
                    next + "</ul>";

                this.component.context.html(nav);
                feather.replace();

                // now create the selectors for the functions
                var firstSelector = edges.css_class_selector(this.namespace, "first", this);
                var prevSelector = edges.css_class_selector(this.namespace, "prev", this);
                var nextSelector = edges.css_class_selector(this.namespace, "next", this);

                // bind the event handlers
                if (this.component.page !== 1) {
                    edges.on(firstSelector, "click", this, "goToFirst");
                    edges.on(prevSelector, "click", this, "goToPrev");
                }
                if (this.component.page !== this.component.totalPages) {
                    edges.on(nextSelector, "click", this, "goToNext");
                }
            };

            this.doScroll = function () {
                $(this.scrollSelector).animate({    // note we do not use component.jq, because the scroll target could be outside it
                    scrollTop: $(this.scrollSelector).offset().top
                }, 1);
            };

            this.goToFirst = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.setFrom(1);
            };

            this.goToPrev = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.decrementPage();
            };

            this.goToNext = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.incrementPage();
            };
        },

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
                    // var recordClasses = edges.css_classes(this.namespace, "record", this);

                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                        // frag += '<div class="row"><div class="col-md-12"><div class="' + recordClasses + '">' + rec + '</div></div></div>';
                    }
                }

                // finally stick it all together into the container
                //var containerClasses = edges.css_classes(this.namespace, "container", this);
                //var container = '<div class="' + containerClasses + '">' + frag + '</div>';
                this.component.context.html(frag);
                feather.replace();

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
                var seal = "";
                if (edges.objVal("admin.seal", resultobj, false)) {
                    seal = '<a href="/apply/seal" class="tag tag--featured">\
                            <span data-feather="check-circle" aria-hidden="true"></span>\
                            DOAJ Seal\
                          </a>';
                }
                var issn = resultobj.bibjson.issn;
                if (!issn) {
                    issn = resultobj.bibjson.eissn;
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + resultobj.bibjson.alternative_title + '</span>';
                }

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.publisher")) {
                    var name = "";
                    var country = "";
                    if (resultobj.bibjson.publisher.name) {
                        name = 'by <em>' + resultobj.bibjson.publisher.name + '</em>';
                    }
                    if (resultobj.bibjson.publisher.country && edges.hasProp(resultobj, "index.country")) {
                        country = 'in <strong>' + resultobj.index.country + '</strong>';
                    }
                    published = 'Published ' + name + " " + country;
                }

                // add the subjects
                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = "<li>" + resultobj.index.classification_paths.join("</li><li>") + "</li>";
                }

                var update_or_added = "";
                if (resultobj.last_manual_update && resultobj.last_manual_update !== '1970-01-01T00:00:00Z') {
                    update_or_added = 'Last updated on ' + doaj.humanDate(resultobj.last_manual_update);
                } else {
                    update_or_added = 'Added on ' + doaj.humanDate(resultobj.created_date);
                }

                // FIXME: this is to present the number of articles indexed, which is not information we currently possess
                // at search time
                var articles = "";

                var apcs = '<li>';
                if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                    apcs += "APCs: ";
                    for (var i = 0; i < resultobj.bibjson.apc.max.length; i++) {
                        apcs += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apcs += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apcs += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        apcs += "</strong>";
                    }
                } else {
                    apcs += "<strong>No</strong> charges";
                }
                apcs += '</li>';

                var licenses = "";
                if (resultobj.bibjson.license && resultobj.bibjson.license.length > 0) {
                    var terms_url = resultobj.bibjson.ref.license_terms;
                    for (var i = 0; i < resultobj.bibjson.license.length; i++) {
                        var lic = resultobj.bibjson.license[i];
                        var license_url = lic.url || terms_url;
                        licenses += '<a href="' + license_url + '" target="_blank" rel="noopener">' + lic.type + '</a>';
                    }
                }

                var frag = '<li class="search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          ' + seal + '\
                          <h3 class="search-results__heading">\
                            <a href="/toc/' + issn + '">\
                              ' + resultobj.bibjson.title + '\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul>\
                            <li>\
                              ' + published + '\
                            </li>\
                            <li>\
                              Accepts manuscripts in <strong>' + resultobj.index.language.join(", ") + '</strong>\
                            </li>\
                          </ul>\
                          <ul>\
                            ' + subjects + '\
                          <ul>\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <ul>\
                          <li>\
                            ' + update_or_added + '\
                          </li>\
                          ' + articles + '\
                          <li>\
                            <a href="' + resultobj.bibjson.ref.journal + '" target="_blank" rel="noopener">Website <span data-feather="external-link" aria-hidden="true"></span></a>\
                          </li>\
                          <li>\
                            ' + apcs + '\
                          </li>\
                          <li>\
                            ' + licenses + '\
                          </li>\
                        </ul>\
                      </aside>\
                    </article>\
                  </li>';

                return frag;
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
                result += "<div class='pull-left' style='width: 4%; min-width: 33px'>";
                result += "<i style='font-size: 24px' class='far fa-file-alt'></i>";
                result += "</div>";

                result += "<div class='pull-left' style='width: 93%'>";

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
                            var field = edges.escapeHtml(author.name);
                            anames.push(field);
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
                    var display = edges.escapeHtml(resultobj.bibjson.title);
                    if (resultobj.admin.in_doaj) {
                        display =  "<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + display + "</a>";
                    }
                    field += "&nbsp;" + display;
                } else {
                    field += "&nbsp" + edges.escapeHtml(resultobj.bibjson.title);
                }
                if (resultobj.admin && resultobj.admin.ticked) {
                    field += "&nbsp<img src='/static/doaj/images/tick_short.png' width='16px' height='16px' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014'>​​";
                }
                if (resultobj.admin && resultobj.admin.seal) {
                    field += "&nbsp<img src='/static/doaj/images/seal_short.png' width='16px' height='16px' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal'>​​";
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