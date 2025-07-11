$.extend(true, doaj, {
    filters: {
        noCharges: function () {
            return {
                id: "no_charges",
                display: "Without fees",
                must: [
                    es.newTermFilter({
                        field: "bibjson.apc.has_apc",
                        value: false
                    }),
                    es.newTermFilter({
                        field: "bibjson.other_charges.has_other_charges",
                        value: false
                    })
                ]
            }
        }
    },
    facets: {
        inDOAJ: function () {
            return edges.newRefiningANDTermSelector({
                id: "in_doaj",
                category: "facet",
                field: "admin.in_doaj",
                display: "In DOAJ?",
                deactivateThreshold: 1,
                valueMap: {
                    1: "Yes",
                    0: "No",
                    true: "Yes",
                    false: "No"
                },
                parseSelectedValueString: function (val) {
                    // this is needed because ES7 doesn't understand "1" or `1` to be `true`, so
                    // we convert the string value of the aggregation back to a boolean
                    return val === "1"
                },
                filterToAggValue: function (val) {
                    return val === true ? 1 : 0;
                },
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },

        openOrClosed: function () {
            return edges.newRefiningANDTermSelector({
                id: "application_type",
                category: "facet",
                field: "index.application_type.exact",
                display: "Open or closed?",
                deactivateThreshold: 1,
                orderDir: "asc",
                valueMap: {
                    "finished application/update": "Closed",
                    "update request": "Open",
                    "new application": "Open"
                },
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },

        applicationStatus: function () {
            return edges.newRefiningANDTermSelector({
                id: "application_status",
                category: "facet",
                field: "admin.application_status.exact",
                display: "Status",
                deactivateThreshold: 1,
                valueFunction: doaj.valueMaps.adminStatusMap,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        hasEditorGroup: function () {
            return edges.newRefiningANDTermSelector({
                id: "has_editor_group",
                category: "facet",
                field: "index.has_editor_group.exact",
                display: "Has editor group?",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        hasEditor: function () {
            return edges.newRefiningANDTermSelector({
                id: "has_editor",
                category: "facet",
                field: "index.has_editor.exact",
                display: "Has Associate Editor?",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        editorGroup: function () {
            return edges.newRefiningANDTermSelector({
                id: "editor_group",
                category: "facet",
                field: "admin.editor_group.exact",
                display: "Editor group",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        editor: function () {
            return edges.newRefiningANDTermSelector({
                id: "editor",
                category: "facet",
                field: "admin.editor.exact",
                display: "Editor",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        hasAPC: function () {
            return edges.newRefiningANDTermSelector({
                id: "author_pays",
                category: "facet",
                field: "index.has_apc.exact",
                display: "Has APC?",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        adminHasAPC: function() {
            return doaj.facets.booleanFacet({
                id: "admin_has_apc",
                field: "bibjson.apc.has_apc",
                display: "Has APC?",
            })
        },
        adminHasOtherCharges: function() {
            return doaj.facets.booleanFacet({
                id: "admin_has_other_charges",
                field: "bibjson.other_charges.has_other_charges",
                display: "Has Other Charges?",
            })
        },
        booleanFacet : function(params) {
            return edges.newRefiningANDTermSelector({
                id: params.id,
                category: "facet",
                field: params.field,
                display: params.display,
                deactivateThreshold: 1,
                valueMap: {
                    0: "No",
                    1: "Yes"
                },
                parseSelectedValueString: function(value) {
                    return value === "1"
                },
                filterToAggValue: function(value) {
                    if (value) {
                        return 1
                    } else {
                        return 0
                    }
                },
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        classification: function () {
            return edges.newRefiningANDTermSelector({
                id: "classification",
                category: "facet",
                field: "index.classification.exact",
                display: "Classification",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        language: function () {
            return edges.newRefiningANDTermSelector({
                id: "language",
                category: "facet",
                field: "index.language.exact",
                display: "Journal language",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        countryPublisher: function () {
            return edges.newRefiningANDTermSelector({
                id: "country_publisher",
                category: "facet",
                field: "index.country.exact",
                display: "Country of publisher",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        subject: function () {
            return edges.newRefiningANDTermSelector({
                id: "subject",
                category: "facet",
                field: "index.subject.exact",
                display: "Subject",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        publisher: function () {
            return edges.newRefiningANDTermSelector({
                id: "publisher",
                category: "facet",
                field: "bibjson.publisher.name.exact",
                display: "Publisher",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        },
        journalLicence: function () {
            return edges.newRefiningANDTermSelector({
                id: "journal_license",
                category: "facet",
                field: "index.license.exact",
                display: "Journal license",
                deactivateThreshold: 1,
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        }
    },

    valueMaps: {
        // This must be updated in line with the list in formcontext/choices.py
        applicationStatus: {
            'update_request': 'Update Request',
            'revisions_required': 'Revisions Required',
            'pending': 'Pending',
            'in progress': 'In Progress',
            'completed': 'Completed',
            'on hold': 'On Hold',
            'ready': 'Ready',
            'rejected': 'Rejected',
            'accepted': 'Accepted',
            'post_submission_review': "Autochecking",
        },

        adminStatusMap: function (value) {
            if (doaj.valueMaps.applicationStatus.hasOwnProperty(value)) {
                return doaj.valueMaps.applicationStatus[value];
            }
            return value;
        },

        displayYearPeriod: function (params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var frdisplay = (new Date(parseInt(from))).getUTCFullYear();
            let todisplay = (new Date(parseInt(to - 1))).getUTCFullYear();

            let display = frdisplay;
            if (frdisplay !== todisplay) {
                display = frdisplay + " to " + todisplay;
            }
            return {to: to, toType: "lt", from: from, fromType: "gte", display: display}
        },

        displayYearMonthPeriod: function (params) {
            var from = params.from;
            var to = params.to;

            let frdisplay = false;
            if (from) {
                frdisplay = new Date(parseInt(from)).toLocaleString('default', { month: 'long', year: 'numeric', timeZone: "UTC" });
            }

            let todisplay = false;
            if (to) {
                todisplay = new Date(parseInt(to - 1)).toLocaleString('default', { month: 'long', year: 'numeric', timeZone: "UTC" });
            }

            let range = frdisplay;
            if (to) {
                if (todisplay !== frdisplay) {
                    range += ` to ${todisplay}`;
                }
            } else {
                range += "+";
            }

            return {to: to, toType: "lt", from: from, fromType: "gte", display: range}
        },

        schemaCodeToNameClosure: function (tree) {
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

            return function (code) {
                var name = nameMap[code];
                if (name) {
                    return name;
                }
                return code;
            }
        },

        countFormat: edges.numFormat({
            thousandsSeparator: ","
        }),

        monthPadding: edges.numFormat({
            zeroPadding: 2
        }),

        refiningANDTermSelectorExporter: function(component) {
            return component.values;
        },

        dateHistogramSelectorExporter: function(component) {
            return component.values;
        }
    },
    components: {
        pager: function (id, category) {
            return edges.newPager({
                id: id,
                category: category,
                renderer: edges.bs3.newPagerRenderer({
                    sizeOptions: [10, 25, 50, 100],
                    numberFormat: doaj.valueMaps.countFormat,
                    scroll: false
                })
            })
        },

        searchingNotification: function () {
            return edges.newSearchingNotification({
                id: "searching-notification",
                category: "searching-notification",
                finishedEvent: "edges:post-render",
                renderer: doaj.renderers.newSearchingNotificationRenderer({
                    scrollOnSearch: true
                })
            })
        },

        subjectBrowser: function (params) {
            var tree = params.tree;
            var hideEmpty = edges.getParam(params.hideEmpty, false);
            var id = edges.getParam(params.id, "subject");
            var category = edges.getParam(params.category, "facet");

            return edges.newTreeBrowser({
                id: id,
                category: category,
                field: "index.schema_codes_tree.exact",
                tree: function (tree) {
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
                nodeMatch: function (node, match_list) {
                    for (var i = 0; i < match_list.length; i++) {
                        var m = match_list[i];
                        if (node.value === m.key) {
                            return i;
                        }
                    }
                    return -1;
                },
                filterMatch: function (node, selected) {
                    return $.inArray(node.value, selected) > -1;
                },
                nodeIndex: function (node) {
                    return node.display.toLowerCase();
                },
                renderer: doaj.renderers.newSubjectBrowserRenderer({
                    title: "Subjects",
                    open: true,
                    hideEmpty: hideEmpty,
                    showCounts: false
                })
            })
        },

        newDateHistogramSelector : function(params) {
            if (!params) { params = {} }
            doaj.components.DateHistogramSelector.prototype = edges.newSelector(params);
            return new doaj.components.DateHistogramSelector(params);
        },
        DateHistogramSelector : function(params) {
            // "year, quarter, month, week, day, hour, minute ,second"
            // period to use for date histogram
            this.interval = params.interval || "year";

            this.sortFunction = edges.getParam(params.sortFunction, false);

            this.displayFormatter = edges.getParam(params.displayFormatter, false);

            this.active = edges.getParam(params.active, true);

            //////////////////////////////////////////////
            // values to be rendered

            this.values = [];
            this.filters = [];

            this.contrib = function(query) {
                query.addAggregation(
                    es.newDateHistogramAggregation({
                        name: this.id,
                        field: this.field,
                        interval: this.interval
                    })
                );
            };

            this.synchronise = function() {
                // reset the state of the internal variables
                this.values = [];
                this.filters = [];

                if (this.edge.result) {
                    var buckets = this.edge.result.buckets(this.id);
                    for (var i = 0; i < buckets.length; i++) {
                        var bucket = buckets[i];
                        var key = bucket.key;
                        if (this.displayFormatter) {
                            key = this.displayFormatter(key);
                        }
                        var obj = {"display" : key, "gte": bucket.key, "count" : bucket.doc_count};
                        if (i < buckets.length - 1) {
                            obj["lt"] = buckets[i+1].key;
                        }
                        this.values.push(obj);
                    }
                }

                if (this.sortFunction) {
                    this.values = this.sortFunction(this.values);
                }

                // now check to see if there are any range filters set on this field
                // this works in a very specific way: if there is a filter on this field, and it
                // starts from the date of a filter in the result list, then we make they assumption
                // that they are a match.  This is because a date histogram either has all the results
                // or only one date bin, if that date range has been selected.  And once a range is selected
                // there will be no "lt" date field to compare the top of the range to.  So, this is the best
                // we can do, and it means that if you have both a date histogram and another range selector
                // for the same field, they may confuse eachother.
                if (this.edge.currentQuery) {
                    var filters = this.edge.currentQuery.listMust(es.newRangeFilter({field: this.field}));
                    for (var i = 0; i < filters.length; i++) {
                        var from = filters[i].gte;
                        for (var j = 0; j < this.values.length; j++) {
                            var val = this.values[j];
                            if (val.gte.toString() === from) {
                                this.filters.push(val);
                            }
                        }
                    }
                }
            };

            this.selectRange = function(params) {
                var from = params.gte;
                var to = params.lt;

                var nq = this.edge.cloneQuery();


                var params = {field: this.field};

                // remove any existing range filters on this field
                nq.removeMust(es.newRangeFilter(params));

                // create the new range query
                if (from) {
                    params["gte"] = from;
                }
                if (to) {
                    params["lt"] = to;
                }
                params["format"] = "epoch_millis"   // Required for ES7.x date ranges against dateOptionalTime formats
                nq.addMust(es.newRangeFilter(params));

                // reset the search page to the start and then trigger the next query
                nq.from = 0;
                this.edge.pushQuery(nq);
                this.edge.doQuery();
            };

            this.removeFilter = function(params) {
                var from = params.gte;
                var to = params.lt;

                var nq = this.edge.cloneQuery();

                // just add a new range filter (the query builder will ensure there are no duplicates)
                var params = {field: this.field};
                if (from) {
                    params["gte"] = from;
                }
                if (to) {
                    params["lt"] = to;
                }
                nq.removeMust(es.newRangeFilter(params));

                // reset the search page to the start and then trigger the next query
                nq.from = 0;
                this.edge.pushQuery(nq);
                this.edge.doQuery();
            };

            this.clearFilters = function(params) {
                var triggerQuery = edges.getParam(params.triggerQuery, true);

                var nq = this.edge.cloneQuery();
                var qargs = {field: this.field};
                nq.removeMust(es.newRangeFilter(qargs));
                this.edge.pushQuery(nq);

                if (triggerQuery) {
                    this.edge.doQuery();
                }
            };

            this.setInterval = function(params) {
                let interval = edges.getParam(params.interval, "year");
                this.interval = interval;
                let q = this.edge.cloneQuery();
                q.removeAggregation(this.id);
                this.contrib(q);
                this.edge.pushQuery(q);
                this.edge.cycle();
            }
        },

        newReportExporter: function (params) {
            return edges.instantiate(doaj.components.ReportExporter, params, edges.newComponent);
        },
        ReportExporter: function(params) {

            this.model = edges.getParam(params.model, "journal");

            this.reportUrl = edges.getParam(params.reportUrl, "/admin/report");

            // list of dictionaries of the form
            // [{component_id: "component_id", display: "display name", exporter: function(component)}]
            // display is optional, if not provided, will attempt to use component.display
            this.facetExports = edges.getParam(params.facetExports, []);

            this.namespace = "doajreportexporter";
            this.component = this;

            this.draw = function(edge) {
                this.edge = edge;

                let toggleClass = edges.css_classes(this.namespace, "toggle", this);
                let controlsClass = edges.css_classes(this.namespace, "controls", this);
                let nameClass = edges.css_classes(this.namespace, "name", this);
                let notesClass = edges.css_classes(this.namespace, "notes", this);
                let exportClass = edges.css_classes(this.namespace, "export", this);
                let downloadClass = edges.css_classes(this.namespace, "download", this);
                let facetId = edges.css_id(this.namespace, "facet", this);

                let facetOptions = ``;
                for (let facetExport of this.facetExports) {
                    let display = this._exportDisplayName(facetExport);
                    facetOptions += `<option value="${facetExport.component_id}">${display}</option>`;
                }

                let exportNotes = current_user && current_user.role.includes("ultra_admin_reports_with_notes")
                let notesFrag = "";
                if (exportNotes) {
                    notesFrag = `<div class="checkbox">
                              <input type="checkbox" id="include_notes" class="${notesClass}">
                              <label for="include_notes">Include notes</label>
                            </div>
                            <br>`;
                }
                let frag = `<div class="row">
                    <div class="col-md-12">
                        <a href="#" class="${toggleClass}">Export Data as CSV</a>
                        <div class="${controlsClass}" style="display:none">
                            Search result exports will be generated in the background and you will be notified when they are ready to download.<br>
                            <input type="text" name="name" class="${nameClass}" placeholder="Enter a name for the export"><br>
                            ${notesFrag}
                            <button type="button" class="btn btn-primary ${exportClass}">Generate</button><br>
                            Or download the current facets<br>
                            <select name="${facetId}" id="${facetId}">
                                <option value="all">All</option>
                                ${facetOptions}
                            </select><br>
                            <button type="button" class="btn btn-primary ${downloadClass}">Download</button>
                        </div>
                    </div>
                </div>`;
                this.context.html(frag);

                let toggleSelector = edges.css_class_selector(this.namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleControls");

                let exportSelector = edges.css_class_selector(this.namespace, "export", this);
                edges.on(exportSelector, "click", this, "export");

                let downloadSelector = edges.css_class_selector(this.namespace, "download", this);
                edges.on(downloadSelector, "click", this, "download");
            };

            this.toggleControls = function(element) {
                let controlsSelector = edges.css_class_selector(this.namespace, "controls", this);
                let controls = this.jq(controlsSelector);
                controls.toggle();
            }

            this.export = function(element) {
                let cq = this.edge.currentQuery;
                let query = cq.objectify({
                    include_paging: false,
                    include_fields: false,
                    include_aggregations: false,
                    include_source_filters: false
                });
                let qa = JSON.stringify(query);

                let nameSelector = edges.css_class_selector(this.namespace, "name", this);
                let name = this.context.find(nameSelector).val();

                let notes = false;
                let exportNotes = current_user && current_user.role.includes("ultra_admin_reports_with_notes")
                if (exportNotes) {
                    let includeNotesSelector = edges.css_class_selector(this.namespace, "notes", this);
                    notes = this.context.find(includeNotesSelector).is(":checked");
                }

                $.post({
                    url: this.reportUrl,
                    data: {
                        query: qa,
                        name: name,
                        model: this.model,
                        notes: notes
                    },
                    dataType: "json",
                    success: function(data) {
                        alert(`Your export "${name}" is being generated! You will be notified when it is ready to download.`);
                    }
                });
            }

            this.download = function(element) {
                let facetSelector = edges.css_id_selector(this.namespace, "facet", this);
                let selection = this.context.find(facetSelector).val();
                let selectedExports = [];
                let filename = this.model + "_facets_" + selection + ".csv";

                if (selection === "all") {
                    selectedExports = this.facetExports;
                } else {
                    selectedExports = this.facetExports.filter(f => f.component_id === selection);
                }

                let data = [];
                let columns = [];
                for (let selectedExport of selectedExports) {
                    let component = this.edge.getComponent({id: selectedExport.component_id});
                    let exporter = selectedExport.exporter;
                    let componentData = exporter(component);

                    let prefix = this._exportDisplayName(selectedExport);
                    let termKey = prefix + " Term";
                    let countKey = prefix + " Count";
                    for (let entry of componentData) {
                        let obj = {}
                        obj[termKey] = entry.display;
                        obj[countKey] = entry.count;
                        data.push(obj);
                    }
                    columns.push(termKey);
                    columns.push(countKey);
                }

                let collapsedData = []
                while(data.length > 0) {
                    let rowAssembly = {}
                    let removals = [];
                    for (let i = 0; i < data.length; i++) {
                        let entry = data[i];
                        if (!(Object.keys(entry)[0] in rowAssembly)) {
                            rowAssembly = {...rowAssembly, ...entry}
                            removals.push(i);
                        }
                    }
                    collapsedData.push(rowAssembly);
                    data = data.filter((_, i) => !removals.includes(i));
                }

                this._deliverCSV(collapsedData, columns, filename);
            }

            this._exportDisplayName = function(facetExport) {
                let display = facetExport.display;
                if (!display) {
                    let component = this.edge.getComponent({id: facetExport.component_id});
                    display = component.display;
                }
                if (!display) {
                    display = facetExport.component_id;
                }
                return display;
            }

            this._convertToCSV = function(data, columns) {
                // Use the columns array as the header row
                const array = [columns].concat(data);

                return array.map((row, index) => {
                    // If it's the header row, return it as is
                    if (index === 0) {
                        return row.join(',');
                    }
                    // Otherwise, map the row values according to the columns
                    return columns.map(col => {
                        const value = row[col] !== undefined ? row[col] : '';
                        return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
                    }).join(',');
                }).join('\n');
            }

            // Function to trigger CSV download
            this._deliverCSV = function(data, columns, filename = 'facets.csv') {
                let csv = this._convertToCSV(data, columns);

                let dateGenerated = new Date();
                let header = `"Date generated","${dateGenerated.toISOString()}"\n`;

                let searchURL = this.component.edge.fullUrl();
                header += `"Search URL","${searchURL}"\n"",""\n`;

                csv = header + csv;

                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                // document.body.removeChild(link);
            }
        },

        newSimultaneousDateRangeEntry: function (params) {
            if (!params) { params = {}}
            doaj.components.SimultaneousDateRangeEntry.prototype = edges.newComponent(params);
            return new doaj.components.SimultaneousDateRangeEntry(params);
        },
        SimultaneousDateRangeEntry: function (params) {
            ///////////////////////////////////////////////
            // fields that can be passed in, and their defaults

            // free text to prefix entry boxes with
            this.display = edges.getParam(params.display, false);

            // list of field objects, which provide the field itself, and the display name.  e.g.
            // [{field : "monitor.rioxxterms:publication_date", display: "Publication Date"}]
            this.fields = edges.getParam(params.fields, []);

            // map from field name (as in this.field[n].field) to a function which will provide
            // the earliest allowed date for that field.  e.g.
            // {"monitor.rioxxterms:publication_date" : earliestDate}
            this.earliest = edges.getParam(params.earliest, {});

            // map from field name (as in this.field[n].field) to a function which will provide
            // the latest allowed date for that field.  e.g.
            // {"monitor.rioxxterms:publication_date" : latestDate}
            this.latest = edges.getParam(params.latest, {});

            this.autoLookupRange = edges.getParam(params.autoLookupRange, false);

            // category for this component, defaults to "selector"
            this.category = edges.getParam(params.category, "selector");

            // default earliest date to use in all cases (defaults to start of the unix epoch)
            this.defaultEarliest = edges.getParam(params.defaultEarliest, new Date(0));

            // default latest date to use in all cases (defaults to now)
            this.defaultLatest = edges.getParam(params.defaultLatest, new Date());

            // list of filters to apply to the autolookup secondary query
            this.autoLookupFilters = edges.getParam(params.autoLookupFilters, false);

            // default renderer from render pack to use
            this.defaultRenderer = edges.getParam(params.defaultRenderer, "newMultiDateRangeRenderer");

            ///////////////////////////////////////////////
            // fields used to track internal state

            this.lastField = false;
            this.currentField = false;
            this.fromDate = false;
            this.toDate = false;

            this.touched = false;
            this.dateOptions = {};
            this.existingFilters = {};

            this.init = function(edge) {
                Object.getPrototypeOf(this).init.call(this, edge);

                // set the initial field
                this.currentField = this.fields[0].field;

                // if required, load the dates once at init
                if (!this.autoLookupRange) {
                    this.loadDates();
                } else {
                    if (edge.secondaryQueries === false) {
                        edge.secondaryQueries = {};
                    }
                    edge.secondaryQueries["multidaterange_" + this.id] = this.getSecondaryQueryFunction();
                }
            };

            this.synchronise = function() {
                this.currentField = false;
                this.fromDate = false;
                this.toDate = false;
                this.existingFilters = {};

                if (this.autoLookupRange) {
                    for (var i = 0; i < this.fields.length; i++) {
                        var field = this.fields[i].field;
                        var agg = this.edge.secondaryResults["multidaterange_" + this.id].aggregation(field);

                        var min = this.defaultEarliest;
                        var max = this.defaultLatest;
                        if (agg.min !== null) {
                            min = new Date(agg.min);
                        }
                        if (agg.max !== null) {
                            max = new Date(agg.max);
                        }

                        this.dateOptions[field] = {
                            earliest: min,
                            latest: max
                        }
                    }
                }

                for (var i = 0; i < this.fields.length; i++) {
                    var field = this.fields[i].field;
                    var filters = this.edge.currentQuery.listMust(es.newRangeFilter({field: field}));
                    if (filters.length > 0) {
                        for (let filter of filters) {
                            if (!this.currentField || (this.lastField && this.lastField === field)) {
                                this.currentField = field;
                                this.fromDate = parseInt(filter.gte);
                                this.toDate = parseInt(filter.lt);
                            }
                            this.existingFilters[field] = {
                                fromDate: filter.gte,
                                toDate: filter.lt
                            }
                        }
                    }
                }

                if (!this.currentField && this.lastField) {
                    this.currentField = this.lastField;
                }

                if (!this.currentField && this.fields.length > 0) {
                    this.currentField = this.fields[0].field;
                }
            };

            //////////////////////////////////////////////
            // functions that can be used to trigger state change

            this.currentEarliest = function () {
                if (!this.currentField) {
                    return false;
                }
                if (this.dateOptions[this.currentField]) {
                    return this.dateOptions[this.currentField].earliest;
                }
            };

            this.currentLatest = function () {
                if (!this.currentField) {
                    return false;
                }
                if (this.dateOptions[this.currentField]) {
                    return this.dateOptions[this.currentField].latest;
                }
            };

            this.changeField = function (newField) {
                this.lastField = this.currentField;
                if (newField !== this.currentField) {
                    this.touched = true;
                    this.currentField = newField;
                    if (this.currentField in this.existingFilters) {
                        this.setFrom(this.existingFilters[this.currentField].fromDate);
                        this.setTo(this.existingFilters[this.currentField].toDate);
                    } else {
                        this.setFrom(false);
                        this.setTo(false);
                    }
                }
            };

            this.setFrom = function (from) {
                if (from !== this.fromDate) {
                    this.touched = true;
                    this.fromDate = from;
                }
            };

            this.setTo = function (to) {
                if (to !== this.toDate) {
                    this.touched = true;
                    this.toDate = to;
                }
            };

            this.triggerSearch = function () {
                if (this.touched) {
                    this.touched = false;
                    var nq = this.edge.cloneQuery();

                    // remove any old filters for this field
                    var removeCount = nq.removeMust(es.newRangeFilter({field: this.currentField}));

                    // in order to avoid unnecessary searching, check the state of the data and determine
                    // if we need to.
                    // - we need to add a new filter to the query if there is a current field and one/both of from and to dates
                    // - we need to do a search if we removed filters before, or are about to add one
                    var addFilter = this.currentField && (this.toDate || this.fromDate);
                    var doSearch = removeCount > 0 || addFilter;

                    // if we're not going to do a search, return
                    if (!doSearch) {
                        return false;
                    }

                    // if there's a filter to be added, do that here
                    if (addFilter) {
                        var range = {field: this.currentField};
                        if (this.toDate) {
                            range["lt"] = this.toDate;
                        }
                        if (this.fromDate) {
                            range["gte"] = this.fromDate;
                        }
                        range["format"] = "epoch_millis"   // Required for ES7.x date ranges against dateOptionalTime formats
                        nq.addMust(es.newRangeFilter(range));
                    }

                    // push the new query and trigger the search
                    this.edge.pushQuery(nq);
                    this.edge.doQuery();

                    return true;
                }
                return false;
            };

            this.loadDates = function () {
                for (var i = 0; i < this.fields.length; i++) {
                    var field = this.fields[i].field;

                    // start with the default earliest and latest
                    var early = this.defaultEarliest;
                    var late = this.defaultLatest;

                    // if specific functions are provided for getting the dates, run them
                    var earlyFn = this.earliest[field];
                    var lateFn = this.latest[field];
                    if (earlyFn) {
                        early = earlyFn();
                    }
                    if (lateFn) {
                        late = lateFn();
                    }

                    this.dateOptions[field] = {
                        earliest: early,
                        latest: late
                    }
                }
            };

            this.getSecondaryQueryFunction = function() {
                var that = this;
                return function(edge) {
                    // clone the current query, which will be the basis for the averages query
                    var query = edge.cloneQuery();

                    // remove any range constraints
                    for (var i = 0; i < that.fields.length; i++) {
                        var field = that.fields[i];
                        query.removeMust(es.newRangeFilter({field: field.field}));
                    }

                    // add the filters that are required for the secondary query
                    if (that.autoLookupFilters) {
                        for (let filter of that.autoLookupFilters) {
                            query.addMust(filter);
                        }
                    }

                    // remove any existing aggregations, we don't need them
                    query.clearAggregations();

                    // add the new aggregation(s) which will actually get the data
                    for (var i = 0; i < that.fields.length; i++) {
                        var field = that.fields[i].field;
                        query.addAggregation(
                            es.newStatsAggregation({
                                name: field,
                                field : field
                            })
                        );
                    }

                    // finally set the size and from parameters
                    query.size = 0;
                    query.from = 0;

                    // return the secondary query
                    return query;
                }
            }
        },

        newFacetDivider: function (params) {
            return edges.instantiate(doaj.components.FacetDivider, params, edges.newComponent);
        },
        FacetDivider: function(params) {
            this.display = edges.getParam(params.display, "");
            this.namespace = "doajfacetdivider";

            this.drawn = false;

            this.draw = function() {
                if (this.drawn) {
                    return
                }

                let frag = `<hr><strong>${this.display}</strong><br>`;
                this.context.html(frag);
                this.drawn = true;
            };
        }
    },

    templates: {
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
                        <div class="col-sm-2 col-md-3">\
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
                        <div class="col-sm-10 col-md-9">\
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

    renderers: {
        newBSMultiDateRangeFacet: function (params) {
            if (!params) {params = {}}
            doaj.renderers.BSMultiDateRangeFacet.prototype = edges.newRenderer(params);
            return new doaj.renderers.BSMultiDateRangeFacet(params);
        },
        BSMultiDateRangeFacet: function (params) {
            ///////////////////////////////////////////////////
            // parameters that can be passed in

            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            this.togglable = edges.getParam(params.togglable, true);

            this.openIcon = edges.getParam(params.openIcon, "glyphicon glyphicon-plus");

            this.closeIcon = edges.getParam(params.closeIcon, "glyphicon glyphicon-minus");

            this.layout = edges.getParam(params.layout, "left");

            this.dateFormat = edges.getParam(params.dateFormat, "MMMM D, YYYY");

            this.ranges = edges.getParam(params.ranges, false);

            this.prefix = edges.getParam(params.prefix, "");

            ///////////////////////////////////////////////////
            // parameters for tracking internal state

            this.dre = false;

            this.selectId = false;
            this.fromId = false;
            this.toId = false;

            this.selectJq = false;
            this.fromJq = false;
            this.toJq = false;

            this.drp = false;
            this.months = doaj.listMonthsInLocale();

            this.namespace = "doaj-multidaterange";

            this.draw = function () {
                var dre = this.component;

                var selectClass = edges.css_classes(this.namespace, "select", this);
                var facetClass = edges.css_classes(this.namespace, "facet", this);
                var headerClass = edges.css_classes(this.namespace, "header", this);
                var bodyClass = edges.css_classes(this.namespace, "body", this);

                var toggleId = edges.css_id(this.namespace, "toggle", this);
                var formId = edges.css_id(this.namespace, "form", this);

                this.selectId = edges.css_id(this.namespace, "date-type", this);
                let fromMonthId = edges.css_id(this.namespace, "from-month", this);
                let fromYearId = edges.css_id(this.namespace, "from-year", this);
                let toMonthId = edges.css_id(this.namespace, "to-month", this);
                let toYearId = edges.css_id(this.namespace, "to-year", this);
                let applyClass = edges.css_classes(this.namespace, "apply", this);

                let header = this.headerLayout({toggleId: toggleId});

                var options = "";
                for (var i = 0; i < dre.fields.length; i++) {
                    var field = dre.fields[i];
                    var selected = dre.currentField === field.field ? ' selected="selected" ' : "";
                    options += '<option value="' + field.field + '"' + selected + '>' + field.display + '</option>';
                }

                // create the controls
                let toFromFrags = this.dateOptionsFrags();

                let frag = `<div class="form-inline">
                                        <div class="form-group">
                                            Type: <select class="${selectClass} form-control input-sm" name="${this.selectId}" id="${this.selectId}">
                                                ${options}
                                            </select><br>
                                            From:
                                            <select class="form-control input-sm" id="${fromMonthId}">
                                                ${toFromFrags.fromMonths}
                                            </select>
                                            <select class="form-control input-sm" id="${fromYearId}">
                                                ${toFromFrags.fromYears}
                                            </select><br>
                                            To: 
                                            <select class="form-control input-sm" id="${toMonthId}">
                                                ${toFromFrags.toMonths}
                                            </select>
                                            <select class="form-control input-sm" id="${toYearId}">
                                                ${toFromFrags.toYears}
                                            </select><br>
                                            <button type="button" class="btn btn-primary ${applyClass}" id="">Apply</button>
                                        </div>
                                    </div>`;

                let filterRemoveClass = edges.css_classes(this.namespace, "filter-remove", this);
                let existing = ``;
                for (let field in dre.existingFilters) {
                    for (let fd of dre.fields) {
                        if (fd.field === field) {
                            let map = doaj.valueMaps.displayYearMonthPeriod({
                                from: dre.existingFilters[field].fromDate,
                                to: dre.existingFilters[field].toDate
                            });
                            let range = map.display;

                            existing += `<strong>${fd.display}</strong>: 
                                            ${range}<a href="#" class="${filterRemoveClass}" data-field="${field}"><i class="glyphicon glyphicon-black glyphicon-remove"></i></a><br>`;
                        }
                    }
                }

                let facet = `<div class="${facetClass}">
                    <div class="${headerClass}">
                        <div class="row">
                            <div class="col-md-12">
                                ${header}
                            </div>
                        </div>
                    </div>
                    <div class="${bodyClass}">
                        <div class="row" style="display:none" id="${formId}">
                            <div class="col-md-12">
                                ${frag}
                            </div>
                            <div class="col-md-12">
                                ${existing}
                            </div>
                        </div>
                    </div>
                </div>`;

                dre.context.html(facet);

                // trigger all the post-render set-up functions
                this.setUIOpen();

                // sort out the selectors we're going to be needing
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");

                let selectIdSelector = edges.css_id_selector(this.namespace, "date-type", this);
                edges.on(selectIdSelector, "change", this, "typeChanged");

                let fromMonthSelector = edges.css_id_selector(this.namespace, "from-month", this);
                let fromYearSelector = edges.css_id_selector(this.namespace, "from-year", this);
                let toMonthSelector = edges.css_id_selector(this.namespace, "to-month", this);
                let toYearSelector = edges.css_id_selector(this.namespace, "to-year", this);
                edges.on(fromMonthSelector, "change", this, "checkDateRange");
                edges.on(fromYearSelector, "change", this, "checkDateRange");
                edges.on(toMonthSelector, "change", this, "checkDateRange");
                edges.on(toYearSelector, "change", this, "checkDateRange");

                let applySelector = edges.css_class_selector(this.namespace, "apply", this);
                edges.on(applySelector, "click", this, "updateDateRange");

                let filterRemoveSelector = edges.css_class_selector(this.namespace, "filter-remove", this);
                edges.on(filterRemoveSelector, "click", this, "removeFilter");
            };

            this.dateOptionsFrags = function (params) {
                let dre = this.component;

                let fromMonths = "";
                let toMonths = "";
                let fromYears = "";
                let toYears = "";

                let earliest = dre.currentEarliest();
                let latest = dre.currentLatest();
                if (earliest && latest) {

                    let startYear = earliest.getUTCFullYear();
                    let endYear = latest.getUTCFullYear();
                    let years = [];
                    for (let year = startYear; year <= endYear; year++) {
                        years.push(year);
                    }

                    let selectedFromYear = 0;
                    let selectedToYear = 0;

                    let fromDate = dre.fromDate ? new Date(parseInt(dre.fromDate)): false;
                    let toDate = dre.toDate ? new Date(parseInt(dre.toDate - 1)) : false;

                    for (let i = 0; i < years.length; i++) {
                        let year = years[i];
                        let fromSelected = "";
                        if ((!fromDate && i === 0) || (fromDate && year === fromDate.getUTCFullYear())) {
                            fromSelected = "selected"
                            selectedFromYear = year;
                        }
                        let toSelected = "";
                        if ((!toDate && i === years.length - 1) || (toDate && year === toDate.getUTCFullYear())) {
                            toSelected = "selected"
                            selectedToYear = year;
                        }
                        fromYears += `<option value="${year}" ${fromSelected}>${year}</option>`;
                        toYears += `<option value="${year}" ${toSelected}>${year}</option>`;
                    }

                    for (let i = 0; i < this.months.length; i++) {
                        let month = this.months[i];

                        let fromSelected = "";
                        if (fromDate) {
                            if (i === fromDate.getUTCMonth() && selectedFromYear === fromDate.getUTCFullYear()) {
                                fromSelected = "selected"
                            }
                        } else {
                            if (i === earliest.getUTCMonth()) {
                                fromSelected = "selected"
                            }
                        }

                        let toSelected = "";
                        if (toDate) {
                            if (i === toDate.getUTCMonth() && selectedToYear === toDate.getUTCFullYear()) {
                                toSelected = "selected"
                            }
                        } else {
                            if (i === latest.getUTCMonth()) {
                                toSelected = "selected"
                            }
                        }

                        fromMonths += `<option value="${i}" ${fromSelected}>${month}</option>`;
                        toMonths += `<option value="${i}" ${toSelected}>${month}</option>`;
                    }
                }

                return {fromMonths: fromMonths, toMonths: toMonths, fromYears: fromYears, toYears: toYears};
            };

            this.headerLayout = function (params) {
                var toggleId = params.toggleId;
                var iconClass = edges.css_classes(this.namespace, "icon", this);

                if (this.layout === "left") {
                    var tog = this.component.display;
                    if (this.togglable) {
                        tog = '<a href="#" id="' + toggleId + '"><i class="' + this.openIcon + '"></i>&nbsp;' + tog + "</a>";
                    }
                    return tog;
                } else if (this.layout === "right") {
                    var tog = "";
                    if (this.togglable) {
                        tog = '<a href="#" id="' + toggleId + '">' + this.component.display + '&nbsp;<i class="' + this.openIcon + ' ' + iconClass + '"></i></a>';
                    } else {
                        tog = this.component.display;
                    }

                    return tog;
                }
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var formSelector = edges.css_id_selector(this.namespace, "form", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var form = this.component.jq(formSelector);
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
                    form.show();
                } else {
                    var i = toggle.find("i");
                    for (var j = 0; j < closeBits.length; j++) {
                        i.removeClass(closeBits[j]);
                    }
                    for (var j = 0; j < openBits.length; j++) {
                        i.addClass(openBits[j]);
                    }
                    form.hide();
                }
            };

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };

            this.dateRangeDisplay = function() {
                let frags = this.dateOptionsFrags();
                let fromMonthSelector = edges.css_id_selector(this.namespace, "from-month", this);
                let fromYearSelector = edges.css_id_selector(this.namespace, "from-year", this);
                let toMonthSelector = edges.css_id_selector(this.namespace, "to-month", this);
                let toYearSelector = edges.css_id_selector(this.namespace, "to-year", this);
                this.component.jq(fromMonthSelector).html(frags.fromMonths);
                this.component.jq(fromYearSelector).html(frags.fromYears);
                this.component.jq(toMonthSelector).html(frags.toMonths);
                this.component.jq(toYearSelector).html(frags.toYears);
            };

            this.updateDateRange = function () {
                // ensure that the correct field is set (it may initially be not set)
                let typeSelector = edges.css_id_selector(this.namespace, "date-type", this);
                let date_type = this.component.jq(typeSelector).val();

                let fromMonthSelector = edges.css_id_selector(this.namespace, "from-month", this);
                let fromYearSelector = edges.css_id_selector(this.namespace, "from-year", this);
                let toMonthSelector = edges.css_id_selector(this.namespace, "to-month", this);
                let toYearSelector = edges.css_id_selector(this.namespace, "to-year", this);
                let fromMonth = this.component.jq(fromMonthSelector).val()
                let fromYear = this.component.jq(fromYearSelector).val()
                let toMonth = this.component.jq(toMonthSelector).val()
                let toYear = this.component.jq(toYearSelector).val()

                let start = new Date(Date.UTC(fromYear, fromMonth, 1, 0, 0, 0));

                toMonth = parseInt(toMonth);
                toMonth += 1;
                if (toMonth > 11) {
                    toMonth = 0;
                    toYear = parseInt(toYear) + 1;
                }
                let end = new Date(Date.UTC(toYear, toMonth, 1, 0, 0, 0));

                if (end < start) {
                    alert("You must choose a 'to' date that is after the 'from' date");
                    return;
                }

                this.component.changeField(date_type);
                this.component.setFrom(start.getTime());
                this.component.setTo(end.getTime());

                // this action should trigger a search (the parent object will
                // decide if that's required)
                this.component.triggerSearch();
            };

            this.checkDateRange = function(element) {
                let fromMonthSelector = edges.css_id_selector(this.namespace, "from-month", this);
                let fromYearSelector = edges.css_id_selector(this.namespace, "from-year", this);
                let toMonthSelector = edges.css_id_selector(this.namespace, "to-month", this);
                let toYearSelector = edges.css_id_selector(this.namespace, "to-year", this);
                let fromMonth = this.component.jq(fromMonthSelector).val()
                let fromYear = this.component.jq(fromYearSelector).val()
                let toMonth = this.component.jq(toMonthSelector).val()
                let toYear = this.component.jq(toYearSelector).val()

                let start = new Date(Date.UTC(fromYear, fromMonth, 1, 0, 0, 0));

                toMonth = parseInt(toMonth);
                toMonth += 1;
                if (toMonth > 11) {
                    toMonth = 0;
                    toYear = parseInt(toYear) + 1;
                }
                let end = new Date(Date.UTC(toYear, toMonth, 1, 0, 0, 0));

                let applySelector = edges.css_class_selector(this.namespace, "apply", this);
                if (end <= start) {
                    this.component.jq(applySelector).prop("disabled", true);
                } else {
                    this.component.jq(applySelector).prop("disabled", false);
                }
            }

            this.typeChanged = function(element) {
                // ensure that the correct field is set (it may initially be not set)
                let typeSelector = edges.css_id_selector(this.namespace, "date-type", this);
                let date_type = this.component.jq(typeSelector).val();
                this.component.changeField(date_type);
                this.dateRangeDisplay();
                this.checkDateRange();
            };

            this.removeFilter = function(element) {
                let field = $(element).attr("data-field");
                this.component.changeField(field);
                this.component.setFrom(false);
                this.component.setTo(false);
                this.component.triggerSearch();
            }
        },

        newFlexibleDateHistogramSelectorRenderer: function (params) {
            if (!params) { params = {} }
            doaj.renderers.FlexibleDateHistogramSelectorRenderer.prototype = edges.newRenderer(params);
            return new doaj.renderers.FlexibleDateHistogramSelectorRenderer(params);
        },
        FlexibleDateHistogramSelectorRenderer: function (params) {

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

            // formatter for count display
            this.countFormat = edges.getParam(params.countFormat, false);

            // a short tooltip and a fuller explanation
            this.tooltipText = edges.getParam(params.tooltipText, false);
            this.tooltip = edges.getParam(params.tooltip, false);
            this.tooltipState = "closed";

            // whether to suppress display of date range with no values
            this.hideEmptyDateBin = params.hideEmptyDateBin || true;

            // how many of the values to display initially, with a "show all" option for the rest
            this.shortDisplay = edges.getParam(params.shortDisplay, false);

            // namespace to use in the page
            this.namespace = "edges-bs3-datehistogram-selector";

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

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results
                var results = "Loading...";
                if (ts.values !== false) {
                    results = "No data available";
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
                    var longClass = edges.css_classes(namespace, "long", this);
                    var short = true;
                    for (var i = 0; i < ts.values.length; i++) {
                        var val = ts.values[i];
                        if (val.count === 0 && this.hideEmptyDateBin) {
                            continue;
                        }
                        //if ($.inArray(val.display, filterTerms) === -1) {
                            var myLongClass = "";
                            var styles = "";
                            if (this.shortDisplay && this.shortDisplay <= i) {
                                myLongClass = longClass;
                                styles = 'style="display:none"';
                                short = false;
                            }

                            var count = val.count;
                            if (this.countFormat) {
                                count = this.countFormat(count)
                            }
                            var ltData = "";
                            if (val.lt) {
                                ltData = ' data-lt="' + edges.escapeHtml(val.lt) + '" ';
                            }
                            results += '<div class="' + resultClass + ' ' + myLongClass + '" '  + styles +  '><a href="#" class="' + valClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + '>' +
                                edges.escapeHtml(val.display) + "</a> (" + count + ")</div>";

                        //}
                    }
                    if (!short) {
                        var showClass = edges.css_classes(namespace, "show-link", this);
                        var showId = edges.css_id(namespace, "show-link", this);
                        var slToggleId = edges.css_id(namespace, "sl-toggle", this);
                        results += '<div class="' + showClass + '" id="' + showId + '">\
                            <a href="#" id="' + slToggleId + '"><span class="all">show all</span><span class="less" style="display:none">show less</span></a> \
                        </div>';
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
                        filterFrag += '<div class="' + resultClass + '"><strong>' + edges.escapeHtml(filt.display) + "&nbsp;";
                        filterFrag += '<a href="#" class="' + filterRemoveClass + '" data-gte="' + edges.escapeHtml(filt.gte) + '"' + ltData + '>';
                        filterFrag += '<i class="glyphicon glyphicon-black glyphicon-remove"></i></a>';
                        filterFrag += "</strong></a></div>";
                    }
                }

                // render the toggle capability
                var tog = ts.display;
                if (this.togglable) {
                    tog = '<a href="#" id="' + toggleId + '"><i class="glyphicon glyphicon-plus"></i>&nbsp;' + tog + "</a>";
                }

                // create the controls
                let intervalClass = edges.css_classes(namespace, "interval", this);
                let yearSelected = this.component.interval === "year" ? "selected" : "";
                let monthSelected = this.component.interval === "month" ? "selected" : "";

                let controls = `Granularity <select name="interval" class="${intervalClass}">
                                            <option value="year" ${yearSelected}>Year</option>
                                            <option value="month" ${monthSelected}>Month</option>
                                        </select>`;

                // render the overall facet
                var frag = `<div class=${facetClass}>
                        <div class=${headerClass}"><div class="row">
                            <div class="col-md-12">${tog}</div>
                        </div></div>
                        <div class="row" style="display:none" id="${resultsId}">
                            <div class="col-md-12">
                                <div class="">${controls}</div>
                                <div class="${selectedClass}">{{SELECTED}}</div>
                                <div class="${resultsListClass}">{{RESULTS}}</div>
                            </div>
                        </div></div>`;

                // substitute in the component parts
                frag = frag.replace(/{{RESULTS}}/g, results)
                    .replace(/{{SELECTED}}/g, filterFrag);

                // now render it into the page
                ts.context.html(frag);

                // trigger all the post-render set-up functions
                this.setUIOpen();

                // sort out the selectors we're going to be needing
                var valueSelector = edges.css_class_selector(namespace, "value", this);
                var filterRemoveSelector = edges.css_class_selector(namespace, "filter-remove", this);
                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                var tooltipSelector = edges.css_id_selector(namespace, "tooltip-toggle", this);
                var shortLongToggleSelector = edges.css_id_selector(namespace, "sl-toggle", this);
                let fromSelector = edges.css_class_selector(namespace, "from", this);
                let toSelector = edges.css_class_selector(namespace, "to", this);
                let intervalSelector = edges.css_class_selector(namespace, "interval", this);
                let resetSelector = edges.css_class_selector(namespace, "reset", this);

                // for when a value in the facet is selected
                edges.on(valueSelector, "click", this, "termSelected");
                // for when the open button is clicked
                edges.on(toggleSelector, "click", this, "toggleOpen");
                // for when a filter remove button is clicked
                edges.on(filterRemoveSelector, "click", this, "removeFilter");

                edges.on(intervalSelector, "change", this, "intervalChanged");
                edges.on(fromSelector, "change", this, "rangeChanged");
                edges.on(toSelector, "change", this, "rangeChanged");
                edges.on(resetSelector, "click", this, "removeFilter");
            };

            /////////////////////////////////////////////////////
            // UI behaviour functions

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var tooltipSelector = edges.css_id_selector(this.namespace, "tooltip", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var tooltip = this.component.jq(tooltipSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    toggle.find("i").removeClass("glyphicon-plus").addClass("glyphicon-minus");
                    results.show();
                    tooltip.show();
                } else {
                    toggle.find("i").removeClass("glyphicon-minus").addClass("glyphicon-plus");
                    results.hide();
                    tooltip.hide();
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

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

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };

            this.intervalChanged = function(element) {
                let interval = $(element).val();
                this.component.setInterval({interval: interval});
            }

            this.rangeChanged = function(element) {
                let fromSelector = edges.css_class_selector(this.namespace, "from", this);
                let toSelector = edges.css_class_selector(this.namespace, "to", this);

                let from = this.component.jq(fromSelector).val();
                let to = this.component.jq(toSelector).val();

                this.component.selectRange({gte: from, lt: to});
            }
        },
        newSearchingNotificationRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchingNotificationRenderer, params, edges.newRenderer);
        },
        SearchingNotificationRenderer: function (params) {

            this.scrollTarget = edges.getParam(params.scrollTarget, "body");

            this.scrollOnSearch = edges.getParam(params.scrollOnSearch, false);

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

                    if (this.scrollOnSearch) {
                        let offset = $(this.scrollTarget).offset().top
                        window.scrollTo(0, offset);
                    }
                } else {
                    let that = this;
                    let idSelector = edges.css_id_selector(this.namespace, "loading", this);
                    this.component.edge.context.animate(
                        {
                            opacity: "1",
                        },
                        {
                            duration: 1000,
                            always: function () {
                                $(idSelector).remove();
                            }
                        }
                    );
                }
            }
        },
        newSubjectBrowserRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SubjectBrowserRenderer, params, edges.newRenderer);
        },
        SubjectBrowserRenderer: function (params) {
            this.title = edges.getParam(params.title, "");

            this.selectMode = edges.getParam(params.selectMode, "multiple");

            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            this.togglable = edges.getParam(params.togglable, true);

            this.open = edges.getParam(params.open, false);

            this.showCounts = edges.getParam(params.showCounts, false);

            this.namespace = "doaj-subject-browser";

            this.viewWindowScrollOffset = 0;
            this.lastScroll = 0;
            this.lastSearch = edges.getParam(params.lastSearch, null);
            this.lastClickedEl = edges.getParam(params.lastClickedEl, null);

            this.init = function(component) {
                edges.newRenderer().init.call(this, component);
                component.edge.context.on("edges:pre-reset", edges.eventClosure(this, "reset"));
            }

            this.draw = function () {
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
                var frag = '<div class="accordion"><h3 class="label label--secondary filter__heading" id="' + toggleId + '"><button class="aria-button" aria-expanded="false">' + this.title + toggle + '</button></h3>\
                    <div class="filter__body collapse" style="height: 0px" id="' + resultsId + '">\
                        <label for="' + searchId + '" class="sr-only">' + placeholder + '</label>\
                        <input type="text" name="' + searchId + '" id="' + searchId + '" class="filter__search" placeholder="' + placeholder + '"';
                if (this.lastSearch) {
                    frag += 'value="' + this.lastSearch + '"';
                }

                frag += '>\
                        <ul class="filter__choices" id="' + filteredId + '" style="display:none"></ul>\
                        <ul class="filter__choices" id="' + mainListId + '">{{FILTERS}}</ul>\
                    </div></div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, treeFrag);

                // now render it into the page
                this.component.context.html(frag);
                feather.replace();

                if (this.lastSearch) {
                    var searchSelector = edges.css_id_selector(namespace, "search", this);
                    this.filterSubjects($(searchSelector));
                }


                // trigger all the post-render set-up functions
                this.setUIOpen();

                var mainListSelector = edges.css_id_selector(namespace, "main", this);
                var filterSelector = edges.css_id_selector(this.namespace, "filtered", this);
                var selector = this.lastSearch ? filterSelector : mainListSelector;
                this.component.jq(selector).scrollTop(this.lastScroll);

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                if (this.togglable) {
                    var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                    edges.on(toggleSelector, "click", this, "toggleOpen");
                }

                var searchSelector = edges.css_id_selector(namespace, "search", this);
                edges.on(searchSelector, "keyup", this, "filterSubjects");
            };

            this.reset = function(edge) {
                this.lastSearch = null;
                this.viewWindowScrollOffset = 0;
                this.lastClickedEl = null;
                this.lastScroll = 0;
            }

            this._renderTree = function (params) {
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
                    return {frag: rFrag, anySelected: anySelected};
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
                    results.removeClass("in").attr("aria-expanded", "false").css({"height": "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function (element) {
                var mainListSelector = edges.css_id_selector(this.namespace, "main", this);
                var filterSelector = edges.css_id_selector(this.namespace, "filtered", this);
                this.lastScroll = this.lastSearch ? this.component.jq(filterSelector).scrollTop() : this.component.jq(mainListSelector).scrollTop();
                var el = this.component.jq(element);
                var checked = el.is(":checked");
                this.lastClickedEl = el[0].id;
                let offset = this.lastSearch ? this.component.jq(filterSelector).offset().top : this.component.jq(mainListSelector).offset().top;
                this.viewWindowScrollOffset = el.offset().top - offset;
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

            this._findParentObject = function(st, value) {
                // Iterate through the array to find the object with children containing the lastClickedEl value
                for (const obj of st) {
                    if (obj.children && obj.children.some(child => child.value === value)) {
                        return obj;
                    }
                }
                return null; // If no parent object is found
            }

            this._findRenderedElement = function(st, value) {
                let label = this.component.jq("label[for='" + value + "']");
                if (label.length > 0) {
                    return label[0];
                }

                // Step 1: Find HTML element with id=lastClickedEl
                const element = document.getElementById(value);

                // Step 2: If it exists, return the element
                if (element) {
                    return element;
                }

                // Step 3: If it doesn't exist, find the parent in the st array
                const parentObject = this._findParentObject(st, value);

                // Step 4: If no more parents (no elements found), return null
                if (!parentObject) {
                    return null;
                }

                // Step 5: Repeat this algorithm for the value of the found parent
                return this._findRenderedElement(st, parentObject.value);
            }

            this.scrollView = function (view) {
                var browser = view[0];
                var st = this.component.syncTree;
                var elemToScroll = this._findRenderedElement(st, this.lastClickedEl);
                if (elemToScroll) {
                    elemToScroll.scrollIntoView();
                    if (browser.clientHeight > 0) {
                        browser.scrollBy(0, -1 * browser.clientHeight / 2);
                    }
                    // browser.scrollTop = elemToScroll.offsetTop - browser.offsetTop - this.viewWindowScrollOffset;
                }
            }

            this.filterSubjects = function (element) {
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
                    this.lastSearch = null;
                    if (this.lastClickedEl) {
                        this.scrollView(mainEl);
                    }
                    return;
                }
                if (term.length < 3) {
                    filterEl.html("<li>Enter 3 characters or more to search</li>");
                    filterEl.show();
                    mainEl.hide();
                    return;
                }
                this.lastSearch = term;
                term = term.toLowerCase();

                function entryMatch(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return false;
                    }

                    var matchTerm = entry.index;
                    var includes = matchTerm.includes(term);
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
                    var displayReport = this._renderTree({
                        tree: filtered,
                        selectedPathOnly: false,
                        showOneLevel: false
                    });

                    filterEl.html(displayReport.frag);
                    mainEl.hide();
                    filterEl.show();

                    if (this.lastClickedEl) {
                        this.scrollView(filterEl);
                    }

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
                                    <select class="' + sortFieldClass + ' input-group__input">';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        sortOptions += '<option value="' + field + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += '<option value="_score">Relevance</option>\
                      </select></div>';
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

                var frag = searchBox + '<div class="container-fluid"><div class="row">' + sortOptions + clearFrag + '</div></div>';

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
                let sb = this.component.sortBy
                if (!this.component.sortBy) {
                    sb = "_score";
                }
                // get the selector we need
                var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                var el = this.component.jq(sortSelector);
                el.val(sb);
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

                var shareButtonClass = edges.css_classes(this.namespace, "toggle-share", this);
                var modalId = edges.css_id(this.namespace, "modal", this);
                let shareButtonFrag = '<button data-toggle="modal" data-target="#' + modalId + '" class="' + shareButtonClass + ' button button--tertiary" role="button">' + this.shareLinkText + '</button>';

                let shorten = "";
                if (this.component.urlShortener) {
                    var shortenButtonClass = edges.css_classes(this.namespace, "shorten-url", this)
                    shorten = '<p><button class="' + shortenButtonClass + '">shorten url</button></p>';
                }
                var embed = "";
                if (this.component.embedSnippet) {
                    var embedClass = edges.css_classes(this.namespace, "embed", this);
                    embed = '<p>Embed this search in your site</p>\
                    <textarea style="width: 100%; height: 150px" readonly class="' + embedClass + '"></textarea>';
                }
                var shareBoxClass = edges.css_classes(this.namespace, "share", this);
                var shareUrlClass = edges.css_classes(this.namespace, "share-url", this);

                var shareFrag = '<div class="' + shareBoxClass + '">\
                    <p>Share a link to this search</p>\
                    <textarea style="width: 100%; height: 150px" readonly class="' + shareUrlClass + '"></textarea>\
                    ' + shorten + '\
                    ' + embed + '\
                </div>';

                var modal = '<section class="modal" id="' + modalId + '" tabindex="-1" role="dialog">\
                    <div class="modal__dialog" role="document">\
                        <form role="search">\
                            <header class="flex-space-between modal__heading"> \
                                <h2 class="modal__title">' + this.shareLinkText + '</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
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

            this.toggleShare = function (element) {
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

            this.toggleShorten = function (element) {
                if (!this.component.shortUrl) {
                    var callback = edges.objClosure(this, "updateShortUrl");
                    this.component.generateShortUrl(callback);
                } else {
                    this.updateShortUrl();
                }
            };

            this.updateShortUrl = function () {
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

                // if there is search text, then proceed to run the search
                var val = this.component.jq(element).val();
                this.component.setSearchField(val, false);
                if (text === "") {
                    return;
                }
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

            this.filterToggle = function (element) {
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
                var frag = '<div class="accordion"><h3 class="label label--secondary filter__heading" id="' + toggleId + '"><button class="aria-button" aria-expanded="false">' + this.component.display + toggle + '</button></h3>\
                    <div class="filter__body collapse"  style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div></div>';

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

                    results.removeClass("in").attr("aria-expanded", "false").css({"height": "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function (element) {
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
            this.hideEmpty = edges.getParam(params.hideEmpty, false)

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
                        if (val.count === 0 && this.hideEmpty) {
                            continue
                        }
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
                var frag = '<div class="accordion"><h3 class="label label--secondary filter__heading" id="' + toggleId + '"><button class="aria-button" aria-expanded="false">' + this.component.display + toggle + '</button></h3>\
                    <div class="filter__body collapse" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div></div>';

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

                    results.removeClass("in").attr("aria-expanded", "false").css({"height": "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

            this.filterToggle = function (element) {
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
                                filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" data-value="' + val.val + '" data-value-idx="' + j + '" alt="Remove" title="Remove">';
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
                var sf = this.component;

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
                    let values = sf.mustFilters[field].values;
                    let idx = el.attr("data-value-idx")
                    value = values[idx].val
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

            this.clearFilters = function () {
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

        newPublicSearchResultRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PublicSearchResultRenderer, params, edges.newRenderer);
        },
        PublicSearchResultRenderer: function (params) {

            this.widget = params.widget;
            if (params.doaj_url) {
                this.doaj_url = params.doaj_url;
            } else {
                this.doaj_url = ""
            }

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-public-search";

            this.selector = edges.getParam(params.selector, null)
            this.currentQueryString = "";


            this.draw = function () {
                if (this.component.edge.currentQuery) {
                    let qs = this.component.edge.currentQuery.getQueryString();
                    if (qs) {
                        this.currentQueryString = qs.queryString || "";
                    }
                }
                var frag = "<li class='alert'><p>You searched for ‘<i>";
                frag += edges.escapeHtml(this.currentQueryString);
                frag += "</i>’ and we found no results.</p>";
                frag += "<p>Please try the following:</p><ul>\
                    <li>Check the spelling and make sure that there are no missing characters.</li>\
                    <li>Use fewer words in your search to make the search less specific.</li>\
                    <li>Remove some of the filters you have set.</li>\
                    <li>Do your search again in English as much of the index uses English terms.</li>\
                    </ul></li>\
                ";

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

            this.toggleAbstract = function (element) {
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

            this._renderResult = function (resultobj) {
                if (resultobj.bibjson && resultobj.bibjson.journal) {
                    // it is an article
                    return this._renderPublicArticle(resultobj);
                } else {
                    // it is a journal
                    return this._renderPublicJournal(resultobj);
                }
            };

            this._renderPublicJournal = function (resultobj) {

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
                    subjects = '<h4>Journal subjects</h4><ul class="inlined-list">';
                    subjects += "<li>" + resultobj.index.classification_paths.join(",&nbsp;</li><li>") + "</li>";
                    subjects += '</ul>';
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

                let apc_frag = "<strong>No</strong> APC";
                let other_charges_frag = "<strong>No</strong> other charges";
                if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                    apc_frag = "APCs: ";
                    let length = resultobj.bibjson.apc.max.length;
                    for (var i = 0; i < length; i++) {
                        apc_frag += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apc_frag += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apc_frag += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        if (i < length - 1) {
                            apc_frag += ', ';
                        }
                        apc_frag += "</strong>";
                    }
                }
                if (edges.hasProp(resultobj,"bibjson.other_charges.has_other_charges") && resultobj.bibjson.other_charges.has_other_charges) {
                    other_charges_frag = "Has other charges";
                }
                let charges = `<li>${apc_frag}; ${other_charges_frag}</li>`;

                var rights = "";
                if (resultobj.bibjson.copyright) {
                    var copyright_url = resultobj.bibjson.copyright.url;
                    rights += '<a href="' + copyright_url + '" target="_blank" rel="noopener">';
                    rights += resultobj.bibjson.copyright.author_retains ? 'Author <strong> retains </strong> all rights' : 'Author <strong> doesn\'t retain </strong> all rights';
                    rights += '</a>';
                }


                var licenses = "";
                if (resultobj.bibjson.license && resultobj.bibjson.license.length > 0) {
                    var terms_url = resultobj.bibjson.ref.license_terms;
                    for (var i = 0; i < resultobj.bibjson.license.length; i++) {
                        var lic = resultobj.bibjson.license[i];
                        var license_url = lic.url || terms_url;
                        licenses += '<a href="' + license_url + '" target="_blank" rel="noopener">' + edges.escapeHtml(lic.type) + '</a>';
                        if (i !== (resultobj.bibjson.license.length - 1)) {
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
                var modals = "";
                if (this.actions.length > 0) {
                    actions = '<h4 class="label">Actions</h4><ul class="tags">';
                    for (var i = 0; i < this.actions.length; i++) {
                        var act = this.actions[i];
                        var actSettings = act(resultobj);
                        if (actSettings) {
                            let data = "";
                            if (actSettings.data) {
                                let dataAttrs = Object.keys(actSettings.data);
                                for (let j = 0; j < dataAttrs.length; j++) {
                                    data += " data-" + dataAttrs[j] + "=" + actSettings.data[dataAttrs[j]];
                                }
                            }
                            actions += '<li class="tag">\
                                <a href="' + actSettings.link + '" tabindex="0" role="button" ' + data + '>' + actSettings.label + '</a>\
                            </li>';
                            if (actSettings.modal) {
                                modals += actSettings.modal
                            }
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
                if (this.widget) {
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/link.svg" alt="link icon">'
                } else {
                    frag += '<i data-feather="link" aria-hidden="true"></i>'
                }


                let externalLink = "";
                if (resultobj.bibjson.ref && resultobj.bibjson.ref.journal) {
                    externalLink = '<li><a href="' + resultobj.bibjson.ref.journal + '" target="_blank" rel="noopener">Website ';

                    if (this.widget) {
                        externalLink += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                    } else {
                        externalLink += '<i data-feather="external-link" aria-hidden="true"></i>'
                    }

                    externalLink += '</a></li>';
                }

                let s2o = "";
                if (resultobj.bibjson.labels && resultobj.bibjson.labels.includes("s2o")) {
                    s2o = '<a href="https://subscribetoopencommunity.org/" id="s2o" target="_blank">' +
                        '<img src="/assets/img/labels/s2o-minimalistic.svg" width="50" alt="Subscribe to Open" title="Subscribe to Open">' +
                        '<p class="sr-only">This journal is part of the Subscribe to Open program.</p>' +
                        '</a>';
                }

                frag +=`</sup>
                            </a>
                            ` + subtitle + `
                          </h3>
                        </header>
                        <div class="search-results__body">
                          <ul class="inlined-list">
                            <li>
                              ` + published + `
                            </li>
                            ` + language + `
                          </ul>
                          ` + subjects + `
                        </div>
                      </div>
                      <aside class="col-sm-4 search-results__aside">
                        <ul>
                          <li>
                            ` + update_or_added + `
                          </li>
                          ` + articles + `
                          ` + externalLink + `
                        <li>
                            ` + charges + `
                          </li>
                          <li>
                            ` + rights + `
                          </li>
                          <li>
                            ` + licenses + `
                          </li>
                          <li class="badges badges--search-result badges--search-result--public">
                          ${s2o}
                          </li>
                        </ul>
                        ` + actions + modals + `
                      </aside>
                    </article>
                  </li>`;

                return frag;
            };

            this._renderPublicArticle = function (resultobj) {
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
                    keywords += '<li>' + resultobj.bibjson.keywords.join(",&nbsp;</li><li>") + '</li>';
                    keywords += '</ul>';
                }

                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = '<h4>Journal subjects</h4><ul class="inlined-list">';
                    subjects += "<li>" + resultobj.index.classification_paths.join(",&nbsp;</li><li>") + "</li>";
                    subjects += '</ul>';
                }

                var subjects_or_keywords = keywords === "" ? subjects : keywords;

                var abstract = "";
                if (resultobj.bibjson.abstract) {
                    var abstractAction = edges.css_classes(this.namespace, "abstractaction", this);
                    var abstractText = edges.css_classes(this.namespace, "abstracttext", this);

                    abstract = '<h4 class="' + abstractAction + '" type="button" aria-expanded="false" rel="' + resultobj.id + '">\
                            Abstract'
                    if (this.widget) {
                        abstract += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/plus.svg" alt="external-link icon">'
                    } else {
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

                const export_url = this.doaj_url + '/service/export/article/' + resultobj.id + '/ris';

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
                if (this.widget) {
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                } else {
                    frag += '<i data-feather="external-link" aria-hidden="true"></i>'
                }
                frag += '</a></li>\
                         <li>\
                            <a href="' + export_url + '" target="_blank">\
                            Export citation (RIS) '
                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/download.svg" alt="external-link icon">'
                } else {
                    frag += '<i data-feather="download" aria-hidden="true"></i>'
                }
                            frag += '</a>\
                          </li>\
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

        newPublisherApplicationRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PublisherApplicationRenderer, params, edges.newRenderer);
        },
        PublisherApplicationRenderer: function (params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-application";

            this.statusMap = {
                "draft": "Not yet submitted",
                "accepted": "Accepted to DOAJ",
                "rejected": "Application rejected",
                "update_request": "Pending",
                "revisions_required": "Revisions Required",
                "pending": "Pending",
                "in progress": "Under review by an editor",
                "completed": "Under review by an editor",
                "on hold": "Under review by an editor",
                "ready": "Under review by an editor"
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
                            <header class="flex-space-between modal__heading"> \
                                <h2 class="modal__title">Delete this application</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
                            <p>Are you sure you want to delete your application for <strong><span class="' + deleteTitleClass + '"></span></strong>?</p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--tertiary" data-dismiss="modal" class="modal__close">No</button>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
            };

            this.deleteLinkClicked = function (element) {
                var deleteTitleSelector = edges.css_class_selector(this.namespace, "delete-title", this);
                var deleteLinkSelector = edges.css_class_selector(this.namespace, "delete-link", this);

                var el = $(element);
                var href = el.attr("href");
                var title = el.attr("data-title");

                this.component.jq(deleteTitleSelector).html(title);
                this.component.jq(deleteLinkSelector).attr("href", href);
            };

            this._accessLink = function (resultobj) {
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

            this._renderResult = function (resultobj) {

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

        newPublisherUpdateRequestRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PublisherUpdateRequestRenderer, params, edges.newRenderer);
        },
        PublisherUpdateRequestRenderer: function (params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-update-request";

            this.statusMap = {
                "accepted": "Accepted to DOAJ",
                "rejected": "Application rejected",
                "update_request": "Pending",
                "revisions_required": "Revisions Required",
                "pending": "Pending",
                "in progress": "Under review by an editor",
                "completed": "Under review by an editor",
                "on hold": "Under review by an editor",
                "ready": "Under review by an editor",
                "post_submission_review": "Pending"
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
                            <header class="flex-space-between modal__heading">\
                              <h2 class="modal__title">Delete this update request</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
                            <p>Are you sure you want to delete your update request for <strong><span class="' + deleteTitleClass + '"></span></strong>?</p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--tertiary" data-dismiss="modal" class="modal__close">No</button>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
            };

            this._renderResult = function (resultobj) {
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
                last_updated += doaj.humanDate(resultobj.last_manual_update);

                var deleteLink = "";
                var deleteLinkTemplate = doaj.publisherUpdatesSearchConfig.deleteLinkTemplate;
                var deleteLinkUrl = deleteLinkTemplate.replace("__application_id__", resultobj.id);
                var deleteClass = edges.css_classes(this.namespace, "delete", this);
                if (resultobj.es_type === "draft_application" ||
                    resultobj.admin.application_status === "update_request" ||
                    resultobj.admin.application_status === "post_submission_review") {
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

            this.deleteLinkClicked = function (element) {
                var deleteTitleSelector = edges.css_class_selector(this.namespace, "delete-title", this);
                var deleteLinkSelector = edges.css_class_selector(this.namespace, "delete-link", this);

                var el = $(element);
                var href = el.attr("href");
                var title = el.attr("data-title");

                this.component.jq(deleteTitleSelector).html(title);
                this.component.jq(deleteLinkSelector).attr("href", href);
            };

            this._accessLink = function (resultobj) {
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
                    subjects = '<h4>Journal subjects</h4><ul class="inlined-list">';
                    subjects += "<li>" + resultobj.index.classification_paths.join(",&nbsp;</li><li>") + "</li>";
                    subjects += '</ul>';
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
                        <select name="' + selectName + '" class="form-control input-sm ' + sortFieldClass + '" id="' + selectName + '">';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        var dir = comp.sortOptions[i].dir;
                        if (dir === undefined) {
                            dir = "";
                        }
                        if (dir !== "") {
                            dir = " " + dir;
                        }
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
        titleField: function (val, resultobj, renderer) {
            var field = '<div class="flex-start flex-space-between flex-wrap"><h3 class="type-01 font-serif" >';
            if (resultobj.bibjson.title) {
                if (resultobj.es_type === "journal") {
                    var display = edges.escapeHtml(resultobj.bibjson.title);
                    if (resultobj.admin.in_doaj) {
                        display = "<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + display + "</a>";
                    }
                    field += display;
                } else {
                    field += edges.escapeHtml(resultobj.bibjson.title);
                }
                field += "</h3>";

                var s2o = '';
                if (resultobj.bibjson.labels && resultobj.bibjson.labels.includes("s2o")) {
                    s2o = s2o = '<a href="https://subscribetoopencommunity.org/" id="s2o" target="_blank" style="padding: .25rem;"> ' +
                        '<img src="/assets/img/labels/s2o-minimalistic.svg" width="50" alt="Subscribe to Open" title="Subscribe to Open">' +
                        '<p class="sr-only">This journal is part of the Subscribe to Open program.</p>' +
                        '</a>';;
                }

                if (s2o) {
                    field += '<div class="badges badges--search-result badges--search-result--maned">' + s2o + '</div>';
                }
                return field + "</div>";
            }
            else {
                return false;
            }
        },

        authorPays: function (val, resultobj, renderer) {
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
            } else {
                return false;
            }
        },

        abstract: function (val, resultobj, renderer) {
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

        journalLicense: function (val, resultobj, renderer) {
            var titles = [];
            if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
                var lics = resultobj["bibjson"]["journal"]["license"];
                var titles = lics.map(function (x) {
                    return x.type
                });
            } else if (resultobj.bibjson && resultobj.bibjson.license) {
                var lics = resultobj["bibjson"]["license"];
                titles = lics.map(function (x) {
                    return x.type
                });
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

        doiLink: function (val, resultobj, renderer) {
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

        links: function (val, resultobj, renderer) {
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

        issns: function (val, resultobj, renderer) {
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

        countryName: function (val, resultobj, renderer) {
            if (resultobj.index && resultobj.index.country) {
                return edges.escapeHtml(resultobj.index.country);
            }
            return false
        },

        inDoaj: function (val, resultobj, renderer) {
            var mapping = {
                "false": {"text": "No", "class": "red"},
                "true": {"text": "Yes", "class": "green"}
            };
            var field = "";
            if (resultobj.admin && resultobj.admin.in_doaj !== undefined) {
                if (mapping[resultobj['admin']['in_doaj']]) {
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

        owner: function (val, resultobj, renderer) {
            if (resultobj.admin && resultobj.admin.owner !== undefined && resultobj.admin.owner !== "") {
                var own = resultobj.admin.owner;
                return '<a href="/account/' + own + '">' + edges.escapeHtml(own) + '</a>'
            }
            return false
        },

        createdDateWithTime: function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['created_date']);
        },

        lastManualUpdate: function (val, resultobj, renderer) {
            var man_update = resultobj['last_manual_update'];
            if (man_update === '1970-01-01T00:00:00Z') {
                return 'Never'
            } else {
                return doaj.iso_datetime2date_and_time(man_update);
            }
        },

        suggestedOn: function (val, resultobj, renderer) {
            if (resultobj && resultobj['admin'] && resultobj['admin']['date_applied']) {
                return doaj.iso_datetime2date_and_time(resultobj['admin']['date_applied']);
            } else {
                return false;
            }
        },

        applicationStatus: function (val, resultobj, renderer) {
            return doaj.valueMaps.applicationStatus[resultobj['admin']['application_status']];
        },

        editSuggestion: function (params) {
            return function (val, resultobj, renderer) {
                if (resultobj.es_type === "application") {
                    // determine the link name
                    var linkName = "Review application";
                    if (resultobj.admin.application_type === "new_application") {
                        if (resultobj.admin.application_status === 'accepted' || resultobj.admin.application_status === 'rejected') {
                            linkName = "View application (finished)"
                        } else {
                            linkName = "Review application"
                        }
                    } else {
                        if (resultobj.admin.application_status === 'accepted' || resultobj.admin.application_status === 'rejected') {
                            linkName = "View update (finished)"
                        } else {
                            linkName = "Review update"
                        }
                    }

                    var result = '<p><a class="edit_suggestion_link button" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += ' style="margin-bottom: .75em;">' + linkName + '</a></p>';
                    return result;
                }
                return false;
            }
        },

        readOnlyJournal: function (params) {
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

        editJournal: function (params) {
            return function (val, resultobj, renderer) {
                if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                    // if it's not a suggestion or an article .. (it's a
                    // journal!)
                    // we really need to expose _type ...
                    var result = '<p><a class="edit_journal_link button" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += ' style="margin-bottom: .75em;">Edit this journal</a></p>';
                    return result;
                }
                return false;
            }
        },
    },

    bulk: {
        applicationMultiFormBox: function (edge_instance, doaj_type) {
            return doaj.multiFormBox.newMultiFormBox({
                edge: edge_instance,
                selector: "#admin-bulk-box",
                bindings: {
                    editor_group: function (context) {
                        autocomplete($('#editor_group', context), 'name', 'editor_group', 1, false);
                    }
                },
                validators: {
                    application_status: function (context) {
                        var val = context.find("#application_status").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    editor_group: function (context) {
                        var val = context.find("#editor_group").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    note: function (context) {
                        var val = context.find("#note").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    }
                },
                submit: {
                    note: {
                        data: function (context) {
                            return {
                                note: $('#note', context).val()
                            };
                        }
                    },
                    editor_group: {
                        data: function (context) {
                            return {
                                editor_group: $('#editor_group', context).val()
                            };
                        }
                    },
                    application_status: {
                        data: function (context) {
                            return {
                                application_status: $('#application_status', context).val()
                            };
                        }
                    }
                },
                urls: {
                    note: "/admin/" + doaj_type + "/bulk/add_note",
                    editor_group: "/admin/" + doaj_type + "/bulk/assign_editor_group",
                    application_status: "/admin/" + doaj_type + "/bulk/change_status"
                }
            });
        }
    }

});
