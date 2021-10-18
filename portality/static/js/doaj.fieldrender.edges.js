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
        },

        schemaCodeToNameClosure : function(tree) {
            var nameMap = {};
            function recurse(ctx) {
                for (var i = 0; i < ctx.length; i++) {
                    var child = ctx[i];
                    var entry = {};
                    nameMap["LCC:" + child.id] = child.text;
                    if (child.children && child.children.length > 0) {
                        recurse(child.children);
                    }
                }
            }
            recurse(tree);

            return function(code) {
                var name = nameMap[code];
                if (name) {
                    return name;
                }
                return code;
            }
        }
    },

    components : {
        subjectBrowser : function(params) {
            var tree = params.tree;
            var hideEmpty = edges.getParam(params.hideEmpty, false);

            return edges.newTreeBrowser({
                id: "subject",
                category: "facet",
                field: "index.schema_codes_tree.exact",
                tree: function(tree) {
                    function recurse(ctx) {
                        var displayTree = [];
                        for (var i = 0; i < ctx.length; i++) {
                            var child = ctx[i];
                            var entry = {};
                            entry.display = child.text;
                            entry.value = "LCC:" + child.id;
                            if (child.children && child.children.length > 0) {
                                entry.children = recurse(child.children);
                            }
                            displayTree.push(entry);
                        }
                        displayTree.sort((a, b) => a.display > b.display ? 1 : -1);
                        return displayTree;
                    }
                    return recurse(tree);
                }(tree),
                pruneTree: true,
                size: 9999,
                nodeMatch: function(node, match_list) {
                    for (var i = 0; i < match_list.length; i++) {
                        var m = match_list[i];
                        if (node.value === m.key) {
                            return i;
                        }
                    }
                    return -1;
                },
                filterMatch: function(node, selected) {
                    return $.inArray(node.value, selected) > -1;
                },
                nodeIndex : function(node) {
                    return node.display.toLowerCase();
                },
                renderer: doaj.renderers.newSubjectBrowser({
                    title: "Subjects",
                    open: true,
                    hideEmpty: hideEmpty,
                    showCounts: false
                })
            })
        },
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
                    titleBarFrag = '<header class="search__header"> \
                        <p class="label">Search</p>\n \
                        <h1>' + this.title + ' \
                            <span data-feather="help-circle" aria-hidden="true" data-toggle="modal" data-target="#modal-help" type="button"></span><span class="sr-only">Help</span> \
                        </h1> \
                        <div class="row">\
                            <form id="search-input-bar" class="col-md-9" role="search"></form>\
                        </div>\
                    </header>';
                }

                var frag = '<div id="searching-notification"></div>' + titleBarFrag + '\
                    <p id="share_embed"></p>\
                    <h2 id="result-count"></h2>\
                    <div class="row">\
                        <div class="col-md-3">\
                            <aside class="filters">\
                              <h2 class="filters__heading" type="button" data-toggle="collapse" data-target="#filters" aria-expanded="false">\
                                <span data-feather="sliders" aria-hidden="true"></span> Refine search results \
                              </h2>\
                              <ul class="collapse filters__list" id="filters" aria-expanded="false">\
                                  {{FACETS}}\
                              </ul>\
                            </aside>\
                        </div>\
                            \
                        <div class="col-md-9">\
                            <aside id="selected-filters"></aside>\
                            <nav>\
                                <h3 class="sr-only">Display options</h3>\
                                <div class="row">\
                                    <form class="col-sm-6" id="sort_by"></form>\
                                    <form class="col-sm-6 flex-end-col" id="rpp"></form>\
                                </div>\
                            </nav>\
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

        newFQWidget: function (params) {
            return edges.instantiate(doaj.templates.FQWidget, params, edges.newTemplate);
        },
        FQWidget: function (params) {
            this.namespace = "fqwidget";

            this.draw = function (edge) {
                this.edge = edge;

                var frag = `
                    <header>
                        <a href="https://doaj.org/" target="_blank" rel="noopener">
                            <svg height="30px" viewBox="0 0 149 53" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                                <title>DOAJ Logotype</title>
                                <g id="logotype" fill="#282624" fill-rule="nonzero">
                                    <path d="M0,0.4219 L17.9297,0.4219 C24.8672,0.4688 30.0703,3.3516 33.5391,9.0703 C34.7812,10.9922 35.5664,13.0078 35.8945,15.1172 C36.1523,17.2266 36.2812,20.8711 36.2812,26.0508 C36.2812,31.5586 36.082,35.4023 35.6836,37.582 C35.4961,38.6836 35.2148,39.668 34.8398,40.5352 C34.4414,41.3789 33.9609,42.2578 33.3984,43.1719 C31.8984,45.5859 29.8125,47.5781 27.1406,49.1484 C24.4922,50.8359 21.2461,51.6797 17.4023,51.6797 L0,51.6797 L0,0.4219 Z M7.7695,44.332 L17.0508,44.332 C21.4102,44.332 24.5742,42.8438 26.543,39.8672 C27.4102,38.7656 27.9609,37.3711 28.1953,35.6836 C28.4062,34.0195 28.5117,30.9023 28.5117,26.332 C28.5117,21.8789 28.4062,18.6914 28.1953,16.7695 C27.9141,14.8477 27.2461,13.2891 26.1914,12.0938 C24.0352,9.1172 20.9883,7.6758 17.0508,7.7695 L7.7695,7.7695 L7.7695,44.332 Z"></path>
                                    <path d="M39.5938,26.0508 C39.5938,20.0977 39.7695,16.1133 40.1211,14.0977 C40.4961,12.082 41.0703,10.4531 41.8438,9.2109 C43.0859,6.8438 45.0781,4.7344 47.8203,2.8828 C50.5156,1.0078 53.8789,0.0469 57.9102,0 C61.9883,0.0469 65.3867,1.0078 68.1055,2.8828 C70.8008,4.7344 72.7461,6.8438 73.9414,9.2109 C74.809,10.4531 75.406,12.082 75.734,14.0977 C76.039,16.1133 76.191,20.0977 76.191,26.0508 C76.191,31.9102 76.039,35.8711 75.734,37.9336 C75.406,39.9961 74.809,41.6484 73.9414,42.8906 C72.7461,45.2578 70.8008,47.3438 68.1055,49.1484 C65.3867,51.0234 61.9883,52.0078 57.9102,52.1016 C53.8789,52.0078 50.5156,51.0234 47.8203,49.1484 C45.0781,47.3438 43.0859,45.2578 41.8438,42.8906 C41.4688,42.1172 41.1289,41.3789 40.8242,40.6758 C40.543,39.9492 40.3086,39.0352 40.1211,37.9336 C39.7695,35.8711 39.5938,31.9102 39.5938,26.0508 Z M47.3984,26.0508 C47.3984,31.0898 47.5859,34.5 47.9609,36.2812 C48.2891,38.0625 48.957,39.5039 49.9648,40.6055 C50.7852,41.6602 51.8633,42.5156 53.1992,43.1719 C54.5117,43.9453 56.082,44.332 57.9102,44.332 C59.7617,44.332 61.3672,43.9453 62.7266,43.1719 C64.0156,42.5156 65.0469,41.6602 65.8203,40.6055 C66.8281,39.5039 67.5195,38.0625 67.8945,36.2812 C68.2461,34.5 68.4219,31.0898 68.4219,26.0508 C68.4219,21.0117 68.2461,17.5781 67.8945,15.75 C67.5195,14.0156 66.8281,12.5977 65.8203,11.4961 C65.0469,10.4414 64.0156,9.5625 62.7266,8.8594 C61.3672,8.1797 59.7617,7.8164 57.9102,7.7695 C56.082,7.8164 54.5117,8.1797 53.1992,8.8594 C51.8633,9.5625 50.7852,10.4414 49.9648,11.4961 C48.957,12.5977 48.2891,14.0156 47.9609,15.75 C47.5859,17.5781 47.3984,21.0117 47.3984,26.0508 Z"></path>
                                    <path d="M104.008,33.3281 L96.59,10.9336 L96.449,10.9336 L89.031,33.3281 L104.008,33.3281 Z M106.223,40.2188 L86.781,40.2188 L82.844,51.6797 L74.617,51.6797 L93.25,0.4219 L99.754,0.4219 L118.387,51.6797 L110.195,51.6797 L106.223,40.2188 Z"></path>
                                    <path d="M124.82,40.8867 C125.547,41.8477 126.484,42.6328 127.633,43.2422 C128.781,43.9688 130.129,44.332 131.676,44.332 C133.738,44.3789 135.707,43.6641 137.582,42.1875 C138.496,41.4609 139.211,40.5 139.727,39.3047 C140.266,38.1562 140.535,36.7148 140.535,34.9805 L140.535,0.4219 L148.305,0.4219 L148.305,35.7539 C148.211,40.9102 146.523,44.8945 143.242,47.707 C139.984,50.5898 136.199,52.0547 131.887,52.1016 C125.934,51.9609 121.492,49.7344 118.562,45.4219 L124.82,40.8867 Z"></path>
                                </g>
                            </svg>
                        </a>
                        <h2 id="result-count"></h2>\
                        <p class="label label--tertiary">On the Directory of Open Access Journals</p>
                        <p></p>
                    </header>
                    <nav class="search-options">
                        <form class="colsearch-options__left" id="rpp"></form>
                    </nav>
                    <nav class="pagination" id="top-pager"></nav>
                    <ol class="search-results" id="results"></ol>
                    <nav class="pagination" id="bottom-pager"></nav>
                `

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
        newSearchingNotificationRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchingNotificationRenderer, params, edges.newRenderer);
        },
        SearchingNotificationRenderer: function (params) {

            this.scrollTarget = edges.getParam(params.scrollTarget, "body");

            // namespace to use in the page
            this.namespace = "doaj-notification";

            this.searching = false;

            this.draw = function () {
                if (this.component.searching) {
                    let id = edges.css_id(this.namespace, "loading", this);

                    this.component.edge.context.css("opacity", "0.3");
                    var frag = `<div id="` + id + `" class='loading overlay'>
                        <div></div>
                        <div></div>
                        <div></div>
                        <span class='sr-only'>Loading results…</span>
                      </div>`
                    this.component.edge.context.before(frag);
                    let offset = $(this.scrollTarget).offset().top
                    window.scrollTo(0, offset);
                } else {
                    let that = this;
                    let idSelector = edges.css_id_selector(this.namespace, "loading", this);
                    this.component.edge.context.animate(
                        {
                            opacity: "1",
                        },
                        {
                            duration: 1000,
                            always: function() {
                                $(idSelector).remove();
                            }
                        }
                    );
                }
            }
        },

        newSubjectBrowser : function(params) {
            return edges.instantiate(doaj.renderers.SubjectBrowser, params, edges.newRenderer);
        },
        SubjectBrowser : function(params) {
            this.title = edges.getParam(params.title, "");

            this.selectMode = edges.getParam(params.selectMode, "multiple");

            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            this.togglable = edges.getParam(params.togglable, true);

            this.open = edges.getParam(params.open, false);

            this.showCounts = edges.getParam(params.showCounts, false);

            this.namespace = "doaj-subject-browser";

            this.lastScroll = 0;

            this.draw = function() {
                // for convenient short references ...
                var st = this.component.syncTree;
                var namespace = this.namespace;
                // var that = this;

                // var checkboxClass = edges.css_classes(namespace, "selector", this);
                // var countClass = edges.css_classes(namespace, "count", this);

                var treeReport = this._renderTree({tree: st, selectedPathOnly: false, showOneLevel: true});
                var treeFrag = treeReport.frag;

                if (treeFrag === "") {
                    treeFrag = "Loading…";
                }

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);
                var searchId = edges.css_id(namespace, "search", this);
                var filteredId = edges.css_id(namespace, "filtered", this);
                var mainListId = edges.css_id(namespace, "main", this);

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var placeholder = 'Search ' + this.component.nodeCount + ' subjects';
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.title + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <label for="' + searchId + '" class="sr-only">' + placeholder + '</label>\
                        <input type="text" name="' + searchId + '" id="' + searchId + '" class="filter__search" placeholder="' + placeholder + '">\
                        <ul class="filter__choices" id="' + filteredId + '" style="display:none"></ul>\
                        <ul class="filter__choices" id="' + mainListId + '">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, treeFrag);

                // now render it into the page
                this.component.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var mainListSelector = edges.css_id_selector(namespace, "main", this);
                this.component.jq(mainListSelector).scrollTop(this.lastScroll);

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");

                var searchSelector = edges.css_id_selector(namespace, "search", this);
                edges.on(searchSelector, "keyup", this, "filterSubjects");
            };

            this._renderTree = function(params) {
                var st = edges.getParam(params.tree, []);
                var selectedPathOnly = edges.getParam(params.selectedPathOnly, true);
                var showOneLevel = edges.getParam(params.showOneLevel, true);
                var that = this;

                var checkboxClass = edges.css_classes(this.namespace, "selector", this);

                function renderEntry(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return "";
                    }

                    var id = edges.safeId(entry.value);
                    var checked = "";
                    if (entry.selected) {
                        checked = ' checked="checked" ';
                    }

                    var count = "";
                    if (that.showCounts) {
                        var countClass = edges.css_classes(that.namespace, "count", that);
                        count = ' <span class="' + countClass + '">(' + entry.count + '/' + entry.childCount + ')</span>';
                    }

                    var frag = '<input class="' + checkboxClass + '" data-value="' + edges.escapeHtml(entry.value) + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                        <label for="' + id + '" class="filter__label">' + entry.display + count + '</label>';

                    return frag;
                }

                function recurse(tree) {
                    var selected = tree;

                    // first check to see if there are any elements at this level that are selected.  If there are,
                    // that is the only element that we'll render
                    if (selectedPathOnly) {
                        for (var i = 0; i < tree.length; i++) {
                            var entry = tree[i];
                            if (entry.selected) {
                                selected = [entry];
                                break;
                            }
                        }
                    }

                    // now go through either this tree level or just the selected elements, and render the relevant
                    // bits of the sub-tree
                    var anySelected = false;
                    var rFrag = "";
                    for (var i = 0; i < selected.length; i++) {
                        var entry = selected[i];
                        var entryFrag = renderEntry(entry);
                        if (entryFrag === "") {
                            continue;
                        }
                        if (entry.selected) {
                            anySelected = true;
                        }
                        if (entry.children) {
                            var childReport = recurse(entry.children);
                            if (childReport.anySelected) {
                                anySelected = true;
                            }
                            // only attach the children frag if, first any of these are true:
                            // - one of the children is selected
                            // - the entry itself is selected
                            // - we don't want to only show the selected path
                            if (!selectedPathOnly || childReport.anySelected || entry.selected) {
                                // Then, another level (separated out to save my brain from the tortuous logic)
                                // only attach the children frag if, any of these are true:
                                // - the entry or one of its children is selected
                                // - we want to show more than one level at a time
                                if (childReport.anySelected || entry.selected || !showOneLevel) {
                                    var cFrag = childReport.frag;
                                    if (cFrag !== "") {
                                        entryFrag += '<ul class="filter__choices">';
                                        entryFrag += cFrag;
                                        entryFrag += '</ul>';
                                    }
                                }
                            }
                        }

                        rFrag += '<li>';
                        rFrag += entryFrag;
                        rFrag += '</li>';
                    }
                    return {frag : rFrag, anySelected: anySelected};
                }

                return recurse(st);
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function(element) {
                var mainListSelector = edges.css_id_selector(this.namespace, "main", this);
                this.lastScroll = this.component.jq(mainListSelector).scrollTop();
                var el = this.component.jq(element);
                // var filter_id = this.component.jq(element).attr("id");
                var checked = el.is(":checked");
                var value = el.attr("data-value");
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

            this.filterSubjects = function(element) {
                var st = this.component.syncTree;
                var term = $(element).val();
                var that = this;

                var filterSelector = edges.css_id_selector(this.namespace, "filtered", this);
                var mainSelector = edges.css_id_selector(this.namespace, "main", this);
                var filterEl = this.component.jq(filterSelector);
                var mainEl = this.component.jq(mainSelector);

                if (term === "") {
                    filterEl.html("");
                    filterEl.hide();
                    mainEl.show();
                    return;
                }
                if (term.length < 3) {
                    filterEl.html("<li>Enter 3 characters or more to search</li>");
                    filterEl.show();
                    mainEl.hide();
                    return;
                }
                term = term.toLowerCase();

                function entryMatch(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return false;
                    }

                    var matchTerm = entry.index;
                    var includes =  matchTerm.includes(term);
                    if (includes) {
                        var idx = matchTerm.indexOf(term);
                        var display = entry.display;
                        return display.substring(0, idx) + "<strong>" + display.substring(idx, idx + term.length) + "</strong>" + display.substring(idx + term.length);
                    }
                }

                function recurse(tree) {
                    var filteredLayer = [];
                    for (var i = 0; i < tree.length; i++) {
                        var entry = tree[i];
                        var childReport = [];
                        if (entry.children) {
                            childReport = recurse(entry.children);
                        }
                        var selfMatch = entryMatch(entry);
                        if (selfMatch || childReport.length > 0) {
                            var newEntry = $.extend({}, entry);
                            delete newEntry.children;
                            if (selfMatch) {
                                newEntry.display = selfMatch;
                            }
                            if (childReport.length > 0) {
                                newEntry.children = childReport;
                            }
                            filteredLayer.push(newEntry);
                        }
                    }
                    return filteredLayer;
                }

                var filtered = recurse(st);

                if (filtered.length > 0) {
                    var displayReport = this._renderTree({tree: filtered, selectedPathOnly: false, showOneLevel: false});

                    filterEl.html(displayReport.frag);
                    mainEl.hide();
                    filterEl.show();

                    var checkboxSelector = edges.css_class_selector(this.namespace, "selector", this);
                    edges.on(checkboxSelector, "change", this, "filterToggle");
                } else {
                    filterEl.html("<li>No subjects match your search</li>");
                    mainEl.hide();
                    filterEl.show();
                }

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
                    clearFrag = '<button type="button" class="tag tag--secondary ' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                            Clear all \
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
                                <input type="text" id="' + textId + '" class="' + textClass + ' form-control input-sm" name="q" value="" placeholder="' + this.searchPlaceholder + '" style="margin-left: -1px; width: 60%;"/> \
                                ' + searchFrag + ' \
                    </div>';

                if (searchBox !== "") {
                    searchBox = searchBox;
                }
                if (sortOptions !== "") {
                    sortOptions = '<div class="col-xs-6">' + sortOptions + '</div>';
                }
                if (clearFrag !== "") {
                    clearFrag = '<div class="col-xs-6" style="text-align: right;">' + clearFrag + '</div>';
                }

                var frag = searchBox + '<div class="row">' + sortOptions + clearFrag + '</div>';

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
                    el.html('sort ↑ by');
                    el.attr('title', 'Current order ascending. Click to change to descending');
                } else {
                    el.html('sort ↓ by');
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
                var frag = '<h3 class="label label--secondary filter__heading">' + edges.escapeHtml(this.title) + '</h3>\
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
                var sizer = '<label for="' + sizeSelectId + '">' + this.sizeLabel + '</label><select class="' + sizeSelectClass + '" name="' + sizeSelectId + '" id="' + sizeSelectId + '">{{SIZES}}</select>';
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

            // this.shareBoxOpen = false;

            this.showShortened = false;

            this.namespace = "doaj-share-embed";

            this.draw = function () {
                // reset these on each draw
                // this.shareBoxOpen = false;
                this.showShortened = false;

                var comp = this.component;

                var shareButtonFrag = "";
                var shareButtonClass = edges.css_classes(this.namespace, "toggle-share", this);
                var modalId = edges.css_id(this.namespace, "modal", this);
                shareButtonFrag = '<button data-toggle="modal" data-target="#' + modalId + '" class="' + shareButtonClass + ' button button--secondary" role="button">' + this.shareLinkText + '</button>';

                var shorten = "";
                if (this.component.urlShortener) {
                    var shortenClass = edges.css_classes(this.namespace, "shorten", this);
                    shorten = '<p>Share a link to this search</p>'
                }
                var embed = "";
                if (this.component.embedSnippet) {
                    var embedClass = edges.css_classes(this.namespace, "embed", this);
                    embed = '<p>Embed this search in your site</p>\
                    <textarea style="width: 100%; height: 150px" readonly class="' + embedClass + '"></textarea>\
                    <p><button class="button button--secondary" data-dismiss="modal" class="modal__close">Close</button></p>';
                }
                var shareBoxClass = edges.css_classes(this.namespace, "share", this);
                var shareUrlClass = edges.css_classes(this.namespace, "share-url", this);
                var shortenButtonClass = edges.css_classes(this.namespace, "shorten-url", this);
                var shareFrag = '<div class="' + shareBoxClass + '">\
                    ' + shorten + '\
                    <textarea style="width: 100%; height: 150px" readonly class="' + shareUrlClass + '"></textarea>\
                    <p><button class="' + shortenButtonClass + '">shorten url</button></p>\
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
                var shortenSelector = edges.css_class_selector(this.namespace, "shorten-url", this);
                var textarea = this.component.jq(shareUrlSelector);
                var button = this.component.jq(shortenSelector);
                if (this.showShortened) {
                    textarea.val(this.component.edge.fullUrl());
                    button.html('shorten url');
                    this.showShortened = false;
                } else {
                    textarea.val(this.component.shortUrl);
                    button.html('original url');
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
                              <span data-feather="search" aria-hidden="true"></span>\
                              <span class="sr-only"> Search</span></button>';

                // if (clearFrag !== "") {
                //     clearFrag = '<div class="col-md-1 col-xs-12">' + clearFrag + "</div>";
                //}

                var sr1 = '<label for="' + textId + '" class="sr-only">Search by keywords</label>';
                var sr2 = '<label for="' + searchFieldId + '" class="sr-only">In the field</label>';
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
                // find out if there's any search text
                var textIdSelector = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textIdSelector).val();

                if (text === "") {
                    return;
                }

                // if there is search text, then proceed to run the search
                var val = this.component.jq(element).val();
                this.component.setSearchField(val, false);
                this.component.setSearchText(text);
            };

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val, false);

                var searchFieldIdSelector = edges.css_id_selector(this.namespace, "fields", this);
                var field = this.component.jq(searchFieldIdSelector).val();
                this.component.setSearchField(field);
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

                var frag = '<h3 class="label label--secondary filter__heading">' + this.facetTitle + '</h3>\
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

            // don't display the facet at all if there is no data to display
            this.hideIfNoData = edges.getParam(params.hideIfNoData, true);

            // namespace to use in the page
            this.namespace = "doaj-or-term-selector";

            this.draw = function () {
                // for convenient short references ...
                var ts = this.component;
                var namespace = this.namespace;

                if (this.hideIfNoData && ts.edge.result && ts.terms.length === 0) {
                    this.component.context.html("");
                    return;
                }

                // sort out all the classes that we're going to be using
                var countClass = edges.css_classes(namespace, "count", this);
                var checkboxClass = edges.css_classes(namespace, "selector", this);

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results or the page is loading
                var results = "<li class='loading'><div></div><div></div><div></div><span class='sr-only'>Loading choices…</span></li>";
                if (ts.edge.result) {
                    results = "<li>No data to show</li>";
                }

                // if we want the active filters, render them
                var filterFrag = "";
                if (ts.selected.length > 0) {
                    var resultClass = edges.css_classes(namespace, "result", this);
                    for (var i = 0; i < ts.selected.length; i++) {
                        var filt = ts.selected[i];
                        var display = this.component._translate(filt);
                        let id = edges.safeId(filt);
                        filterFrag += '<li>\
                                <input class="' + checkboxClass + '" data-key="' + edges.escapeHtml(filt) + '" id="' + id + '" type="checkbox" name="' + id + '" checked="checked">\
                                <label for="' + id + '" class="filter__label">' + edges.escapeHtml(display) + '</label>\
                            </li>';
                    }
                }

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
                            continue;
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
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
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
                var results = "<li class='loading'><div></div><div></div><div></div><span class='sr-only'>Loading choices…</span></li>";
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
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
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
                var showClear = false;
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
                        showClear = true;
                    } else {
                        if ($.inArray(field, this.omit) > -1) {
                            continue;
                        }
                        showClear = true;

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
                }

                if (showClear) {
                    var clearClass = edges.css_classes(this.namespace, "clear", this);
                    var clearFrag = '<a href="#" class="' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                            CLEAR ALL \
                            <span data-feather="x" aria-hidden="true"></span>\
                        </a>';

                    filters += '<li class="tag tag--secondary ' + valClass + '">' + clearFrag + '</li>';
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

                    // click handler for when the clear button is clicked
                    var clearSelector = edges.css_class_selector(ns, "clear", this);
                    edges.on(clearSelector, "click", this, "clearFilters");
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

            this.clearFilters = function() {
                this.component.clearSearch();
            }
        },

        newPagerRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PagerRenderer, params, edges.newRenderer);
        },
        PagerRenderer: function (params) {

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

            this.goToFirst = function (element) {
                this.component.setFrom(1);
            };

            this.goToPrev = function (element) {
                this.component.decrementPage();
            };

            this.goToNext = function (element) {
                this.component.incrementPage();
            };
        },

        newPublicSearchResultRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublicSearchResultRenderer, params, edges.newRenderer);
        },
        PublicSearchResultRenderer : function(params) {

            this.widget = params.widget;
            if (params.doaj_url) {
                this.doaj_url = params.doaj_url;
            }
            else {
                this.doaj_url = ""
            }

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-public-search";

            this.selector = edges.getParam(params.selector, null)
            this.currentQueryString  = "";


            this.draw = function () {
                if (this.component.edge.currentQuery){
                    let qs = this.component.edge.currentQuery.getQueryString();
                    if (qs) {
                        this.currentQueryString = qs.queryString || "";
                    }
                }
                var frag = "<li class='alert'><p>You searched for <i>'";
                frag += edges.escapeHtml(this.currentQueryString);
                frag +="'</i> and we found no results.</p><p>Search terms must be in <strong>English</strong>.</p> <p>Try removing some of the filters you have set, modifying the text in the search box, or using less specific search terms.</p></li>";;

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
                    seal = '<a href="' + this.doaj_url + '/apply/seal" target="_blank">'
                    if (this.widget){
                        seal += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/check-circle.svg"> DOAJ Seal</a>'
                    }
                    else {
                        seal += '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 499 176" style="height: 1em; width: auto;">\
                                  <path fill="#982E0A" d="M175.542.5c-48.325 0-87.5 39.175-87.5 87.5v87.5c48.325 0 87.5-39.175 87.5-87.5V.5Z"/>\
                                  <path fill="#FD5A3B" d="M.542.5c48.326 0 87.5 39.175 87.5 87.5v87.5c-48.325 0-87.5-39.175-87.5-87.5V.5Z"/>\
                                  <path fill="#282624" d="M235.398 1.246h31.689c12.262.082 21.458 5.178 27.589 15.285 2.195 3.397 3.583 6.96 4.163 10.688.456 3.728.684 10.17.684 19.324 0 9.735-.353 16.528-1.057 20.38-.331 1.948-.828 3.687-1.491 5.22a48.029 48.029 0 0 1-2.548 4.66c-2.651 4.267-6.338 7.788-11.06 10.563-4.681 2.983-10.418 4.474-17.212 4.474h-30.757V1.246Zm13.732 77.608h16.404c7.705 0 13.297-2.63 16.777-7.891 1.532-1.947 2.506-4.412 2.92-7.395.373-2.94.559-8.45.559-16.528 0-7.87-.186-13.504-.559-16.901-.497-3.397-1.677-6.151-3.542-8.264-3.811-5.261-9.196-7.809-16.155-7.643H249.13v64.622Zm56.247-32.311c0-10.522.311-17.564.932-21.126.663-3.563 1.678-6.442 3.045-8.637 2.195-4.184 5.716-7.912 10.563-11.185C324.681 2.281 330.625.583 337.75.5c7.208.083 13.214 1.781 18.02 5.095 4.763 3.273 8.202 7 10.314 11.185 1.533 2.195 2.589 5.074 3.169 8.637.539 3.562.808 10.604.808 21.126 0 10.356-.269 17.357-.808 21.002-.58 3.645-1.636 6.566-3.169 8.761-2.112 4.184-5.551 7.87-10.314 11.06-4.806 3.314-10.812 5.054-18.02 5.22-7.125-.166-13.069-1.906-17.833-5.22-4.847-3.19-8.368-6.876-10.563-11.06a100.47 100.47 0 0 1-1.802-3.914c-.497-1.285-.911-2.9-1.243-4.847-.621-3.645-.932-10.646-.932-21.002Zm13.794 0c0 8.906.332 14.933.995 18.082.579 3.148 1.76 5.695 3.541 7.642 1.45 1.864 3.356 3.376 5.717 4.536 2.32 1.367 5.095 2.05 8.326 2.05 3.273 0 6.11-.683 8.513-2.05 2.278-1.16 4.101-2.672 5.468-4.536 1.781-1.947 3.003-4.494 3.666-7.642.621-3.149.932-9.176.932-18.082s-.311-14.975-.932-18.206c-.663-3.065-1.885-5.572-3.666-7.518-1.367-1.864-3.19-3.418-5.468-4.66-2.403-1.202-5.24-1.844-8.513-1.927-3.231.083-6.006.725-8.326 1.926-2.361 1.243-4.267 2.796-5.717 4.66-1.781 1.947-2.962 4.454-3.541 7.519-.663 3.231-.995 9.3-.995 18.206Zm100.053 12.862-13.11-39.58h-.249l-13.111 39.58h26.47Zm3.915 12.179h-34.361l-6.96 20.256h-14.539l32.932-90.594h11.495l32.932 90.594H430.16l-7.021-20.256Zm32.87 1.18c1.284 1.699 2.941 3.087 4.971 4.163 2.03 1.285 4.412 1.927 7.146 1.927 3.645.083 7.125-1.18 10.439-3.79 1.615-1.285 2.878-2.983 3.79-5.096.953-2.03 1.429-4.577 1.429-7.643V1.245h13.732v62.448c-.166 9.113-3.148 16.155-8.948 21.126-5.758 5.095-12.448 7.684-20.07 7.767-10.521-.249-18.371-4.184-23.549-11.806l11.06-8.016Z"/>\
                                  <path fill="#982E0A" fill-rule="evenodd" d="M266.081 175.5c-25.674 0-30.683-15.655-30.683-23.169h16.907s0 11.272 13.776 11.272c9.393 0 11.897-4.384 11.897-8.141 0-5.866-7.493-7.304-16.099-8.955-11.604-2.227-25.229-4.841-25.229-19.223 0-11.271 10.645-20.664 28.179-20.664 25.047 0 28.804 14.402 28.804 20.664h-16.907s0-8.767-11.897-8.767c-6.888 0-10.646 3.507-10.646 7.515 0 4.559 6.764 5.942 14.818 7.589 11.857 2.424 26.511 5.421 26.511 19.963 0 12.523-10.646 21.916-29.431 21.916Zm68.035 0c-21.917 0-32.562-15.404-32.562-34.44 0-19.036 11.146-34.44 32.562-34.44 21.415 0 31.309 15.404 31.309 34.44 0 1.503-.125 3.757-.125 3.757h-46.087c.751 10.019 5.009 17.533 15.529 17.533 10.645 0 12.524-10.019 12.524-10.019h17.533s-3.757 23.169-30.683 23.169Zm13.275-41.954c-1.127-8.015-4.634-13.776-13.275-13.776-8.642 0-12.9 5.761-14.402 13.776h27.677Zm44.961-5.01c.251-7.013 4.384-10.019 11.898-10.019 6.888 0 10.645 3.006 10.645 8.141 0 6.056-7.139 7.672-15.828 9.639-1.732.392-3.526.798-5.337 1.256-10.77 2.756-20.789 8.266-20.789 20.414 0 12.023 8.766 17.533 20.664 17.533 16.656 0 20.664-14.402 20.664-14.402h.626v12.524h17.533v-44.46c0-16.906-12.524-22.542-28.178-22.542-15.029 0-28.429 5.26-29.431 21.916h17.533Zm22.543 12.274c0 9.643-3.131 23.419-15.028 23.419-5.636 0-9.143-3.131-9.143-8.141 0-5.76 4.759-8.641 10.395-10.019l.674-.168c4.853-1.209 10.35-2.579 13.102-5.091Zm47.739 19.035h31.935v13.777h-49.468v-65.124h17.533v51.347Z" clip-rule="evenodd"/>\
                          </svg>\
                          <p class="sr-only">DOAJ Seal</p>\
                      </a>';
                    }
                }
                var issn = resultobj.bibjson.pissn;
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
                    let length = resultobj.bibjson.apc.max.length;
                    for (var i = 0; i < length; i++) {
                        apcs += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apcs += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apcs += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        if (i < length - 1) {
                            apcs += ', ';
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
                        if (i != (resultobj.bibjson.license.length-1)) {
                            licenses += ', ';
                        }
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

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          <h3 class="search-results__heading">\
                            <a href="' + this.doaj_url + '/toc/' + issn + '" target="_blank">\
                              ' + edges.escapeHtml(resultobj.bibjson.title) + '\
                              <sup>'
                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/link.svg" alt="link icon">'
                }
                else {
                    frag += '<i data-feather="link" aria-hidden="true"></i>'
                }


                frag +='</sup>\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul class="inlined-list">\
                            <li>\
                              ' + published + '\
                            </li>\
                            ' + language + '\
                          </ul>\
                          <ul>\
                            ' + subjects + '\
                          </ul>\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        ' + seal + '\
                        <ul>\
                          <li>\
                            ' + update_or_added + '\
                          </li>\
                          ' + articles + '\
                          <li>\
                            <a href="' + resultobj.bibjson.ref.journal + '" target="_blank" rel="noopener">Website '

                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                }
                else {
                    frag += '<i data-feather="external-link" aria-hidden="true"></i>'
                }



                frag += '</a></li>\
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
                    let humanised = doaj.humanYearMonth(resultobj.index.date);
                    if (humanised) {
                        date = "(" + humanised + ")";
                    }
                }

                var title = "";
                if (resultobj.bibjson.title) {
                    title = edges.escapeHtml(resultobj.bibjson.title);
                }

                // set the authors
                var authors = "";
                if (edges.hasProp(resultobj, "bibjson.author") && resultobj.bibjson.author.length > 0) {
                    authors = '<ul class="inlined-list">';
                    var anames = [];
                    var bauthors = resultobj.bibjson.author;
                    for (var i = 0; i < bauthors.length; i++) {
                        var author = bauthors[i];
                        if (author.name) {
                            var field = edges.escapeHtml(author.name);
                            anames.push(field);
                        }
                    }
                    authors += '<li>' + anames.join(",&nbsp;</li><li>") + '</li>';
                    authors += '</ul>';

                }

                var keywords = "";
                if (edges.hasProp(resultobj, "bibjson.keywords") && resultobj.bibjson.keywords.length > 0) {
                    keywords = '<h4>Article keywords</h4><ul class="inlined-list">';
                    keywords+= '<li>' + resultobj.bibjson.keywords.join(",&nbsp;</li><li>") + '</li>';
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

                    abstract = '<h4 class="' + abstractAction + '" type="button" aria-expanded="false" rel="' + resultobj.id + '">\
                            Abstract'
                    if (this.widget){
                        abstract += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/plus.svg" alt="external-link icon">'
                    }
                    else {
                        abstract += '<i data-feather="plus" aria-hidden="true"></i>'
                    }
                    abstract += '</h4>\
                          <p rel="' + resultobj.id + '" class="collapse ' + abstractText + '" aria-expanded="false">\
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
                // We have stopped syncing journal license to articles: https://github.com/DOAJ/doajPM/issues/2548
                /*
                var license = "";
                if (edges.hasProp(resultobj, "bibjson.journal.license") && resultobj.bibjson.journal.license.length > 0) {
                    for (var i = 0; i < resultobj.bibjson.journal.license.length; i++) {
                        var lic = resultobj.bibjson.journal.license[i];
                        license += '<a href="' + lic.url + '" target="_blank" rel="noopener">' + lic.type + '</a> ';
                    }
                }
                */

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.journal.publisher")) {
                    var name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.journal.publisher) + '</em>';
                    published = 'Published ' + name;
                }

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          <p class="label"><a href="' + this.doaj_url + '/toc/' + issns[0] + '" target="_blank">\
                            ' + edges.escapeHtml(journal) + ' ' + date + '\
                          </a></p>\
                          <h3 class="search-results__heading">\
                            <a href="' + this.doaj_url + '/article/' + resultobj.id + '" class="" target="_blank">\
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
                            <a href="' + ftl + '" target="_blank" rel="noopener"> Read online '
                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                }
                else {
                    frag += '<i data-feather="external-link" aria-hidden="true"></i>'
                }
                frag += '</a></li>\
                          <li>\
                            <a href="' + this.doaj_url + '/toc/' + issns[0] + '" target="_blank" rel="noopener">About the journal</a>\
                          </li>\
                          <li>\
                            ' + published + '\
                          </li>\
                        </ul>\
                      </aside>\
                    </article></li>';
                        /*
                         <li>\
                            ' + license + '\
                         </li>\
                         */
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
                "draft" : "Not yet submitted",
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
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--secondary" data-dismiss="modal" class="modal__close">No</button>\
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
                        var issn = resultobj.bibjson.pissn;
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

                var frag = '<li class="card search-results__record">\
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
        },

        newPublisherUpdateRequestRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublisherUpdateRequestRenderer, params, edges.newRenderer);
        },
        PublisherUpdateRequestRenderer : function(params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-update-request";

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
                var frag = "You do not have any update requests yet";
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

                    frag += '<section class="modal in" id="modal-delete-update-request" tabindex="-1" role="dialog" style="display: none;"> \
                        <div class="modal__dialog" role="document">\
                            <h2 class="modal__title">Delete this update request</h2>\
                            <p>Are you sure you want to delete your update request for <span class="' + deleteTitleClass + '"></span></p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--secondary" data-dismiss="modal" class="modal__close">No</button>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
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

                /*
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
                 */

                var deleteLink = "";
                var deleteLinkTemplate = doaj.publisherUpdatesSearchConfig.deleteLinkTemplate;
                var deleteLinkUrl = deleteLinkTemplate.replace("__application_id__", resultobj.id);
                var deleteClass = edges.css_classes(this.namespace, "delete", this);
                if (resultobj.es_type === "draft_application" ||
                    resultobj.admin.application_status === "update_request") {
                    deleteLink = '<li class="tag">\
                        <a href="' + deleteLinkUrl + '"  data-toggle="modal" data-target="#modal-delete-update-request" class="' + deleteClass + '"\
                            data-title="' + titleText + '">\
                            <span data-feather="trash-2" aria-hidden="true"></span>\
                            <span>Delete</span>\
                        </a>\
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
                    actions += deleteLink;
                    actions += '</ul>';
                }



                var frag = '<li class="card search-results__record">\
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
                        ' + actions + '\
                      </div>\
                    </article>\
                  </li>';

                return frag;
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
                var status = resultobj.admin.application_status;

                // if it's an accepted application, link to the ToC
                if (status === "accepted") {
                    var issn = resultobj.bibjson.pissn;
                    if (!issn) {
                        issn = resultobj.bibjson.eissn;
                    }
                    if (issn) {
                        issn = edges.escapeHtml(issn);
                    }
                    return [doaj.publisherUpdatesSearchConfig.tocUrl + issn, "View"];
                    // otherwise just link to the view page
                } else {
                    return [doaj.publisherUpdatesSearchConfig.journalReadOnlyUrl + resultobj['id'], "View"];
                }
            };

            this._renderPublicJournal = function(resultobj) {
                var seal = "";
                if (edges.objVal("admin.seal", resultobj, false)) {
                    seal = '<a href="/apply/seal" target="_blank">\
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 499 176" style="height: 1em; width: auto;"><path fill="#982E0A" d="M175.542.5c-48.325 0-87.5 39.175-87.5 87.5v87.5c48.325 0 87.5-39.175 87.5-87.5V.5Z"/> <path fill="#FD5A3B" d="M.542.5c48.326 0 87.5 39.175 87.5 87.5v87.5c-48.325 0-87.5-39.175-87.5-87.5V.5Z"/> <path fill="#282624" d="M235.398 1.246h31.689c12.262.082 21.458 5.178 27.589 15.285 2.195 3.397 3.583 6.96 4.163 10.688.456 3.728.684 10.17.684 19.324 0 9.735-.353 16.528-1.057 20.38-.331 1.948-.828 3.687-1.491 5.22a48.029 48.029 0 0 1-2.548 4.66c-2.651 4.267-6.338 7.788-11.06 10.563-4.681 2.983-10.418 4.474-17.212 4.474h-30.757V1.246Zm13.732 77.608h16.404c7.705 0 13.297-2.63 16.777-7.891 1.532-1.947 2.506-4.412 2.92-7.395.373-2.94.559-8.45.559-16.528 0-7.87-.186-13.504-.559-16.901-.497-3.397-1.677-6.151-3.542-8.264-3.811-5.261-9.196-7.809-16.155-7.643H249.13v64.622Zm56.247-32.311c0-10.522.311-17.564.932-21.126.663-3.563 1.678-6.442 3.045-8.637 2.195-4.184 5.716-7.912 10.563-11.185C324.681 2.281 330.625.583 337.75.5c7.208.083 13.214 1.781 18.02 5.095 4.763 3.273 8.202 7 10.314 11.185 1.533 2.195 2.589 5.074 3.169 8.637.539 3.562.808 10.604.808 21.126 0 10.356-.269 17.357-.808 21.002-.58 3.645-1.636 6.566-3.169 8.761-2.112 4.184-5.551 7.87-10.314 11.06-4.806 3.314-10.812 5.054-18.02 5.22-7.125-.166-13.069-1.906-17.833-5.22-4.847-3.19-8.368-6.876-10.563-11.06a100.47 100.47 0 0 1-1.802-3.914c-.497-1.285-.911-2.9-1.243-4.847-.621-3.645-.932-10.646-.932-21.002Zm13.794 0c0 8.906.332 14.933.995 18.082.579 3.148 1.76 5.695 3.541 7.642 1.45 1.864 3.356 3.376 5.717 4.536 2.32 1.367 5.095 2.05 8.326 2.05 3.273 0 6.11-.683 8.513-2.05 2.278-1.16 4.101-2.672 5.468-4.536 1.781-1.947 3.003-4.494 3.666-7.642.621-3.149.932-9.176.932-18.082s-.311-14.975-.932-18.206c-.663-3.065-1.885-5.572-3.666-7.518-1.367-1.864-3.19-3.418-5.468-4.66-2.403-1.202-5.24-1.844-8.513-1.927-3.231.083-6.006.725-8.326 1.926-2.361 1.243-4.267 2.796-5.717 4.66-1.781 1.947-2.962 4.454-3.541 7.519-.663 3.231-.995 9.3-.995 18.206Zm100.053 12.862-13.11-39.58h-.249l-13.111 39.58h26.47Zm3.915 12.179h-34.361l-6.96 20.256h-14.539l32.932-90.594h11.495l32.932 90.594H430.16l-7.021-20.256Zm32.87 1.18c1.284 1.699 2.941 3.087 4.971 4.163 2.03 1.285 4.412 1.927 7.146 1.927 3.645.083 7.125-1.18 10.439-3.79 1.615-1.285 2.878-2.983 3.79-5.096.953-2.03 1.429-4.577 1.429-7.643V1.245h13.732v62.448c-.166 9.113-3.148 16.155-8.948 21.126-5.758 5.095-12.448 7.684-20.07 7.767-10.521-.249-18.371-4.184-23.549-11.806l11.06-8.016Z"/> <path fill="#982E0A" fill-rule="evenodd" d="M266.081 175.5c-25.674 0-30.683-15.655-30.683-23.169h16.907s0 11.272 13.776 11.272c9.393 0 11.897-4.384 11.897-8.141 0-5.866-7.493-7.304-16.099-8.955-11.604-2.227-25.229-4.841-25.229-19.223 0-11.271 10.645-20.664 28.179-20.664 25.047 0 28.804 14.402 28.804 20.664h-16.907s0-8.767-11.897-8.767c-6.888 0-10.646 3.507-10.646 7.515 0 4.559 6.764 5.942 14.818 7.589 11.857 2.424 26.511 5.421 26.511 19.963 0 12.523-10.646 21.916-29.431 21.916Zm68.035 0c-21.917 0-32.562-15.404-32.562-34.44 0-19.036 11.146-34.44 32.562-34.44 21.415 0 31.309 15.404 31.309 34.44 0 1.503-.125 3.757-.125 3.757h-46.087c.751 10.019 5.009 17.533 15.529 17.533 10.645 0 12.524-10.019 12.524-10.019h17.533s-3.757 23.169-30.683 23.169Zm13.275-41.954c-1.127-8.015-4.634-13.776-13.275-13.776-8.642 0-12.9 5.761-14.402 13.776h27.677Zm44.961-5.01c.251-7.013 4.384-10.019 11.898-10.019 6.888 0 10.645 3.006 10.645 8.141 0 6.056-7.139 7.672-15.828 9.639-1.732.392-3.526.798-5.337 1.256-10.77 2.756-20.789 8.266-20.789 20.414 0 12.023 8.766 17.533 20.664 17.533 16.656 0 20.664-14.402 20.664-14.402h.626v12.524h17.533v-44.46c0-16.906-12.524-22.542-28.178-22.542-15.029 0-28.429 5.26-29.431 21.916h17.533Zm22.543 12.274c0 9.643-3.131 23.419-15.028 23.419-5.636 0-9.143-3.131-9.143-8.141 0-5.76 4.759-8.641 10.395-10.019l.674-.168c4.853-1.209 10.35-2.579 13.102-5.091Zm47.739 19.035h31.935v13.777h-49.468v-65.124h17.533v51.347Z" clip-rule="evenodd"/></svg>\
                              <span class="sr-only">DOAJ Seal</span>\
                          </a>';
                }
                var issn = resultobj.bibjson.pissn;
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
                    let length = resultobj.bibjson.apc.max.length;
                    for (var i = 0; i < length; i++) {
                        apcs += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apcs += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apcs += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        if (i < length - 1) {
                            apcs += ', ';
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

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          <h3 class="search-results__heading">\
                            <a href="/toc/' + issn + '">\
                              ' + edges.escapeHtml(resultobj.bibjson.title) + '\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul class="inlined-list">\
                            <li>\
                              ' + published + '\
                            </li>\
                            ' + language + '\
                          </ul>\
                          <ul>\
                            ' + subjects + '\
                          </ul>\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        ' + seal + '\
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
        },
        newSortRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SortRenderer, params, edges.newRenderer);
        },
        SortRenderer: function (params) {

            this.prefix = edges.getParam(params.prefix, "");

            // should the direction switcher be rendered?  If not, then it's wise to set "dir" on the components
            // sortOptions, so that the correct dir is used
            this.dirSwitcher = edges.getParam(params.dirSwitcher, true);

            this.namespace = "doaj-sort-renderer";

            this.draw = function () {
                var comp = this.component;

                // if sort options are provided render the orderer and the order by
                var sortOptions = "";
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    // classes that we'll use
                    var directionClass = edges.css_classes(this.namespace, "direction", this);
                    var sortFieldClass = edges.css_classes(this.namespace, "sortby", this);
                    var prefixClass = edges.css_classes(this.namespace, "prefix", this);

                    var selectName = edges.css_id(this.namespace, "select", this);

                    var label = '<label class="' + prefixClass + '" for="' + selectName + '">' + this.prefix + '</label>';

                    var direction = "";
                    if (this.dirSwitcher) {
                        direction = '<span class="input-group-btn"> \
                            <button type="button" class="btn btn-default btn-sm ' + directionClass + '" title="" href="#"></button> \
                        </span>';
                    }

                    sortOptions = label + '\
                        ' + direction + ' \
                        <select name="' + selectName + '" class="form-control input-sm ' + sortFieldClass + '" id="' + selectName + '"> \
                            <option value="_score">Relevance</option>';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        var dir = comp.sortOptions[i].dir;
                        if (dir === undefined) {
                            dir = "";
                        }
                        dir = " " + dir;
                        sortOptions += '<option value="' + field + '' + dir + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += ' </select>';
                }

                // assemble the final fragment and render it into the component's context
                var frag = '{{SORT}}';
                frag = frag.replace(/{{SORT}}/g, sortOptions);

                comp.context.html(frag);

                // now populate all the dynamic bits
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    if (this.dirSwitcher) {
                        this.setUISortDir();
                    }
                    this.setUISortField();
                }

                // attach all the bindings
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                    var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                    edges.on(directionSelector, "click", this, "changeSortDir");
                    edges.on(sortSelector, "change", this, "changeSortBy");
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

                // find out the available value options
                var options = el.find("option");
                var vals = [];
                for (var i = 0; i < options.length; i++) {
                    vals.push($(options[i]).attr("value"));
                }

                // sort out the value we want to set
                var fieldVal = this.component.sortBy;
                var fullVal = this.component.sortBy + " " + this.component.sortDir;

                // choose the first value which matches an actual option
                var setVal = false;
                if ($.inArray(fieldVal, vals) > -1) {
                    setVal = fieldVal;
                } else if ($.inArray(fullVal, vals) > -1) {
                    setVal = fullVal;
                }

                if (setVal !== false) {
                    el.val(setVal);
                }
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSortDir = function (element) {
                this.component.changeSortDir();
            };

            this.changeSortBy = function (element) {
                var val = this.component.jq(element).val();
                var bits = val.split(" ");
                var field = bits[0];
                var dir = false;
                if (bits.length === 2) {
                    dir = bits[1];
                }
                this.component.setSort({field: field, dir: dir});
            };
        }
    },

    fieldRender: {
        titleField : function (val, resultobj, renderer) {
            var field = '<h3>';
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
                if (resultobj.admin && resultobj.admin.seal) {
                    field += '<a href="/apply/seal" target="_blank">\
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 499 176" style="height: 1em; width: auto;">\
                              <path fill="#982E0A" d="M175.542.5c-48.325 0-87.5 39.175-87.5 87.5v87.5c48.325 0 87.5-39.175 87.5-87.5V.5Z"/>\
                              <path fill="#FD5A3B" d="M.542.5c48.326 0 87.5 39.175 87.5 87.5v87.5c-48.325 0-87.5-39.175-87.5-87.5V.5Z"/>\
                              <path fill="#282624" d="M235.398 1.246h31.689c12.262.082 21.458 5.178 27.589 15.285 2.195 3.397 3.583 6.96 4.163 10.688.456 3.728.684 10.17.684 19.324 0 9.735-.353 16.528-1.057 20.38-.331 1.948-.828 3.687-1.491 5.22a48.029 48.029 0 0 1-2.548 4.66c-2.651 4.267-6.338 7.788-11.06 10.563-4.681 2.983-10.418 4.474-17.212 4.474h-30.757V1.246Zm13.732 77.608h16.404c7.705 0 13.297-2.63 16.777-7.891 1.532-1.947 2.506-4.412 2.92-7.395.373-2.94.559-8.45.559-16.528 0-7.87-.186-13.504-.559-16.901-.497-3.397-1.677-6.151-3.542-8.264-3.811-5.261-9.196-7.809-16.155-7.643H249.13v64.622Zm56.247-32.311c0-10.522.311-17.564.932-21.126.663-3.563 1.678-6.442 3.045-8.637 2.195-4.184 5.716-7.912 10.563-11.185C324.681 2.281 330.625.583 337.75.5c7.208.083 13.214 1.781 18.02 5.095 4.763 3.273 8.202 7 10.314 11.185 1.533 2.195 2.589 5.074 3.169 8.637.539 3.562.808 10.604.808 21.126 0 10.356-.269 17.357-.808 21.002-.58 3.645-1.636 6.566-3.169 8.761-2.112 4.184-5.551 7.87-10.314 11.06-4.806 3.314-10.812 5.054-18.02 5.22-7.125-.166-13.069-1.906-17.833-5.22-4.847-3.19-8.368-6.876-10.563-11.06a100.47 100.47 0 0 1-1.802-3.914c-.497-1.285-.911-2.9-1.243-4.847-.621-3.645-.932-10.646-.932-21.002Zm13.794 0c0 8.906.332 14.933.995 18.082.579 3.148 1.76 5.695 3.541 7.642 1.45 1.864 3.356 3.376 5.717 4.536 2.32 1.367 5.095 2.05 8.326 2.05 3.273 0 6.11-.683 8.513-2.05 2.278-1.16 4.101-2.672 5.468-4.536 1.781-1.947 3.003-4.494 3.666-7.642.621-3.149.932-9.176.932-18.082s-.311-14.975-.932-18.206c-.663-3.065-1.885-5.572-3.666-7.518-1.367-1.864-3.19-3.418-5.468-4.66-2.403-1.202-5.24-1.844-8.513-1.927-3.231.083-6.006.725-8.326 1.926-2.361 1.243-4.267 2.796-5.717 4.66-1.781 1.947-2.962 4.454-3.541 7.519-.663 3.231-.995 9.3-.995 18.206Zm100.053 12.862-13.11-39.58h-.249l-13.111 39.58h26.47Zm3.915 12.179h-34.361l-6.96 20.256h-14.539l32.932-90.594h11.495l32.932 90.594H430.16l-7.021-20.256Zm32.87 1.18c1.284 1.699 2.941 3.087 4.971 4.163 2.03 1.285 4.412 1.927 7.146 1.927 3.645.083 7.125-1.18 10.439-3.79 1.615-1.285 2.878-2.983 3.79-5.096.953-2.03 1.429-4.577 1.429-7.643V1.245h13.732v62.448c-.166 9.113-3.148 16.155-8.948 21.126-5.758 5.095-12.448 7.684-20.07 7.767-10.521-.249-18.371-4.184-23.549-11.806l11.06-8.016Z"/>\
                              <path fill="#982E0A" fill-rule="evenodd" d="M266.081 175.5c-25.674 0-30.683-15.655-30.683-23.169h16.907s0 11.272 13.776 11.272c9.393 0 11.897-4.384 11.897-8.141 0-5.866-7.493-7.304-16.099-8.955-11.604-2.227-25.229-4.841-25.229-19.223 0-11.271 10.645-20.664 28.179-20.664 25.047 0 28.804 14.402 28.804 20.664h-16.907s0-8.767-11.897-8.767c-6.888 0-10.646 3.507-10.646 7.515 0 4.559 6.764 5.942 14.818 7.589 11.857 2.424 26.511 5.421 26.511 19.963 0 12.523-10.646 21.916-29.431 21.916Zm68.035 0c-21.917 0-32.562-15.404-32.562-34.44 0-19.036 11.146-34.44 32.562-34.44 21.415 0 31.309 15.404 31.309 34.44 0 1.503-.125 3.757-.125 3.757h-46.087c.751 10.019 5.009 17.533 15.529 17.533 10.645 0 12.524-10.019 12.524-10.019h17.533s-3.757 23.169-30.683 23.169Zm13.275-41.954c-1.127-8.015-4.634-13.776-13.275-13.776-8.642 0-12.9 5.761-14.402 13.776h27.677Zm44.961-5.01c.251-7.013 4.384-10.019 11.898-10.019 6.888 0 10.645 3.006 10.645 8.141 0 6.056-7.139 7.672-15.828 9.639-1.732.392-3.526.798-5.337 1.256-10.77 2.756-20.789 8.266-20.789 20.414 0 12.023 8.766 17.533 20.664 17.533 16.656 0 20.664-14.402 20.664-14.402h.626v12.524h17.533v-44.46c0-16.906-12.524-22.542-28.178-22.542-15.029 0-28.429 5.26-29.431 21.916h17.533Zm22.543 12.274c0 9.643-3.131 23.419-15.028 23.419-5.636 0-9.143-3.131-9.143-8.141 0-5.76 4.759-8.641 10.395-10.019l.674-.168c4.853-1.209 10.35-2.579 13.102-5.091Zm47.739 19.035h31.935v13.777h-49.468v-65.124h17.533v51.347Z" clip-rule="evenodd"/>\
                              </svg>\
                            <span class="sr-only">DOAJ Seal</span>\
                          </a>';
                }
                return field + "</h3>"
            } else {
                return false;
            }
        },

        authorPays : function(val, resultobj, renderer) {
            if (resultobj.es_type === "journal") {
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
            }
            else {
                return false;
            }
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
                        urls.push("<strong>Home page</strong>: <a href='" + url + "'>" + edges.escapeHtml(url) + "</a>")
                    }
                }
                return urls.join("<br>");
            }
            if (resultobj.bibjson && resultobj.bibjson.link) {
                var ls = resultobj.bibjson.link;
                for (var i = 0; i < ls.length; i++) {
                    var t = ls[i].type;
                    var label = '';
                    if (t === 'fulltext') {
                        label = 'Full text'
                    } else {
                        label = t.substring(0, 1).toUpperCase() + t.substring(1)
                    }
                    return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + edges.escapeHtml(ls[i].url) + "</a>"
                }
            }
            return false;
        },

        issns : function (val, resultobj, renderer) {
            if (resultobj.bibjson && (resultobj.bibjson.pissn || resultobj.bibjson.eissn)) {
                var issn = resultobj.bibjson.pissn;
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

                    var result = '<p><a class="edit_suggestion_link button" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>' + linkName + '</a></p>';
                    return result;
                }
                return false;
            }
        },

        readOnlyJournal : function(params) {
            return function (val, resultobj, renderer) {
                if (resultobj.admin && resultobj.admin.current_journal) {
                    var result = '<br/><p><a class="readonly_journal_link button" href="';
                    result += params.readOnlyJournalUrl;
                    result += resultobj.admin.current_journal;
                    result += '" target="_blank"';
                    result += '>View journal being updated</a></p>';
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
                    var result = '<p><a class="edit_journal_link button button--secondary" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>Edit this journal</a></p>';
                    return result;
                }
                return false;
            }
        },
    }

});
