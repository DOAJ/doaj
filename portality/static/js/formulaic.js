var formulaic = {

    newFormulaic: function (params) {
        return edges.instantiate(formulaic.Formulaic, params);
    },
    Formulaic: function (params) {
        // Construction Arguments
        ///////////////////////////////////////////////////////

        // jquery selector for the form we're working with
        this.formSelector = edges.getParam(params.formSelector, "#formulaic");

        // the fieldsets configuration for this form
        this.fieldsets = edges.getParam(params.fieldsets, {});

        // a mapping from short strings to function paths for the functions used by this form
        this.functions = edges.getParam(params.functions, {});

        // should we apply front-end validation
        this.doValidation = edges.getParam(params.doValidation, true);

        // should we autosave?  Enter 0 for no, or the number of milliseconds between each save
        this.autoSave = edges.getParam(params.autoSave, 0);

        this.controlSelect = edges.getParam(params.controlSelect, formulaic.newDefaultControlSelect());
        this.controlSelect.set_formuaic(this);

        // Internal properties
        ///////////////////////////////////////////////////////

        // jquery handle on the form
        this.context = $(this.formSelector);

        // list of fields whose values are synchronised
        this.synchronised = {};

        // an inverted map of conditionals: keys are fields which are conditions of other fields
        this.conditionals = {};

        // internal variable for holding reference to the parsley validator for the form
        this.activeParsley = false;

        // hold references to widgets that we have loaded
        this.widgetRefs = {};

        // hold references to instantiated widgets
        this.activeWidgets = {};

        // references to exclusive checkboxes
        this.exclusive = {};

        this.lastSaveVal = "";

        /**
         * Construct the Formulaic instance
         */
        this.init = function () {
            // set up the save button
            this.bindSave();

            // first detect any sychronised fields and register them
            this.registerSynchronised();

            // bind any conditional fields
            this.bindConditional();

            // attach any widgets to the form
            this.applyWidgets();

            // find any checkboxes that
            this.bindExclusiveCheckboxes();

            // Note that we don't bind parsley validation on init, because we don't want to
            // always validate.  Instead Parsley is inited later when the user attempts an initial
            // submit
        };

        // Object utility functions
        ////////////////////////////////////////////////

        /*
        this._controlSelect = function(params) {
            var context = this.context;
            if (params.fieldset) {
                context = $("#" + params.fieldset, this.context);
            }
            if (params.name) {
                return $("[name=" + params.name + "], [data-formulaic-sync=" + params.name + "]", context).filter(":input");
            } else if (params.id) {
                return $("#" + params.id, context).filter(":input");
            } else if (params.syncName) {
                return $("[data-formulaic-sync=" + params.syncName + "]", context).filter(":input");
            }
        };*/

        this.getElementName = function (element) {
            var name = element.attr("data-formulaic-sync");
            if (!name) {
                name = element.attr("name");
            }
            return name;
        };

        this.getFieldDefinition = function (params) {
            var field = params.field;

            for (var i = 0; i < this.fieldsets.length; i++) {
                var fieldset = this.fieldsets[i];
                for (var j = 0; j < fieldset.fields.length; j++) {
                    var fieldDef = fieldset.fields[j];
                    if (fieldDef.name === field) {
                        return fieldDef;
                    }
                }
            }

            return false;
        };

        ////////////////////////////////////////////////

        //////////////////////////////////////////////
        // Functions for handling save

        this.bindSave = function () {
            edges.on(this.context.find(".formulaic-complete"), "click.Complete", this, "saveComplete", false, false, false);
            edges.on(this.context.find(".formulaic-draft"), "click.Draft", this, "saveDraftAndComplete", false, false, false);

            if (this.autoSave > 0) {
                setTimeout(this.backgroundSaveClosure(), this.autoSave);
            }
        };

        this.backgroundSaveClosure = function () {
            var that = this;
            return function () {
                that.save({validate: false, additional: {"draft": "true", "async": "true"}, complete: false});
                setTimeout(that.backgroundSaveClosure(), that.autoSave);
            };
        };

        this.saveComplete = function (element, event) {
            this.save({event: event});
        };

        this.saveDraftAndComplete = function (element, event) {
            this.save({validate: false, additional: {"draft": "true", "async": "true"}, event: event});
        };

        this.save = function (params) {
            if (!params) {
                params = {};
            }
            var validate = edges.getParam(params.validate, this.doValidation);
            var additional_params = edges.getParam(params.additional, {});
            var complete = edges.getParam(params.complete, true);
            var event = params.event;

            if (validate) {
                this.bounceParsley();
            } else {
                this.destroyParsley();
            }

            if (!validate || (this.activeParsley && this.activeParsley.isValid())) {
                if (!complete) {
                    if (event) {
                        event.preventDefault();
                    }
                    var submit_data = this.context.serialize();
                    if (submit_data === this.lastSaveVal) {
                        return;
                    }
                    var full_data = $.param(additional_params) + "&" + submit_data;
                    var that = this;
                    $.post({
                        url: this.context.attr("action"),
                        data: full_data,
                        error: function () {/*alert("background save failed")*/
                        },
                        success: function (response_data) {
                            that.lastSaveVal = submit_data;
                            var rd = JSON.parse(response_data);
                            that.setId(rd);
                        }
                    });
                }
                // otherwise, event propagates and form is submitted by the browser
            } else {
                if (event) {
                    event.preventDefault();
                }
                if (this.activeParsley) {
                    this.activeParsley.validate();
                }
            }
        };

        this.setId = function (params) {
            var id = params.id;
            var existing = this.context.find("[name=id]");
            if (existing.length > 0) {
                existing.attr("value", id);
            } else {
                this.context.append('<input type="hidden" name="id" value="' + id + '">');
            }
        };

        /////////////////////////////////////////////////////

        /////////////////////////////////////////////////////
        // Functions for handling synchronised fields

        this.registerSynchronised = function () {
            var fieldRegister = [];
            for (var i = 0; i < this.fieldsets.length; i++) {
                var fieldset = this.fieldsets[i];
                for (var j = 0; j < fieldset.fields.length; j++) {
                    var field = fieldset.fields[j];
                    if ($.inArray(field.name, fieldRegister) === -1) {
                        fieldRegister.push(field.name);
                    } else {
                        if ($.inArray(field.name, Object.keys(this.synchronised)) === -1) {
                            this.synchronised[field.name] = [fieldset.name];
                        } else {
                            this.synchronised[field.name].push(fieldset.name);
                        }
                    }
                }
            }

            var fields = Object.keys(this.synchronised);
            for (var i = 0; i < fields.length; i++) {
                var name = fields[i];
                var allByName = this.controlSelect.input({name: name});
                allByName.each(function () {
                    var that = $(this);
                    var current_id = that.attr("id");
                    that.attr("data-formulaic-sync", name).attr("data-formulaic-id", current_id);
                });

                var fieldsets = this.synchronised[name];
                for (var j = 0; j < fieldsets.length; j++) {
                    var fieldset = fieldsets[j];
                    var elements = this.controlSelect.input({fieldset: fieldset, name: name});
                    elements.each(function () {
                        var newname = fieldset + "__" + name;
                        var newid = fieldset + "__" + $(this).attr("id");
                        $(this).attr("name", newname).attr("id", newid);
                    });
                }

                edges.on(allByName, "change.Synchronise", this, "synchroniseChange");
            }
        };

        this.synchroniseChange = function (element) {
            var that = $(element);
            var name = that.attr("data-formulaic-sync");
            var original_id = that.attr("data-formulaic-id");
            var type = that.attr("type");

            // TODO: we currently only synchronise radio and checkboxes, so if you need to synchronise
            // other fields, this will need extending
            if (type === "radio" || type === "checkbox") {
                var checked = that.is(":checked");
                var toSync = this.controlSelect.input({syncName: name});
                toSync.each(function () {
                    var el = $(this);
                    if (el.attr("data-formulaic-id") === original_id) {
                        el.prop("checked", checked);
                    } else {
                        el.prop("checked", !checked);
                    }
                });
            }
        };

        ///////////////////////////////////////////////////////

        // Functions for conditional fields
        ///////////////////////////////////////////////////////

        this.bindConditional = function () {
            for (var i = 0; i < this.fieldsets.length; i++) {
                var fieldset = this.fieldsets[i];
                for (var j = 0; j < fieldset.fields.length; j++) {
                    var field = fieldset.fields[j];

                    if (!field.hasOwnProperty("conditional")) {
                        continue;
                    }

                    for (var k = 0; k < field.conditional.length; k++) {
                        var condition = field.conditional[k];
                        var condField = condition.field;

                        // register the conditional relationship
                        if (this.conditionals.hasOwnProperty(condField)) {
                            if ($.inArray(field, this.conditionals[condField]) === -1) {
                                this.conditionals[condField].push(field.name);
                            }
                        } else {
                            this.conditionals[condField] = [field.name];
                        }

                        // bind a change event for checking conditionals
                        var element = this.controlSelect.input({name: condField});
                        edges.on(element, "change.Conditional", this, "checkConditional");

                        // then actually check the conditional
                        this.checkConditional(element);
                    }
                }
            }
        };

        this.checkConditional = function (element) {
            var name = this.getElementName($(element));
            var downstream = this.conditionals[name];
            for (var i = 0; i < downstream.length; i++) {
                var field = downstream[i];
                if (this.isConditionSatisfied({field: field})) {
                    this.controlSelect.container({name: field}).show();
                } else {
                    this.removeValues(this.controlSelect.container({name: field}));
                    this.controlSelect.container({name: field}).hide();
                }
            }
        };

        this.removeValues = (container) => {
            let inputs = $(container).find("input");
            inputs.each((idx, inp) => {
                let el = $(inp);
                let type = el.attr("type");
                if (type === "checkbox" || type === "radio") {
                    el.prop("checked", false);
                } else {
                    el.val("");
                }
            });
            let selects = $(container).find("select");
            selects.each((idx, sel) => {
                $(sel).val("").change();
            });
        };

        this.isConditionSatisfied = function (params) {
            var field = params.field;
            var definition = this.getFieldDefinition(params);
            for (var i = 0; i < definition.conditional.length; i++) {
                var condField = definition.conditional[i];
                var elements = this.controlSelect.input({name: condField.field});
                var type = elements.attr("type");
                var val = condField.value;

                if (type === "radio" || type === "checkbox") {
                    var checkedValues = [];
                    elements.each(function () {
                        var that = $(this);
                        if (that.is(":checked")) {
                            checkedValues.push(that.val());
                        }
                    });
                    if ($.inArray(val, checkedValues) !== -1) {
                        return true;
                    }
                }
            }
            return false;
        };

        ///////////////////////////////////////////////////////

        // Functions for widget handling
        ///////////////////////////////////////////////////////

        this.applyWidgets = function () {
            for (var i = 0; i < this.fieldsets.length; i++) {
                var fieldset = this.fieldsets[i];
                for (var j = 0; j < fieldset.fields.length; j++) {
                    var fieldDef = fieldset.fields[j];
                    if (fieldDef.hasOwnProperty("widgets")) {
                        for (var k = 0; k < fieldDef.widgets.length; k++) {
                            var widgetDef = fieldDef.widgets[k];

                            var widgetName = false;
                            var widgetArgs = {};
                            if (typeof widgetDef === "string") {
                                widgetName = widgetDef
                            } else {
                                widgetName = Object.keys(widgetDef)[0];
                                widgetArgs = widgetDef[widgetName];
                            }

                            var widget = this.getWidget(widgetName);
                            if (!widget) {
                                continue;
                            }
                            var active = widget({
                                fieldDef: fieldDef,
                                formulaic: this,
                                args: widgetArgs
                            });

                            if (this.activeWidgets.hasOwnProperty(fieldDef.name)) {
                                this.activeWidgets[fieldDef.name].push(active);
                            } else {
                                this.activeWidgets[fieldDef.name] = [active]
                            }

                        }
                    }
                }
            }
        };

        this.getWidget = function (widgetName) {
            if (this.widgetRefs[widgetName]) {
                return this.widgetRefs[widgetName];
            }

            var functionPath = this.functions[widgetName];
            if (!functionPath) {
                return false;
            }

            var bits = functionPath.split(".");
            var context = window;
            for (var i = 0; i < bits.length; i++) {
                var bit = bits[i];
                context = context[bit];
                if (!context) {
                    console.log("Unable to load " + widgetName + " from path " + functionPath);
                    return false;
                }
            }
            return context;
        };

        //////////////////////////////////////////////////////

        // Functions for exclusive checkboxes
        //////////////////////////////////////////////////////

        this.bindExclusiveCheckboxes = function () {
            // first register all the exclusive elements and values
            for (var i = 0; i < this.fieldsets.length; i++) {
                var fieldset = this.fieldsets[i];
                for (var j = 0; j < fieldset.fields.length; j++) {
                    var field = fieldset.fields[j];
                    if (field.hasOwnProperty("options")) {
                        for (var k = 0; k < field.options.length; k++) {
                            var opt = field.options[k];
                            if (opt.hasOwnProperty("exclusive") && opt.exclusive) {
                                if (this.exclusive.hasOwnProperty(field.name)) {
                                    if ($.inArray(opt.value, this.exclusive) === -1) {
                                        this.exclusive[field.name].push(opt.value);
                                    }
                                } else {
                                    this.exclusive[field.name] = [opt.value];
                                }
                            }
                        }
                    }
                }
            }

            var exclusiveFields = Object.keys(this.exclusive);
            for (var i = 0; i < exclusiveFields.length; i++) {
                var name = exclusiveFields[i];
                var elements = this.controlSelect.input({name: name});
                edges.on(elements, "change.Exclusive", this, "checkExclusive");
                for (var j = 0; j < elements.length; j++) {
                    this.checkExclusive(elements[j]);
                }
            }
        };

        this.checkExclusive = function (element) {
            var jqel = $(element);
            var name = jqel.attr("name");
            var value = jqel.val();

            if (!this.exclusive.hasOwnProperty(name)) {
                return;
            }
            var values = this.exclusive[name];
            if ($.inArray(value, values) === -1) {
                return;
            }

            var checked = jqel.is(":checked");
            var elements = this.controlSelect.input({name: name});
            var that = this;
            elements.each(function () {
                if (checked && $(this).val() !== value) {
                    $(this).prop("checked", false);
                    $(this).prop('disabled', true);
                    that.checkConditional(this);
                } else {
                    $(this).prop('disabled', false);
                }
            });
        };

        ////////////////////////////////////////////////////

        // Parsley state management
        ////////////////////////////////////////////////////

        this.destroyParsley = function () {
            if (!this.doValidation) {
                return;
            }
            if (this.activeParsley) {
                this.activeParsley.destroy();
                this.activeParsley = false;
                this.context.off("submit.Parsley");
            }
            // $(".has-error").removeClass("has-error");
        };

        this.bounceParsley = function () {
            if (!this.doValidation) {
                return;
            }
            this.destroyParsley();
            this.activeParsley = this.context.parsley();
        };

        ////////////////////////////////////////////////////

        // call the init  function to complete construction
        this.init();
    },

    newDefaultControlSelect: function (params) {
        return edges.instantiate(formulaic.DefaultControlSelect, params);
    },
    DefaultControlSelect: function (params) {
        this.containerClassTemplate = edges.getParam(params.containerClassTemplate, "{name}__container");

        this.groupSeparator = edges.getParam(params.groupSeparator, "-");

        this.formulaic = false;

        this.set_formuaic = function (f) {
            this.formulaic = f;
        };

        this.get_context = function (params) {
            var context = this.formulaic.context;
            if (params.fieldset) {
                context = $("#" + params.fieldset, context);
            }
            return context;
        };

        this.localiseName = function (params) {
            var name = params.name;
            var def = this.formulaic.getFieldDefinition({field: name});
            if (def.hasOwnProperty("group")) {
                var upperChain = this.localiseName({name: def.group});
                return upperChain + this.groupSeparator + name;
            } else {
                return name;
            }
        };

        this.input = function (params) {
            var context = this.get_context(params);
            if (params.name) {
                var name = this.localiseName({name: params.name});
                return $("[name=" + name + "], [data-formulaic-sync=" + name + "]", context).filter(":input");
            } else if (params.id) {
                return $("#" + params.id, context).filter(":input");
            } else if (params.syncName) {
            } else if (params.syncName) {
                return $("[data-formulaic-sync=" + params.syncName + "]", context).filter(":input");
            }
        };

        this.container = function (params) {
            var context = this.get_context(params);
            var name = params.name || params.syncName;
            var selector = "." + this.containerClassTemplate.replace("{name}", name);
            return $(selector, context);
        };

        this.widgetsContainer = function (params) {
            var context = this.get_context(params);
            return $("#" + params.name + "_widgets-container", context)
        }
    },

    edges: {
        newTreeBrowser: function (params) {
            return edges.instantiate(formulaic.edges.TreeBrowserForm, params, edges.newTreeBrowserCore);
        },
        TreeBrowserForm: function (params) {
            this.sourceInput = edges.getParam(params.sourceInput, false);
            this.selected = [];

            this.init = function (edge) {
                // first kick the request up to the superclass
                edges.newTreeBrowserCore().init.call(this, edge);

                // sourceInput can be false
                // this is specific for the form, not the TreeBrowser itself
                var text = this.sourceInput.val();
                if (text !== "") {
                    this.selected = text.split(",").map(function (x) {
                        return x.trim()
                    })
                } else {
                    this.selected = [];
                }
            };

            this.synchronise = function () {
                this.syncTree = $.extend(true, [], this.tree);
                var selected = this.selected;
                var that = this;

                var processNode = function (node) {
                    node.index = that.nodeIndex ? that.nodeIndex(node) : node.display;
                    if (that.filterMatch(node, selected)) {
                        node.selected = true;
                        anySelected = true;
                        return true;
                    }
                    return false;
                };

                var path = [];
                this.baseRecurse(this.syncTree, path, processNode);
            };

            this.addFilter = function (params) {
                var value = params.value;
                var parents = this.parentIndex[value];
                var terms = [params.value];
                var clearOthers = edges.getParam(params.clearOthers, false);

                var newValues = $.extend(true, [], this.selected);

                // if there is, just add the term to it (removing and parent terms along the way)
                if (newValues.length > 0) {
                    newValues.sort();

                    // if this is an exclusive filter that clears all others, just do that
                    if (clearOthers) {
                        newValues = [];
                    }

                    // next, if there are any terms left, remove all the parent terms
                    for (var i = 0; i < parents.length; i++) {
                        var parent = parents[i];
                        var location = $.inArray(parent, newValues);
                        if (location !== -1) {
                            newValues.splice(location, 1);
                        }
                    }

                    // now add all the provided terms
                    var hadTermAlready = 0;
                    for (var i = 0; i < terms.length; i++) {
                        var term = terms[i];
                        if ($.inArray(term, newValues) !== -1) {
                            hadTermAlready++;
                        } else {
                            newValues.push(term);
                        }
                    }
                } else {
                    newValues = terms;
                }

                // store the new values on the object and in the form
                this.selected = newValues;
                this.sourceInput.val(newValues.join(","));
                this.sourceInput.trigger("change");
                this.edge.cycle();
                return true;
            };

            this.removeFilter = function (params) {
                var term = params.value;

                var newValues = $.extend(true, [], this.selected);

                if (newValues.length > 0) {
                    var location = $.inArray(term, newValues);
                    if (location !== -1) {
                        // the filter we are being asked to remove is the actual selected one
                        newValues.splice(location, 1);
                    } else {
                        // the filter we are being asked to remove may be a parent of the actual selected one
                        // first get all the parent sets of the values that are currently in force
                        var removes = [];
                        for (var i = 0; i < newValues.length; i++) {
                            var val = newValues[i];
                            var parentSet = this.parentIndex[val];
                            if ($.inArray(term, parentSet) > -1) {
                                removes.push(val);
                            }
                        }
                        for (var i = 0; i < removes.length; i++) {
                            var location = $.inArray(removes[i], newValues);
                            if (location !== -1) {
                                newValues.splice(location, 1);
                            }
                        }
                    }

                    var grandparents = this.parentIndex[term];
                    if (grandparents.length > 0) {
                        var immediate = grandparents[grandparents.length - 1];
                        var sharedParent = false;
                        for (var i = 0; i < newValues.length; i++) {
                            var aunts = this.parentIndex[newValues[i]];
                            if (aunts.length > 0 && aunts[aunts.length - 1] === immediate) {
                                sharedParent = true;
                                break;
                            }
                        }
                        if (!sharedParent && $.inArray(immediate, newValues) === -1) {
                            newValues.push(immediate);
                        }
                    }
                }

                // reset the search page to the start and then trigger the next query
                // store the new values on the object and in the form
                this.selected = newValues;
                this.sourceInput.val(newValues.join(","));
                this.sourceInput.trigger("change");
                this.edge.cycle();
            };
        }
    },

    widgets: {
        _select2_shift_focus: function () {
            let id = $(this).attr("id");
            console.log("focused on " + id);
            let select2_elem = $("#s2id_" + id).find("input");
            $(select2_elem).focus();
        },

        _make_empty_container: function (namespace, containerName, form, fieldDef, additionalClasses, additionalStyles) {
            if (!additionalClasses) {
                additionalClasses = "";
            }
            if (!additionalStyles) {
                additionalStyles = "";
            }

            let containerSelector = edges.css_class_selector(namespace, containerName);
            let elements = form.controlSelect.widgetsContainer({name: fieldDef.name});
            let existing = false;
            for (let i = 0; i < elements.length; i++) {
                let el = $(elements[i]);
                let cont = el.find(containerSelector)
                if (cont.length > 0) {
                    cont.empty();
                    existing = true;
                }
            }

            if (!existing) {
                let containerClass = edges.css_classes(namespace, containerName);
                elements.append(`<div class="${containerClass} ${additionalClasses}" ${additionalStyles}></div>`);
            }

            return elements.find(containerSelector);
        },

        newAutocheck: function (params) {
            return edges.instantiate(formulaic.widgets.Autocheck, params);
        },
        Autocheck: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.namespace = "formulaic-autocheck-" + this.fieldDef.name;

            this.init = function () {
                let annos = this._getAutochecksForField();
                if (annos.length === 0) {
                    return;
                }

                let generalClass = "formulaic-autocheck-container";
                let defaultDisplay = "style='display: none'";
                let cont = formulaic.widgets._make_empty_container(this.namespace, "autochecks", this.form, this.fieldDef, generalClass, defaultDisplay);

                let frag = "";
                for (let anno of annos) {
                    frag += this._renderAutocheck(anno)
                }

                let listClass = edges.css_classes(this.namespace, "list")
                frag = `<ul class="${listClass}">${frag}</ul>`;
                cont.html(frag);

                feather.replace();
            }

            this._getAutochecksForField = function () {
                if (!doaj.autochecks) {
                    return [];
                }
                let applicable = [];
                for (let anno of doaj.autochecks.checks) {
                    if (anno.field && anno.field === this.fieldDef.name) {
                        applicable.push(anno);
                    }
                }
                return applicable;
            }

            this._renderAutocheck = function (autocheck) {
                let frag = "<li>";

                if (autocheck.checked_by && doaj.autocheckers &&
                    doaj.autocheckers.registry.hasOwnProperty(autocheck.checked_by)) {
                    frag += (new doaj.autocheckers.registry[autocheck.checked_by]()).draw(autocheck)
                } else {
                    frag += this._defaultRender(autocheck);
                }

                frag += `</li>`;
                return frag;
            }

            this._defaultRender = function (autocheck) {
                let frag = "";
                if (autocheck.advice) {
                    frag += `${autocheck.advice}<br>`
                }
                if (autocheck.reference_url) {
                    frag += `<a href="${autocheck.reference_url}" target="_blank">${autocheck.reference_url}</a><br>`
                }
                if (autocheck.suggested_value) {
                    frag += `Suggested Value(s): ${autocheck.suggested_value.join(", ")}<br>`
                }
                if (autocheck.original_value) {
                    frag += `(Original value when automated checks ran: ${autocheck.original_value})`
                }
                return frag;
            }

            this.init();
        },

        newSubjectTree: function (params) {
            return edges.instantiate(formulaic.widgets.SubjectTree, params);
        },
        SubjectTree: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.input = false;

            this.ns = "formulaic-subjecttree";

            this.nestedEdge = false;

            this.init = function () {

                var tree = doaj.af.lccTree;
                var containerId = edges.css_id(this.ns, "container");
                var containerSelector = edges.css_id_selector(this.ns, "container");
                var widgetId = edges.css_id(this.ns, this.fieldDef.name);
                var modalOpenClass = edges.css_classes(this.ns, "open");
                var closeClass = edges.css_classes(this.ns, "close");

                this.input = $("[name=" + this.fieldDef.name + "]");
                this.input.hide();

                this.input.after('<a href="#" class="button button--tertiary ' + modalOpenClass + '">Open Subject Classifier</a>');
                this.input.after(`<div class="modal" id="` + containerId + `" tabindex="-1" role="dialog" style="display: none; padding-right: 0px; overflow-y: scroll">
                                    <div class="modal__dialog" role="document">
                                        <header class="flex-space-between modal__heading">
                                          <h3 class="modal__title">
                                            “Subject classifications”
                                          </h3>
                                          <span type="button" data-dismiss="modal" class="` + closeClass + ` type-01"><span class="sr-only">Close</span>&times;</span>
                                        </header>
                                        <p class="alert">Selecting a subject will not automatically select its sub-categories.</p>
                                        <div id="` + widgetId + `"></div>
                                        <button type="button" data-dismiss="modal" class="` + closeClass + `">Add subject(s)</button>
                                    </div>
                                 </div>`);


                var subjectBrowser = formulaic.edges.newTreeBrowser({
                    id: widgetId,
                    sourceInput: this.input,
                    tree: function (tree) {
                        function recurse(ctx) {
                            var displayTree = [];
                            for (var i = 0; i < ctx.length; i++) {
                                var child = ctx[i];
                                var entry = {};
                                entry.display = child.text;
                                entry.value = child.id;
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
                        showCounts: false,
                        togglable: false
                    })
                });

                this.nestedEdge = edges.newEdge({
                    selector: containerSelector,
                    manageUrl: false,
                    components: [
                        subjectBrowser
                    ],
                    callbacks: {
                        "edges:query-fail": function () {
                            alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                        },
                        "edges:post-init": function () {
                            feather.replace();
                        },
                        "edges:post-render": function () {
                            feather.replace();
                        }
                    }
                });

                var modalOpenSelector = edges.css_class_selector(this.ns, "open");
                edges.on(modalOpenSelector, "click", this, "openModal");

                var closeSelector = edges.css_class_selector(this.ns, "close");
                edges.on(closeSelector, "click", this, "closeModal");
            };

            this.openModal = function () {
                var containerSelector = edges.css_id_selector(this.ns, "container");
                $(containerSelector).show();
            };

            this.closeModal = function () {
                var containerSelector = edges.css_id_selector(this.ns, "container");
                $(containerSelector).hide();
                this.input.trigger("change");
            };

            this.init();
        },
        newClickableOwner: function (params) {
            return edges.instantiate(formulaic.widgets.ClickableOwner, params)
        },
        ClickableOwner: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.namespace = "formulaic-clickableowner";

            this.link = false;

            this.init = function () {
                var elements = this.form.controlSelect.input({name: this.fieldDef.name});
                edges.on(elements, "change.ClickableOwner", this, "updateOwner");
                for (var i = 0; i < elements.length; i++) {
                    this.updateOwner(elements[i]);
                }
            };

            this.updateOwner = function (element) {
                var that = $(element);
                var val = that.val();

                if (val) {
                    if (this.link) {
                        this.link.attr("href", "/account/" + val);
                    } else {
                        let cont = formulaic.widgets._make_empty_container(this.namespace, "clickable_owner", this.form, this.fieldDef);
                        var classes = edges.css_classes(this.namespace, "visit");
                        var id = edges.css_id(this.namespace, this.fieldDef.name);
                        cont.html('<p><small><a id="' + id + '" class="' + classes + ' tag" rel="noopener noreferrer" target="_blank" href="/account/' + val + '"><span data-feather="user" aria-hidden="true"></span> See this account’s profile</a></small></p>');

                        var selector = edges.css_id_selector(this.namespace, this.fieldDef.name);
                        this.link = $(selector, this.form.context);
                    }
                } else if (this.link) {
                    this.link.remove();
                    this.link = false;
                }
            };

            this.init();
        },
        newClickToCopy: function (params) {
            return edges.instantiate(formulaic.widgets.ClickToCopy, params)
        },
        ClickToCopy: function (params) {
            this.fieldDef = params.fieldDef;
            this.init = function () {
                var elements = $("#click-to-copy--" + this.fieldDef.name);
                edges.on(elements, "click", this, "copy");
            };
            this.copy = function (element) {
                let form = new doaj.af.BaseApplicationForm()
                let value = form.determineFieldsValue(this.fieldDef.name)
                let value_to_copy = form.convertValueToText(value);
                navigator.clipboard.writeText(value_to_copy)
                var confirmation = $("#copy-confirmation--" + this.fieldDef.name);
                confirmation.text("Copied: " + value_to_copy);
                confirmation.show().delay(3000).fadeOut();
            };
            this.init();

        },
        newTrimWhitespace: function (params) {
            return edges.instantiate(formulaic.widgets.TrimWhitespace, params)
        },
        TrimWhitespace: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.ns = "formulaic-trimwhitespace";

            this.link = false;

            this.init = function () {
                var elements = this.form.controlSelect.input({name: this.fieldDef.name});
                edges.on(elements, "focus.TrimWhitespace", this, "trim");
                edges.on(elements, "blur.TrimWhitespace", this, "trim");

                for (var i = 0; i < elements.length; i++) {
                    this.trim(elements[i]);
                }
            };

            this.trim = function (element) {
                var that = $(element);
                var val = that.val();
                var nv = val.trim();
                if (nv !== val) {
                    that.val(nv);
                }
            };

            this.init();
        },

        newClickableUrl: function (params) {
            return edges.instantiate(formulaic.widgets.ClickableUrl, params)
        },
        ClickableUrl: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.ns = "formulaic-clickableurl";

            this.link = false;

            this.init = function () {
                var elements = this.form.controlSelect.input({name: this.fieldDef.name});

                edges.on(elements, "keyup.ClickableUrl", this, "updateUrl");

                for (var i = 0; i < elements.length; i++) {
                    this.updateUrl(elements[i]);
                }
            };

            this.updateUrl = function (element) {
                var that = $(element);
                var val = that.val();

                if (val && (val.substring(0, 7) === "http://" || val.substring(0, 8) === "https://") && val.length > 10) {
                    if (this.link) {
                        this.link.attr("href", val);
                    } else {
                        var classes = edges.css_classes(this.ns, "visit");
                        var id = edges.css_id(this.ns, this.fieldDef.name);
                        that.after('<p><a id="' + id + '" class="' + classes + ' button" style="margin: 0; height: 100%" rel="noopener noreferrer" target="_blank" title="Open URL in a new tab" href="' + val + '">\
                                        Open link\
                                        <span data-feather="external-link" aria-hidden="true"></span>\
                                    </a></p>');
                        var selector = edges.css_id_selector(this.ns, this.fieldDef.name);
                        this.link = $(selector, this.form.context);
                    }
                } else if (this.link) {
                    this.link.remove();
                    this.link = false;
                }
            };

            this.init();
        },

        newFullContents: function (params) {
            return edges.instantiate(formulaic.widgets.FullContents, params)
        },
        FullContents: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;

            this.ns = "formulaic-fullcontents";

            this.container = false;

            this.init = function () {
                var elements = this.form.controlSelect.input({name: this.fieldDef.name});
                edges.on(elements, "keyup.FullContents", this, "updateContents");

                for (var i = 0; i < elements.length; i++) {
                    this.updateContents(elements[i]);
                }
            };

            this.updateContents = function (element) {
                var that = $(element);
                var val = that.val();

                // if there is a behaviour for when the field is empty and disabled, then check if it is, and if
                // it is include the desired alternative text
                if (this.args && this.args.empty_disabled) {
                    if (val === "" && that.prop("disabled")) {
                        val = this.args.empty_disabled;
                    }
                }

                if (val) {
                    if (this.container) {
                        this.container.html('<small><strong>Full contents: ' + edges.escapeHtml(val) + '</strong></small>');
                    } else {
                        let cont = formulaic.widgets._make_empty_container(this.ns, "clickable_url", this.form, this.fieldDef);
                        var classes = edges.css_classes(this.ns, "contents");
                        var id = edges.css_id(this.ns, this.fieldDef.name);
                        cont.html('<p id="' + id + '" class="' + classes + '"><small><strong>Full contents: ' + edges.escapeHtml(val) + '</strong></small></p>');

                        var selector = edges.css_id_selector(this.ns, this.fieldDef.name);
                        this.container = $(selector, this.form.context);
                    }
                } else if (this.container) {
                    this.container.remove();
                    this.container = false;
                }
            };

            this.init();
        },

        newNoteModal: function (params) {
            return edges.instantiate(formulaic.widgets.NoteModal, params)
        },
        NoteModal: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.ns = "formulaic-notemodal";

            this.container = false;

            this.init = function () {
                var viewClass = edges.css_classes(this.ns, "view");
                var closeClass = edges.css_classes(this.ns, "close");
                let group = $("div[name='" + this.fieldDef["name"] + "__group']")
                var textarea = group.find("textarea");

                let inputs = group.find("input[type=text]")
                for (let i = 0; i < inputs.length; i++) {
                    let jqin = $(inputs[i]);
                    let iid = jqin.attr("id");
                    if (iid.endsWith("_author")) {
                        let val = jqin.val()
                        if (val === "") {
                            jqin.hide();
                        }
                    }
                }

                for (var i = 0; i < textarea.length; i++) {
                    var container = $(textarea[i]);

                    let contentHeight = container[0].scrollHeight;
                    if (contentHeight > 200) {
                        contentHeight = 200;
                    }
                    container.css("height", (contentHeight + 5) + "px");

                    var modalId = "modal-" + this.fieldDef["name"] + "-" + i;

                    var date = $("#" + this.fieldDef["name"] + "-" + i + "-note_date");
                    var note = $("#" + this.fieldDef["name"] + "-" + i + "-note");
                    var author = $("#" + this.fieldDef["name"] + "-" + i + "-note_author");

                    $(`<button class="button ` + viewClass + `" style="margin: 0 1rem 1rem 0;">View note</button>
                        <div class="modal" id="` + modalId + `" tabindex="-1" role="dialog" style="display: none; padding-right: 0px; overflow-y: scroll">
                            <div class="modal__dialog" role="document">
                              <header class="flex-space-between modal__heading">
                                <span>
                                  <p class="label">Note</p>
                                  <h3 class="modal__title"> ${author.val()} </h3>
                                  <h3 class="modal__title"> ${date.val()} </h3>
                                </span>
                                <span type="button" data-dismiss="modal" class="type-01 ` + closeClass + `"><span class="sr-only">Close</span>&times;</span>
                              </header>
                              <p>` + edges.escapeHtml(note.val()).replace(/\n/g, "<br/>") + `</p>
                            </div>
                        </div>
                        </div>
                    `).insertAfter(container);
                }

                var viewSelector = edges.css_class_selector(this.ns, "view");
                edges.on(viewSelector, "click", this, "showModal");

                var closeSelector = edges.css_class_selector(this.ns, "close");
                edges.on(closeSelector, "click", this, "closeModal");
            };

            this.showModal = function (element) {
                var that = $(element);
                var modal = that.siblings(".modal");
                modal.show();
            };

            this.closeModal = function (element) {
                var that = $(element);
                var modal = that.parents(".modal");
                modal.hide();
            };

            this.init();
        },

        newInfiniteRepeat: function (params) {
            return edges.instantiate(formulaic.widgets.InfiniteRepeat, params)
        },
        InfiniteRepeat: function (params) {
            this.fieldDef = params.fieldDef;
            this.args = params.args;

            this.idRx = /(.+?-)(\d+)(-.+)/;
            this.template = "";
            this.container = false;
            this.divs = false;

            this.init = function () {
                this.divs = $("div[name='" + this.fieldDef["name"] + "__group']");
                for (var i = 0; i < this.divs.length; i++) {
                    var div = $(this.divs[i]);
                    div.append($('<button type="button" data-id="' + i + '" id="remove_field__' + this.fieldDef["name"] + '--id_' + i + '" class="remove_field__button" style="display:none; margin: 0 0 1rem 0; border: 0; float: right;">Remove<span data-feather="x" aria-hidden="true"/></button>'));
                    feather.replace();
                }

                this.template = $(this.divs[0]).html();
                this.container = $(this.divs[0]).parents(".removable-fields");

                if (this.divs.length === 1) {
                    let div = $(this.divs[0]);
                    let inputs = div.find(":input");
                    let tripwire = false;
                    for (var i = 0; i < inputs.length; i++) {
                        if ($(inputs[i]).val()) {
                            tripwire = true;
                            break;
                        }
                    }
                    if (!tripwire) {
                        // the field is empty
                        $(this.divs[0]).remove();
                        this.divs = [];
                    }
                }

                this.addFieldBtn = $("#add_field__" + this.fieldDef["name"]);
                this.removeFieldBtns = $('[id^="remove_field__' + this.fieldDef["name"] + '"]');

                edges.on(this.addFieldBtn, "click", this, "addField");
                edges.on(this.removeFieldBtns, "click", this, "removeField");

                // show or hide the remove buttons
                for (let i = 0; i < this.divs.length; i++) {
                    let cur_div = $(this.divs[i]);
                    if (!cur_div.find('textarea').is(':disabled')) {
                        cur_div.find('[id^="remove_field__"]').show();
                    }
                }

            };

            this.addField = function () {
                var currentLargest = -1;
                for (var i = 0; i < this.divs.length; i++) {
                    var div = $(this.divs[i]);
                    var id = div.find(":input").attr("id");
                    var match = id.match(this.idRx);
                    var thisId = parseInt(match[2]);
                    if (thisId > currentLargest) {
                        currentLargest = thisId;
                    }
                }
                var newId = currentLargest + 1;

                var frag = '<div name="' + this.fieldDef["name"] + '__group">' + this.template + '</div>';
                var jqt = $(frag);
                var that = this;
                jqt.find(":input").each(function () {
                    var el = $(this);
                    var id = el.attr("id");

                    var match = id.match(that.idRx);
                    if (match) {
                        var bits = id.split(that.idRx);
                        var newName = bits[1] + newId + bits[3];
                        el.attr("id", newName).attr("name", newName).val("");
                    } else {
                        // could be the remove button
                        if (id.substring(0, "remove_field".length) === "remove_field") {
                            el.attr("id", "remove_field__" + that.fieldDef["name"] + "--id_" + newId);
                            el.show();
                        }
                    }
                });
                if (this.args.enable_on_repeat) {
                    for (var i = 0; i < this.args.enable_on_repeat.length; i++) {
                        var enables = jqt.find(that.args.enable_on_repeat[i]);
                        enables.removeAttr("disabled");
                    }
                }

                var topPlacement = this.fieldDef.repeatable.add_button_placement === "top";
                if (this.divs.length > 0) {
                    if (topPlacement) {
                        $(this.divs[0]).before(jqt);
                    } else {
                        $(this.divs[this.divs.length - 1]).after(jqt);
                    }
                } else {
                    this.container.append(jqt);
                }


                this.divs = $("div[name='" + this.fieldDef["name"] + "__group']");
                this.removeFieldBtns = $('[id^="remove_field__' + this.fieldDef["name"] + '"]');
                edges.on(this.removeFieldBtns, "click", this, "removeField");
            };

            this.removeField = function (element) {
                var container = $(element).parents("div[name='" + this.fieldDef["name"] + "__group']");
                container.remove();
                this.divs = $("div[name='" + this.fieldDef["name"] + "__group']");
            };

            this.init();
        },

        newMultipleField: function (params) {
            return edges.instantiate(formulaic.widgets.MultipleField, params)
        },
        MultipleField: function (params) {
            this.fieldDef = params.fieldDef;
            this.max = this.fieldDef["repeatable"]["initial"] - 1;

            this.init = () => {
                if (this.fieldDef["input"] === "group") {
                    this._setupRepeatingGroup();
                } else {
                    this._setupRepeatingIndividual();
                }
                feather.replace();
            };

            this._setupIndividualSelect2 = function () {
                for (var idx = 0; idx < this.fields.length; idx++) {
                    let f = this.fields[idx];
                    let s2_input = $($(f).select2());
                    $(f).on("focus", formulaic.widgets._select2_shift_focus);
                    s2_input.after($('<button type="button" id="remove_field__' + f.name + '--id_' + idx + '" class="remove_field__button">Remove <span data-feather="x" aria-hidden="true"/></button>'));
                    if (idx !== 0) {
                        s2_input.attr("required", false);
                        s2_input.attr("data-parsley-validate-if-empty", "true");
                        if (!s2_input.val()) {
                            s2_input.closest('li').hide();
                        } else {
                            this.count++;
                        }
                    }
                }

                this.remove_btns = $('[id^="remove_field__' + this.fieldDef["name"] + '"]');
                if (this.count === 0) {
                    $(this.remove_btns[0]).hide();
                }

                this.addFieldBtn = $("#add_field__" + this.fieldDef["name"]);
                this.addFieldBtn.on("click", () => {
                    $('#s2id_' + this.fieldDef["name"] + '-' + (this.count + 1)).closest('li').show();
                    this.count++;
                    if (this.count > 0) {
                        $(this.remove_btns[0]).show();
                    }
                    if (this.count >= this.max) {
                        $(this.addFieldBtn).hide();
                    }
                });

                if (this.count >= this.max) {
                    this.addFieldBtn.hide();
                }

                $(this.remove_btns).each((idx, btn) => {
                    $(btn).on("click", (event) => {
                        for (let i = idx; i < this.count; i++) {
                            let data = $(this.fields[i + 1]).select2('data');
                            if (data === null) {
                                data = {id: i, text: ""};
                            }
                            $(this.fields[i]).select2('data', {id: data.id, text: data.text});
                        }
                        this.count--;
                        $(this.fields[this.count + 1]).select2('data', {id: this.count + 1, text: ""});
                        $('#s2id_' + this.fieldDef["name"] + '-' + (this.count + 1)).closest('li').hide();
                        if (this.count === 0) {
                            $(this.remove_btns[0]).hide();
                        }
                        if (this.count < this.max) {
                            $(this.addFieldBtn).show();
                        }
                    })
                })
            };

            this._setupIndividualField = function () {
                for (var idx = 0; idx < this.fields.length; idx++) {
                    let f = this.fields[idx];
                    let jqf = $(f);
                    jqf.after($('<button type="button" id="remove_field__' + f.name + '--id_' + idx + '" class="remove_field__button">Remove <span data-feather="x" aria-hidden="true"/></button>'));
                    if (idx !== 0) {
                        jqf.attr("required", false);
                        jqf.attr("data-parsley-validate-if-empty", "true");
                        if (!jqf.val()) {
                            jqf.parent().hide();
                        } else {
                            this.count++;
                        }
                    }
                }

                this.remove_btns = $('[id^="remove_field__' + this.fieldDef["name"] + '-"]');
                if (this.count === 0) {
                    $(this.remove_btns[0]).hide();
                }

                this.addFieldBtn = $("#add_field__" + this.fieldDef["name"]);
                this.addFieldBtn.on("click", () => {
                    let next_input = $('[id="' + this.fieldDef["name"] + '-' + (this.count + 1) + '"]').parent();
                    // TODO: why .show() does not work?
                    $(next_input).show();
                    this.count++;
                    if (this.count > 0) {
                        $(this.remove_btns[0]).show();
                    }
                    if (this.count >= this.max) {
                        $(this.addFieldBtn).hide();
                    }
                });

                if (this.count >= this.max) {
                    this.addFieldBtn.hide();
                }

                $(this.remove_btns).each((idx, btn) => {
                    $(btn).on("click", (event) => {
                        for (let i = idx; i < this.count; i++) {
                            let data = $(this.fields[i + 1]).val();
                            if (data === null) {
                                data = "";
                            }
                            $(this.fields[i]).val(data);
                        }

                        this.count--;
                        $(this.fields[this.count + 1]).val("");
                        let last_input = $('[id="' + this.fieldDef["name"] + '-' + (this.count + 1) + '"]').parent();
                        $(last_input).hide();
                        if (this.count === 0) {
                            $(this.remove_btns[0]).hide();
                        }
                        if (this.count < this.max) {
                            $(this.addFieldBtn).show();
                        }
                    })
                });
            };

            this._setupRepeatingIndividual = function () {
                let tag = this.fieldDef["input"] === "select" ? "select" : "input";
                this.fields = $(tag + '[id^="' + this.fieldDef["name"] + '-"]');
                this.count = 0;

                if (tag === "select") {
                    this._setupIndividualSelect2();
                } else {
                    this._setupIndividualField();
                }
            };

            this._setupRepeatingGroup = function () {
                this.divs = $("div[name='" + this.fieldDef["name"] + "__group']");
                this.count = 0;

                for (var idx = 0; idx < this.divs.length; idx++) {
                    let div = $(this.divs[idx]);
                    div.append($('<button type="button" id="remove_field__' + this.fieldDef["name"] + '--id_' + idx + '" class="remove_field__button">Remove <span data-feather="x" aria-hidden="true"/></button>'));

                    if (idx !== 0) {
                        let inputs = div.find(":input");
                        var hasVal = false;
                        for (var j = 0; j < inputs.length; j++) {
                            $(inputs[j]).attr("required", false)
                                .attr("data-parsley-required-if", false)
                                .attr("data-parsley-validate-if-empty", "true");
                            if ($(inputs[j]).val()) {
                                hasVal = true;
                            }
                        }
                        if (!hasVal) {
                            div.hide();
                        } else {
                            this.count++;
                        }
                    }
                }

                this.remove_btns = $('[id^="remove_field__' + this.fieldDef["name"] + '"]');
                if (this.count === 0) {
                    $(this.remove_btns[0]).hide();
                }

                this.addFieldBtn = $("#add_field__" + this.fieldDef["name"]);
                this.addFieldBtn.on("click", () => {
                    $(this.divs[this.count + 1]).show();
                    this.count++;
                    if (this.count > 0) {
                        $(this.remove_btns[0]).show();
                    }
                    if (this.count === this.max) {
                        $(this.addFieldBtn).hide();
                    }
                });

                if (this.count >= this.max) {
                    this.addFieldBtn.hide();
                }

                $(this.remove_btns).each((idx, btn) => {
                    $(btn).on("click", () => {
                        let thisDiv = $(btn).parent();
                        let nextDiv = $(thisDiv);
                        for (let i = idx; i < this.count; i++) {
                            thisDiv = nextDiv;
                            nextDiv = nextDiv.next();
                            let thisInputs = $(thisDiv).find("select, input[id^='" + this.fieldDef["name"] + "']");
                            let nextInputs = $(nextDiv).find("select, input[id^='" + this.fieldDef["name"] + "']");
                            for (let j = 0; j < thisInputs.length; j++) {
                                let thisInput = $(thisInputs[j]);
                                let nextInput = $(nextInputs[j]);
                                if (thisInput.is("select")) {
                                    let data = $(nextInput).select2('data');
                                    if (data === null) {
                                        data = {id: i, text: ""};
                                    }
                                    $(thisInput).select2('data', {id: data.id, text: data.text});

                                } else {
                                    $(thisInputs[j]).val($(nextInputs[j]).val());
                                }
                            }
                        }
                        this.count--;
                        $(this.divs[this.count + 1]).find("select, input[id^='" + this.fieldDef["name"] + "']").each((idx, inp) => {
                            if ($(inp).is("select")) {
                                $(inp).select2('data', {id: this.count + 1, text: ""});
                            } else {
                                $(inp).val("");
                            }
                        });
                        $(this.divs[this.count + 1]).hide();
                        if (this.count === 0) {
                            $(this.remove_btns[0]).hide();
                        }
                        if (this.count < this.max) {
                            $(this.addFieldBtn).show();
                        }
                    })
                })
            };

            this.init()
        },

        newSelect: function (params) {
            return edges.instantiate(formulaic.widgets.Select, params);
        },
        Select: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;

            this.ns = "formulaic-select";
            this.elements = false;

            this.init = function () {
                let allow_clear = this.args.allow_clear || false;
                this.elements = $("select[name$='" + this.fieldDef.name + "']");
                this.elements.select2({
                    allowClear: allow_clear,
                    newOption: true,
                    placeholder: "Start typing…"
                });
                $(this.elements).on("focus", formulaic.widgets._select2_shift_focus);
            };

            this.init();
        },

        newTagList: function (params) {
            return edges.instantiate(formulaic.widgets.TagList, params);
        },
        TagList: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;

            this.ns = "formulaic-taglist";

            this.init = function () {
                var stopWords = edges.getParam(this.args.stopWords, []);

                var ajax = {
                    url: current_scheme + "//" + current_domain + "/autocomplete/journal/" + this.args["field"],
                    dataType: 'json',
                    data: function (term, page) {
                        return {
                            q: term
                        };
                    },
                    results: function (data, page) {
                        return {results: data["suggestions"].filter((x) => $.inArray(x.text.toLowerCase(), stopWords) === -1)};
                    }
                };

                var csc = function (term) {
                    if ($.inArray(term.toLowerCase(), stopWords) !== -1) {
                        return null;
                    }
                    return {id: $.trim(term), text: $.trim(term)};
                };


                var initSel = function (element, callback) {
                    var initial = element.val();
                    var entries = initial.split(",").map(x => x.trim()).filter(x => x !== "");
                    var data = [];
                    for (var i = 0; i < entries.length; i++) {
                        data.push({id: entries[i], text: entries[i]});
                    }
                    callback(data);
                };

                // apply the create search choice
                let selector = "[name='" + this.fieldDef.name + "']";
                $(selector).select2({
                    multiple: true,
                    minimumInputLength: 1,
                    ajax: ajax,
                    createSearchChoice: csc,
                    initSelection: initSel,
                    placeholder: "Start typing…",
                    allowClear: false,
                    tags: true,
                    tokenSeparators: [',', ";"],
                    maximumSelectionSize: this.args["maximumSelectionSize"],
                    width: 'resolve'
                });

                $(selector).on("focus", formulaic.widgets._select2_shift_focus);

            };

            this.init();
        },

        newTagEntry: function (params) {
            return edges.instantiate(formulaic.widgets.TagEntry, params);
        },
        TagEntry: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;

            this.ns = "formulaic-tagentry";

            this.init = function () {
                let selector = "[name='" + this.fieldDef.name + "']";
                $(selector).select2({
                    minimumInputLength: 1,
                    tags: [],
                    tokenSeparators: [','],
                    width: 'resolve'
                });
                $(selector).on("focus", formulaic.widgets._select2_shift_focus);
            };

            this.init();
        },


        newLoadEditors: function (params) {
            return edges.instantiate(formulaic.widgets.LoadEditors, params);
        },

        LoadEditors: function (params) {
            this.fieldDef = params.fieldDef;
            this.params = params.args;

            this.groupField = false;
            this.editorField = false;

            this.init = function () {
                this.groupField = $("[name='" + this.fieldDef.name + "']");
                this.editorField = $("[name='" + this.params.field + "']");
                edges.on(this.groupField, "change", this, "updateEditors");
            };

            this.updateEditors = function (element) {
                var ed_group_name = $(element).val();
                var ed_query_url = "/admin/dropdown/eg_associates";

                // var ed_group_name = $("#s2id_editor_group").find('span').text();
                var that = this;
                $.ajax({
                    type: "GET",
                    data: {egn: ed_group_name},
                    dataType: "json",
                    url: ed_query_url,
                    success: function (resp) {
                        // Get the options for the drop-down from our ajax request
                        var assoc_options = [];
                        if (resp != null) {
                            assoc_options = [["", "No editor assigned"]];

                            for (var i = 0; i < resp.length; i++) {
                                assoc_options = assoc_options.concat([[resp[i], resp[i]]]);
                            }
                        } else {
                            assoc_options = [["", ""]];
                        }

                        // Set the editor drop-down options to be the chosen group's associates
                        // var ed_field = $("#editor");
                        that.editorField.empty();

                        for (var j = 0; j < assoc_options.length; j++) {
                            that.editorField.append(
                                $("<option></option>").attr("value", assoc_options[j][0]).text(assoc_options[j][1])
                            );
                        }
                    }
                })
            };

            this.init();
        },

        newAutocomplete: function (params) {
            return edges.instantiate(formulaic.widgets.Autocomplete, params);
        },

        Autocomplete: function (params) {
            this.fieldDef = params.fieldDef;
            this.params = params.args;

            this.init = function () {
                let doc_type = this.params.type || "journal";
                let doc_field = this.params.field;
                let mininput = this.params.min_input === undefined ? 3 : this.params.min_input;
                let include_input = this.params.include === undefined ? true : this.params.include;
                let allow_clear = this.params.allow_clear_input === undefined ? true : this.params.allow_clear_input;

                let ajax = {
                    url: current_scheme + "//" + current_domain + "/autocomplete/" + doc_type + "/" + doc_field,
                    dataType: 'json',
                    data: function (term, page) {
                        return {
                            q: term
                        };
                    },
                    results: function (data, page) {
                        return {results: data["suggestions"]};
                    }
                };

                var csc = function (term) {
                    return {"id": term, "text": term};
                };

                var initSel = function (element, callback) {
                    var data = {id: element.val(), text: element.val()};
                    callback(data);
                };

                let selector = "[name='" + this.fieldDef.name + "']";

                $(selector).on("focus", formulaic.widgets._select2_shift_focus);

                if (include_input) {
                    // apply the create search choice
                    $(selector).select2({
                        minimumInputLength: mininput,
                        ajax: ajax,
                        createSearchChoice: csc,
                        initSelection: initSel,
                        allowClear: allow_clear,
                        width: 'resolve'
                    });
                } else {
                    // go without the create search choice option
                    $(selector).select2({
                        minimumInputLength: mininput,
                        ajax: ajax,
                        initSelection: initSel,
                        allowClear: allow_clear,
                        width: 'resolve'
                    });
                }

                $(selector).on("focus", formulaic.widgets._select2_shift_focus);
            };

            this.init()
        },
        newIssnLink: function (params) {
            return edges.instantiate(formulaic.widgets.IssnLink, params)
        },
        IssnLink: function (params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.issn = params.issn;

            this.ns = "formulaic-issnlink";

            this.link = false;
            this.url = "https://portal.issn.org/resource/ISSN/";

            this.init = function () {
                var elements = this.form.controlSelect.input(
                    {name: this.fieldDef.name});
                edges.on(elements, "keyup.IssnLink", this, "updateUrl");

                for (var i = 0; i < elements.length; i++) {
                    this.updateUrl(elements[i]);
                }
            };

            this.updateUrl = function (element) {
                var that = $(element);
                var val = that.val();
                var id = edges.css_id(this.ns, this.fieldDef.name);

                var match = val.match(/[d0-9]{4}-{0,1}[0-9]{3}[0-9xX]{1}/);
                var url = this.url + val;

                if (val && match) {
                    if (this.link) {
                        this.link.text(url);
                        this.link.attr("href", url);
                    } else {
                        var classes = edges.css_classes(this.ns, "visit");
                        that.after('<p><small><a id="' + id + '" class="' + classes + '" rel="noopener noreferrer" target="_blank" href="' + url + '">' + url + '</a></small></p>');

                        var selector = edges.css_id_selector(this.ns, this.fieldDef.name);
                        this.link = $(selector, this.form.context);
                    }
                } else if (this.link) {
                    this.link.remove();
                    this.link = false;
                }
            };

            this.init();
        },

        newArticleInfo : (params) => edges.instantiate(formulaic.widgets.ArticleInfo, params),
        ArticleInfo: function ({formulaic, fieldDef, args}) {
            const $sealEle = $('label[for=doaj_seal-0]');

            if (!$sealEle.length) {
                console.log('skip ArticleInfo, seal section not found')
                return;
            }

            const idResult = window.location.pathname.match('/journal/([a-f0-9]+)')
            if (!idResult) {
                console.log('skip ArticleInfo, journal id not found')
                return
            }
            const journalId = idResult[1]
            fetch(`/admin/journal/${journalId}/article-info`)
                .then(response => response.json())
                .then(data => {
                    let articleText = `(This journal has ${data.n_articles} articles in DOAJ)`
                    if (data.n_articles > 0) {
                        const articlesUrl = `/admin/journal/${journalId}/article-info/admin-site-search`
                        articleText = `<a href="${articlesUrl}" target="_blank">${articleText}</a>`
                    }
                    $sealEle.html($sealEle.text() + ` ${articleText}`)
                })
        }
    }
};
