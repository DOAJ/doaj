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

            this.titleBar = edges.getParam(params.titleBar, true);

            this.draw = function (edge) {
                this.edge = edge;

                var titleBarFrag = "";
                if (this.titleBar) {
                    titleBarFrag = '<header class="search__header" style="background-image: url(\'/static/doaj/images/search-background.jpg\')"> \
                        <p class="label">Search</p>\n \
                        <h1>' + this.title + ' \
                            <span data-feather="help-circle" aria-hidden="true" data-toggle="modal" data-target="#modal-help" type="button"></span><span class="sr-only">Help</span> \
                        </h1> \
                        <div class="row">\
                            <div id="search-input-bar" class="col-md-9"></div>\
                        </div>\
                    </header>';
                }

                var frag = titleBarFrag + '\
                    <h2 id="result-count"></h2>\
                    <div class="row">\
                        <div class="col-md-3">\
                            <aside class="filters">\
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
                edge.context.html(frag);
            };
        },

        newPublisherApplications: function (params) {
            return edges.instantiate(doaj.templates.PublisherApplications, params, edges.newTemplate);
        },
        PublisherApplications: function (params) {
            this.namespace = "doajpublisherapplications";

            this.draw = function (edge) {
                this.edge = edge;

                var frag = '<div class="row">\
                    <div class="col-md-12">\
                        <nav class="pagination" id="top-pager"></nav>\
                        <ol class="search-results" id="results"></ol>\
                        <nav class="pagination" id="bottom-pager"></nav>\
                    </div>\
                </div>';

                edge.context.html(frag);
            };
        }
    },

    renderers : {
        newSubjectBrowser : function(params) {
            return edges.instantiate(doaj.renderers.SubjectBrowser, params, edges.newRenderer);
        },
        SubjectBrowser : function(params) {
            this.title = edges.getParam(params.title, "");

            this.selectMode = edges.getParam(params.selectMode, "multiple");

            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            this.togglable = edges.getParam(params.togglable, true);

            this.open = edges.getParam(params.open, false);

            this.namespace = "doaj-subject-browser";

            this.draw = function() {
                // for convenient short references ...
                var st = this.component.syncTree;
                var namespace = this.namespace;
                var that = this;

                var checkboxClass = edges.css_classes(namespace, "selector", this);
                var countClass = edges.css_classes(namespace, "count", this);

                function renderEntry(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return "";
                    }

                    var id = edges.safeId(entry.value);
                    var checked = "";
                    if (entry.selected) {
                        checked = ' checked="checked" ';
                    }
                    // FIXME: putting this in for the moment, just so we can use it in dev
                    var count = ' <span class="' + countClass + '">(' + entry.count + '/' + entry.childCount + ')</span>';

                    var frag = '<input class="' + checkboxClass + '" data-value="' + edges.escapeHtml(entry.value) + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                        <label for="' + id + '" class="filter__label">' + edges.escapeHtml(entry.display) + count + '</label>';

                    return frag;
                }

                function recurse(tree) {
                    var rFrag = "";
                    for (var i = 0; i < tree.length; i++) {
                        var entry = tree[i];
                        var entryFrag = renderEntry(entry);
                        if (entryFrag === "") {
                            continue;
                        }
                        if (entry.children) {
                            var cFrag = recurse(entry.children);
                            if (cFrag !== "") {
                                entryFrag += '<ul class="filter__choices">';
                                entryFrag += cFrag;
                                entryFrag += '</ul>';
                            }
                        }

                        rFrag += '<li>';
                        rFrag += entryFrag;
                        rFrag += '</li>';
                    }
                    return rFrag;
                }
                var treeFrag = recurse(st);

                if (treeFrag === "") {
                    treeFrag = "Loading...";
                }


                /*
                // sort out all the classes that we're going to be using
                var resultClass = edges.css_classes(namespace, "result", this);
                var valClass = edges.css_classes(namespace, "value", this);
                var filterRemoveClass = edges.css_classes(namespace, "filter-remove", this);
                var facetClass = edges.css_classes(namespace, "facet", this);
                var headerClass = edges.css_classes(namespace, "header", this);
                var selectionsClass = edges.css_classes(namespace, "selections", this);
                var bodyClass = edges.css_classes(namespace, "body", this);
                var countClass = edges.css_classes(namespace, "count", this);
                */

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var frag = '<h3 class="filter__heading" type="button" id="' + toggleId + '">' + this.title + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, treeFrag);

                // now render it into the page
                this.component.context.html(frag);
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
                // var filter_id = this.component.jq(element).attr("id");
                var checked = this.component.jq(element).is(":checked");
                var value = this.component.jq(element).attr("data-value");
                if (checked) {
                    this.component.addFilter({value: value});
                } else {
                    this.component.removeFilter({value: value});
                }
            };

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

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

            ////////////////////////////////////////
            // state variables

            this.focusSearchBox = false;

            this.namespace = "doaj-bs3-search-controller";

            this.draw = function () {
                var comp = this.component;

                var clearClass = edges.css_classes(this.namespace, "reset", this);
                var clearFrag = "";
                if (this.clearButton) {
                    clearFrag = '<button type="button" class="' + clearClass + '" title="Clear all search and sort parameters and start again"> \
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

                    sortOptions = '<div class="input-group ' + sortClasses + '"> \
                                    <button type="button" class="input-group__input ' + directionClass + '" title="" href="#"></button> \
                                    <select class="' + sortFieldClass + ' input-group__input"> \
                                        <option value="_score">Relevance</option>';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        sortOptions += '<option value="' + field + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += ' </select></div>';
                }

                // select box for fields to search on
                var field_select = "";
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    // classes that we'll use
                    var searchFieldClass = edges.css_classes(this.namespace, "field", this);

                    field_select += '<select class="' + searchFieldClass + ' input-group__input">';
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
                    searchFrag = '<button type="button" class="input-group__input ' + searchClass + '"> \
                            ' + text + ' \
                        </button>';
                }

                var searchClasses = edges.css_classes(this.namespace, "searchcombo", this);
                var searchBox = '<div class="input-group ' + searchClasses + '"> \
                                ' + field_select + '\
                                <input type="text" id="' + textId + '" class="' + textClass + ' form-control input-sm" name="q" value="" placeholder="' + this.searchPlaceholder + '"/> \
                                ' + searchFrag + ' \
                    </div>';

                if (clearFrag !== "") {
                    clearFrag = '<div class="col-md-3 col-xs-12">' + clearFrag + "</div>";
                }
                if (sortOptions !== "") {
                    sortOptions = '<div class="col-md-9 col-xs-12">' + sortOptions + "</div>";
                }
                if (searchBox !== "") {
                    searchBox = '<div class="col-xs-12">' + searchBox + "</div>";
                }

                var frag = '<div class="row">' + clearFrag + sortOptions + searchBox + '</div>';

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
        },

        newSearchBoxFacetRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchBoxFacetRenderer, params, edges.newRenderer);
        },
        SearchBoxFacetRenderer: function (params) {

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            this.title = edges.getParam(params.title, "");

            ////////////////////////////////////////
            // state variables

            this.focusSearchBox = false;

            this.namespace = "doaj-bs3-search-box-facet";

            this.draw = function () {
                var comp = this.component;

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);
                var textId = edges.css_id(this.namespace, "text", this);

                //var frag = '<div class="row">' + clearFrag + sortOptions + searchBox + '</div>';
                var frag = '<h3 class="filter__heading">' + edges.escapeHtml(this.title) + '</h3>\
                    <label for="' + textId + '" class="sr-only">' + edges.escapeHtml(this.title) + '</label>\
                    <input type="text" name="' + textId + '" id="' + textId + '" class="filter__search ' + textClass + '" placeholder="' + this.searchPlaceholder + '">';

                comp.context.html(frag);
                feather.replace();

                this.setUISearchText();

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

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

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

            this.hideValues = edges.getParam(params.hideValues, []);

            this.omit = edges.getParam(params.omit, []);

            this.namespace = "doaj-selected-filters";

            this.draw = function () {
                // for convenient short references
                var sf = this.component;
                var ns = this.namespace;

                // sort out the classes we are going to use
                var fieldClass = edges.css_classes(ns, "field", this);
                var fieldNameClass = edges.css_classes(ns, "fieldname", this);
                var valClass = edges.css_classes(ns, "value", this);
                var containerClass = edges.css_classes(ns, "container", this);
                var removeClass = edges.css_classes(ns, "remove", this);

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

                    // render any compound filters
                    if (def.filter === "compound") {
                        filters += '<li class="tag ' + valClass + '">';
                        filters += '<a href="DELETE" class="' + removeClass + '" data-compound="' + field + '" alt="Remove" title="Remove">';
                        filters += def.display;
                        filters += ' <span data-feather="x" aria-hidden="true"></span>';
                        filters += "</a>";
                        filters += "</li>";
                    } else {
                        if ($.inArray(field, this.omit) > -1) {
                            continue;
                        }

                        // then render any filters that have values
                        for (var j = 0; j < def.values.length; j++) {
                            var val = def.values[j];
                            var valDisplay = ": " + val.display;
                            if ($.inArray(field, this.hideValues) > -1) {
                                valDisplay = "";
                            }
                            filters += '<li class="tag ' + valClass + '">';

                            // the remove block looks different, depending on the kind of filter to remove
                            if (def.filter === "term" || def.filter === "terms") {
                                filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" data-value="' + val.val + '" alt="Remove" title="Remove">';
                                filters += def.display + valDisplay;
                                filters += ' <span data-feather="x" aria-hidden="true"></span>';
                                filters += "</a>";
                            } else if (def.filter === "range") {
                                var from = val.from ? ' data-' + val.fromType + '="' + val.from + '" ' : "";
                                var to = val.to ? ' data-' + val.toType + '="' + val.to + '" ' : "";
                                filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" ' + from + to + ' alt="Remove" title="Remove">';
                                filters += def.display + valDisplay;
                                filters += ' <span data-feather="x" aria-hidden="true"></span>';
                                filters += "</a>";
                            }

                            filters += "</li>";
                        }
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

                // if this is a compound filter, remove it by id
                var compound = el.attr("data-compound");
                if (compound) {
                    this.component.removeCompoundFilter({compound_id: compound});
                    return;
                }

                // otherwise follow the usual instructions for removing a filter
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

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-public-search";

            this.draw = function () {
                var frag = "No results found that match your search criteria.  Try removing some of the filters you have set, or modifying the text in the search box.";
                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }
                }

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

                if (el.attr("aria-expanded") === "false") {
                    el.removeClass("collapsed").attr("aria-expanded", "true");
                    at.addClass("in").attr("aria-expanded", "true");
                } else {
                    el.addClass("collapsed").attr("aria-expanded", "false");
                    at.removeClass("in").attr("aria-expanded", "false");
                }
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
                if (issn) {
                    issn = edges.escapeHtml(issn);
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.publisher")) {
                    var name = "";
                    var country = "";
                    if (resultobj.bibjson.publisher.name) {
                        name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.publisher.name) + '</em>';
                    }
                    if (resultobj.bibjson.publisher.country && edges.hasProp(resultobj, "index.country")) {
                        country = 'in <strong>' + edges.escapeHtml(resultobj.index.country) + '</strong>';
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
                        licenses += '<a href="' + license_url + '" target="_blank" rel="noopener">' + edges.escapeHtml(lic.type) + '</a>';
                    }
                }

                var language = "";
                if (resultobj.index.language && resultobj.index.language.length > 0) {
                    language = '<li>\
                              Accepts manuscripts in <strong>' + resultobj.index.language.join(", ") + '</strong>\
                            </li>';
                }

                var actions = "";
                if (this.actions.length > 0) {
                    actions = '<h4 class="label">Actions</h4><ul class="tags">';
                    for (var i = 0; i < this.actions.length; i++) {
                        var act = this.actions[i];
                        var actSettings = act(resultobj);
                        if (actSettings) {
                            actions += '<li class="tag">\
                                <a href="' + actSettings.link + '">' + actSettings.label + '</a>\
                            </li>';
                        }
                    }
                    actions += '</ul>';
                }

                var frag = '<li class="search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          ' + seal + '\
                          <h3 class="search-results__heading">\
                            <a href="/toc/' + issn + '">\
                              ' + edges.escapeHtml(resultobj.bibjson.title) + '\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul>\
                            <li>\
                              ' + published + '\
                            </li>\
                            ' + language + '\
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
                        ' + actions + '\
                      </aside>\
                    </article>\
                  </li>';

                return frag;
            };

            this._renderPublicArticle = function(resultobj) {
                var journal = resultobj.bibjson.journal ? resultobj.bibjson.journal.title : "";

                var date = "";
                if (resultobj.index.date) {
                    date = "(" + doaj.humanYearMonth(resultobj.index.date) + ")";
                }

                var title = "";
                if (resultobj.bibjson.title) {
                    title = edges.escapeHtml(resultobj.bibjson.title);
                }

                // set the authors
                var authors = "";
                if (edges.hasProp(resultobj, "bibjson.author") && resultobj.bibjson.author.length > 0) {
                    authors = '<ul class="article-summary__authors">';
                    var anames = [];
                    var bauthors = resultobj.bibjson.author;
                    for (var i = 0; i < bauthors.length; i++) {
                        var author = bauthors[i];
                        if (author.name) {
                            var field = edges.escapeHtml(author.name);
                            anames.push(field);
                        }
                    }
                    authors += '<li>' + anames.join("</li><li>") + '</li>';
                    authors += '</ul>';
                }

                var keywords = "";
                if (edges.hasProp(resultobj, "bibjson.keywords") && resultobj.bibjson.keywords.length > 0) {
                    keywords = '<h4>Article keywords</h4><ul>';
                    keywords+= '<li>' + resultobj.bibjson.keywords.join(", ") + '</li>';
                    keywords += '</ul>';
                }

                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = '<h4>Journal subjects</h4><ul>';
                    subjects += "<li>" + resultobj.index.classification_paths.join("<br>") + "</li>";
                    subjects += '</ul>';
                }

                var subjects_or_keywords = keywords === "" ? subjects : keywords;

                var abstract = "";
                if (resultobj.bibjson.abstract) {
                    var abstractAction = edges.css_classes(this.namespace, "abstractaction", this);
                    var abstractText = edges.css_classes(this.namespace, "abstracttext", this);

                    abstract = '<h4 class="article-summary__abstract-heading ' + abstractAction + '" type="button" aria-expanded="false" rel="' + resultobj.id + '">\
                            Abstract\
                            <span data-feather="plus" aria-hidden="true"></span>\
                          </h4>\
                          <p rel="' + resultobj.id + '" class="collapse article-summary__abstract-body ' + abstractText + '" aria-expanded="false">\
                            ' + edges.escapeHtml(resultobj.bibjson.abstract) + '\
                          </p>';
                }

                var doi_url = false;
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "doi") {
                            var doi = ids[i].id;
                            var tendot = doi.indexOf("10.");
                            doi_url = "https://doi.org/" + edges.escapeHtml(doi.substring(tendot));
                        }
                    }
                }

                var ftl = false;
                if (edges.hasProp(resultobj, "bibjson.link") && resultobj.bibjson.link.length !== 0) {
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

                var issns = [];
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                            issns.push(edges.escapeHtml(ids[i].id))
                        }
                    }
                }

                var license = "";
                if (edges.hasProp(resultobj, "bibjson.journal.license") && resultobj.bibjson.journal.license.length > 0) {
                    for (var i = 0; i < resultobj.bibjson.journal.license.length; i++) {
                        var lic = resultobj.bibjson.journal.license[i];
                        license += '<a href="' + lic.url + '" target="_blank" rel="noopener">' + lic.type + '</a> ';
                    }
                }

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.journal.publisher")) {
                    var name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.journal.publisher) + '</em>';
                    published = 'Published ' + name;
                }

                var frag = '<li class="search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main article-summary">\
                        <header>\
                          <p class="label">\
                            ' + edges.escapeHtml(journal) + ' ' + date + '\
                          </p>\
                          <h3 class="search-results__heading">\
                            <a href="/article/' + resultobj.id + '" class="">\
                              ' + title + '\
                            </a>\
                          </h3>\
                          ' + authors + '\
                        </header>\
                        <div class="search-results__body">\
                          ' + subjects_or_keywords + '\
                          ' + abstract + '\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <ul>\
                          <li>\
                            <a href="' + ftl + '" target="_blank" rel="noopener">Read online <span data-feather="external-link" aria-hidden="true"></span></a>\
                          </li>\
                          <li>\
                            <a href="/toc/' + issns[0] + '" target="_blank" rel="noopener">Journal Table of Contents</a>\
                          </li>\
                          <li>\
                            ' + license + '\
                          </li>\
                          <li>\
                            ' + published + '\
                          </li>\
                        </ul>\
                      </aside>\
                    </article></li>';

                // close off the result and return
                return frag;
            };
        },

        newPublisherApplicationRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublisherApplicationRenderer, params, edges.newRenderer);
        },
        PublisherApplicationRenderer : function(params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-application";

            this.statusMap = {
                "accepted" : "Accepted to DOAJ",
                "rejected" : "Application rejected",
                "update_request" : "Pending",
                "revisions_required" : "Revisions Required",
                "pending" : "Pending",
                "in progress" : "Under review by an editor",
                "completed" : "Under review by an editor",
                "on hold" : "Under review by an editor",
                "ready" : "Under review by an editor"
            };

            this.draw = function () {
                var frag = "You do not have any applications yet";
                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }

                    var deleteTitleClass = edges.css_classes(this.namespace, "delete-title", this);
                    var deleteLinkClass = edges.css_classes(this.namespace, "delete-link", this);

                    frag += '<section class="modal in" id="modal-delete-application" tabindex="-1" role="dialog" style="display: none;"> \
                        <div class="modal__dialog" role="document">\
                            <h2 class="modal__title">Delete this application</h2>\
                            <p>Are you sure you want to delete your application for <span class="' + deleteTitleClass + '"></span></p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '">Yes, delete it</a> <a class="button button--secondary" data-dismiss="modal" class="modal__close">No</a>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
            };

            this.deleteLinkClicked = function(element) {
                var deleteTitleSelector = edges.css_class_selector(this.namespace, "delete-title", this);
                var deleteLinkSelector = edges.css_class_selector(this.namespace, "delete-link", this);

                var el = $(element);
                var href = el.attr("href");
                var title = el.attr("data-title");

                this.component.jq(deleteTitleSelector).html(title);
                this.component.jq(deleteLinkSelector).attr("href", href);
            };

            this._accessLink = function(resultobj) {
                if (resultobj.es_type === "draft_application") {
                    // if it's a draft, just link to the draft edit page
                    return [doaj.publisherApplicationsSearchConfig.applyUrl + resultobj['id'], "Edit"];
                } else {
                    var status = resultobj.admin.application_status;

                    // if it's an accepted application, link to the ToC
                    if (status === "accepted") {
                        var issn = resultobj.bibjson.issn;
                        if (!issn) {
                            issn = resultobj.bibjson.eissn;
                        }
                        if (issn) {
                            issn = edges.escapeHtml(issn);
                        }
                        return [doaj.publisherApplicationsSearchConfig.tocUrl + issn, "View"];
                        // otherwise just link to the view page
                    } else {
                        return [doaj.publisherApplicationsSearchConfig.journalReadOnlyUrl + resultobj['id'], "View"];
                    }
                }
            };

            this._renderResult = function(resultobj) {

                var accessLink = this._accessLink(resultobj);

                var titleText = "Untitled";
                if (edges.hasProp(resultobj, "bibjson.title")) {
                    titleText = edges.escapeHtml(resultobj.bibjson.title);
                }
                var title = titleText;
                if (accessLink) {
                    title = '<a href="' + accessLink[0] + '">' + title + '</a>';
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var status = "";
                if (edges.hasProp(resultobj, "admin.application_status")) {
                    status = this.statusMap[resultobj.admin.application_status];
                    if (!status) {
                        status = "Status is unspecified";
                    }
                } else {
                    status = "Not yet submitted";
                }

                var completion = "";
                if (resultobj.es_type === "draft_application") {
                    // FIXME: how do we calculate completion
                }

                var last_updated = "Last updated ";
                last_updated += doaj.humanDate(resultobj.last_updated);

                var icon = "edit-3";
                if (accessLink[1] === "View") {
                    icon = "eye";
                }
                var viewOrEdit = '<li class="tag">\
                    <a href="' + accessLink[0] + '">\
                        <span data-feather="' + icon + '" aria-hidden="true"></span>\
                        <span>' + accessLink[1] + '</span>\
                    </a>\
                </li>';

                var deleteLink = "";
                var deleteLinkTemplate = doaj.publisherApplicationsSearchConfig.deleteLinkTemplate;
                var deleteLinkUrl = deleteLinkTemplate.replace("__application_id__", resultobj.id);
                var deleteClass = edges.css_classes(this.namespace, "delete", this);
                if (resultobj.es_type === "draft_application" ||
                        resultobj.admin.application_status === "update_request") {
                    deleteLink = '<li class="tag">\
                        <a href="' + deleteLinkUrl + '"  data-toggle="modal" data-target="#modal-delete-application" class="' + deleteClass + '"\
                            data-title="' + titleText + '">\
                            <span data-feather="trash-2" aria-hidden="true"></span>\
                            <span>Delete</span>\
                        </a>\
                    </li>';
                }

                var frag = '<li class="search-results__record">\
                    <article class="row">\
                      <div class="col-sm-4 search-results__main">\
                        <header>\
                          <h3 class="search-results__heading">\
                            ' + title + '\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <h4 class="label">Status</h4>\
                        <ul>\
                          <li>\
                            <strong>' + status + '</strong>\
                          </li>\
                          ' + completion + '\
                          <li>\
                            ' + last_updated + '\
                          </li>\
                        </ul>\
                      </aside>\
                      <div class="col-sm-4 search-results__aside">\
                        <h4 class="label">Actions</h4>\
                        <ul class="tags">\
                            ' + viewOrEdit + '\
                            ' + deleteLink + '\
                        </ul>\
                      </div>\
                    </article>\
                  </li>';

                return frag;
            };
        }
    },

    fieldRender: {
        titleField : function (val, resultobj, renderer) {
            var field = '<span class="title">';
            if (resultobj.bibjson.title) {
                if (resultobj.es_type === "journal") {
                    var display = edges.escapeHtml(resultobj.bibjson.title);
                    if (resultobj.admin.in_doaj) {
                        display =  "<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + display + "</a>";
                    }
                    field += display;
                } else {
                    field += edges.escapeHtml(resultobj.bibjson.title);
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
            var field = "";
            if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                field += 'Has charges';
            } else if (edges.hasProp(resultobj, "bibjson.other_charges.has_other_charges") && resultobj.bibjson.other_charges.has_other_charges) {
                field += 'Has charges';
            }
            if (field === "") {
                field = 'No charges';
            }

            var urls = [];
            if (edges.hasProp(resultobj, "bibjson.apc.url")) {
                urls.push(resultobj.bibjson.apc.url);
            }
            if (edges.hasProp(resultobj, "bibjson.has_other_charges.url")) {
                urls.push(resultobj.bibjson.has_other_charges.url)
            }

            if (urls.length > 0) {
                field += ' (see ';
                for (var i = 0; i < urls.length; i++) {
                    field += '<a href="' + urls[i] + '">' + urls[i] + '</a>';
                }
                field += ')';
            }

            return field ? field : false;
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
            var titles = [];
            if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
                var lics = resultobj["bibjson"]["journal"]["license"];
                var titles = lics.map(function(x) { return x.type });
            }
            else if (resultobj.bibjson && resultobj.bibjson.license) {
                var lics = resultobj["bibjson"]["license"];
                titles = lics.map(function(x) { return x.type });
            }

            var links = [];
            if (titles.length > 0) {
                for (var i = 0; i < titles.length; i++) {
                    var title = titles[i];
                    if (doaj.licenceMap[title]) {
                        var urls = doaj.licenceMap[title];
                        // i know i know, i'm not using styles.  the attrs still work and are easier.
                        links.push("<a href='" + urls[1] + "' title='" + title + "' target='blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + title + "'></a>");
                    } else {
                        links.push(title);
                    }
                }
                return links.join(" ");
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
            if (resultobj.bibjson && resultobj.bibjson.ref) {
                var urls = [];
                var ls = Object.keys(resultobj.bibjson.ref);
                for (var i = 0; i < ls.length; i++) {
                    if (ls[i] === "journal") {
                        var url = resultobj.bibjson.ref[ls[i]];
                        urls.push("<strong>" + ls[i] + "</strong>: <a href='" + url + "'>" + edges.escapeHtml(url) + "</a>")
                    }
                }
                return urls.join("<br>");
            }
            return false;
        },

        issns : function (val, resultobj, renderer) {
            if (resultobj.bibjson && (resultobj.bibjson.issn || resultobj.bibjson.eissn)) {
                var issn = resultobj.bibjson.issn;
                var eissn = resultobj.bibjson.eissn;
                var issns = [];
                if (issn) {
                    issns.push(edges.escapeHtml(issn));
                }
                if (eissn) {
                    issns.push(edges.escapeHtml(eissn));
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
            if (resultobj && resultobj['admin'] && resultobj['admin']['date_applied']) {
                return doaj.iso_datetime2date_and_time(resultobj['admin']['date_applied']);
            } else {
                return false;
            }
        },

        applicationStatus : function(val, resultobj, renderer) {
            return doaj.valueMaps.applicationStatus[resultobj['admin']['application_status']];
        },

        editSuggestion : function(params) {
            return function (val, resultobj, renderer) {
                if (resultobj.es_type === "application") {
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