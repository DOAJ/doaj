var formulaic = {

    newFormulaic : function(params) {
        return edges.instantiate(formulaic.Formulaic, params);
    },
    Formulaic : function(params) {
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
        this.init = function() {
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

        this.getElementName = function(element) {
            var name = element.attr("data-formulaic-sync");
            if (!name) {
                name = element.attr("name");
            }
            return name;
        };

        this.getFieldDefinition = function(params) {
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

        this.bindSave = function() {
            edges.on(this.context.find(".formulaic-complete"), "click.Complete", this, "saveComplete", false, false, false);
            edges.on(this.context.find(".formulaic-draft"), "click.Draft", this, "saveDraftAndComplete", false, false, false);

            if (this.autoSave > 0) {
                setTimeout(this.backgroundSaveClosure(), this.autoSave);
            }
        };

        this.backgroundSaveClosure = function() {
            var that = this;
            return function() {
                that.save({validate: false, additional : {"draft" : "true", "async" : "true"}, complete: false});
                setTimeout(that.backgroundSaveClosure(), that.autoSave);
            }
        };

        this.saveComplete = function(element, event) {
            this.save({event: event});
        };

        this.saveDraftAndComplete = function(element, event) {
            this.save({validate: false, additional : {"draft" : "true", "async" : "true"}, event: event})
        };

        this.save = function(params) {
            if (!params) { params = {}}
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
                        error: function() {/*alert("background save failed")*/},
                        success: function(response_data) {
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

        this.setId = function(params) {
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

        this.registerSynchronised = function() {
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
                allByName.each(function() {
                    var that = $(this);
                    var current_id = that.attr("id");
                    that.attr("data-formulaic-sync", name).attr("data-formulaic-id", current_id);
                });

                var fieldsets = this.synchronised[name];
                for (var j = 0; j < fieldsets.length; j++) {
                    var fieldset = fieldsets[j];
                    var elements = this.controlSelect.input({fieldset: fieldset, name: name});
                    elements.each(function() {
                        var newname = fieldset + "__" + name;
                        var newid = fieldset + "__" + $(this).attr("id");
                        $(this).attr("name", newname).attr("id", newid);
                    });
                }

                edges.on(allByName, "change.Synchronise", this, "synchroniseChange");
            }
        };

        this.synchroniseChange = function(element) {
            var that = $(element);
            var name = that.attr("data-formulaic-sync");
            var original_id = that.attr("data-formulaic-id");
            var type = that.attr("type");

            // TODO: we currently only synchronise radio and checkboxes, so if you need to synchronise
            // other fields, this will need extending
            if (type === "radio" || type === "checkbox") {
                var checked = that.is(":checked");
                var toSync = this.controlSelect.input({syncName: name});
                toSync.each(function() {
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

        // Functionsl for conditional fields
        ///////////////////////////////////////////////////////

        this.bindConditional = function() {
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
                            this.conditionals[condField] = [field.name]
                        }

                        // bind a change event for checking conditionals
                        var element = this.controlSelect.input({name: condField});
                        edges.on(element, "change.Conditional", this, "checkConditional");
                    }
                }
            }
        };

        this.checkConditional = function(element) {
            var name = this.getElementName($(element));
            var downstream = this.conditionals[name];
            for (var i = 0; i < downstream.length; i++) {
                var field = downstream[i];
                if (this.isConditionSatisfied({field: field})) {
                    this.controlSelect.container({name: field}).show();
                } else {
                    this.controlSelect.container({name: field}).hide();
                }
            }
        };

        this.isConditionSatisfied = function(params) {
            var field = params.field;
            var definition = this.getFieldDefinition(params);
            for (var i = 0; i < definition.conditional.length; i++) {
                var condField = definition.conditional[i];
                var elements = this.controlSelect.input({name: condField.field});
                var type = elements.attr("type");
                var val = condField.value;

                if (type === "radio" || type === "checkbox") {
                    var checkedValues = [];
                    elements.each(function() {
                        var that = $(this);
                        if (that.is(":checked")) {
                            checkedValues.push(that.val());
                        }
                    });
                    if ($.inArray(val, checkedValues) === -1) {
                        return false;
                    }
                }
            }
            return true;
        };

        ///////////////////////////////////////////////////////

        // Functions for widget handling
        ///////////////////////////////////////////////////////

        this.applyWidgets = function() {
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

        this.getWidget = function(widgetName) {
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

        this.bindExclusiveCheckboxes = function() {
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
            }
        };

        this.checkExclusive = function(element) {
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
            elements.each(function() {
                var that = $(this);
                if (checked && that.val() !== value) {
                    that.prop("checked", false);
                    that.prop('disabled', true);
                } else {
                    that.prop('disabled', false);
                }
            });
        };

        ////////////////////////////////////////////////////

        // Parsley state management
        ////////////////////////////////////////////////////

        this.destroyParsley = function() {
            if (!this.doValidation) { return; }
            if (this.activeParsley) {
                this.activeParsley.destroy();
                this.activeParsley = false;
                this.context.off("submit.Parsley");
            }
            // $(".has-error").removeClass("has-error");
        };

        this.bounceParsley = function() {
            if (!this.doValidation) { return; }
            this.destroyParsley();
            this.activeParsley = this.context.parsley();
        };

        ////////////////////////////////////////////////////

        // call the init  function to complete construction
        this.init();
    },

    newDefaultControlSelect : function(params) {
        return edges.instantiate(formulaic.DefaultControlSelect, params);
    },
    DefaultControlSelect : function(params) {
        this.containerClassTemplate = edges.getParam(params.containerClassTemplate, "{name}__container");

        this.formulaic = false;

        this.set_formuaic = function(f) {
            this.formulaic = f;
        };

        this.get_context = function(params) {
            var context = this.formulaic.context;
            if (params.fieldset) {
                context = $("#" + params.fieldset, context);
            }
            return context;
        };

        this.input = function(params) {
            var context = this.get_context(params);
            if (params.name) {
                var name = params.name;
                // TODO: we might need to do something about nested fields, especially if they are repeatable
                //var def = this.formulaic.getFieldDefinition({field: name});
                //if (def.in_group) {
                //    name = def.in_group + "-" + name;
                //}
                return $("[name=" + name + "], [data-formulaic-sync=" + name + "]", context).filter(":input");
            } else if (params.id) {
                return $("#" + params.id, context).filter(":input");
            } else if (params.syncName) {
                return $("[data-formulaic-sync=" + params.syncName + "]", context).filter(":input");
            }
        };

        this.container = function(params) {
            var context = this.get_context(params);
            var name = params.name || params.syncName;
            var selector = "." + this.containerClassTemplate.replace("{name}", name);
            return $(selector, context)
        };
    },

    widgets : {
        newClickableUrl : function(params) {
            return edges.instantiate(formulaic.widgets.ClickableUrl, params)
        },
        ClickableUrl : function(params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;

            this.ns = "formulaic-clickableurl";

            this.link = false;

            this.init = function() {
                var elements = this.form.controlSelect.input({name: this.fieldDef.name});
                edges.on(elements, "change.ClickableUrl", this, "updateUrl");
            };

            this.updateUrl = function(element) {
                var that = $(element);
                var val = that.val();

                if (val) {
                    if (this.link) {
                        this.link.attr("href", val);
                    } else {
                        var classes = edges.css_classes(this.ns, "visit");
                        var id = edges.css_id(this.ns, this.fieldDef.name);
                        that.after('<a id="' + id + '" class="' + classes + '" target="_blank" href="' + val + '">visit site</a>');

                        var selector = edges.css_id_selector(this.ns, this.fieldDef.name);
                        this.link = $(selector, this.form.context);
                    }
                } else {
                    this.link.remove();
                    this.link = false;
                }
            };

            this.init();
        },

        newSelect : function(params) {
            return edges.instantiate(formulaic.widgets.Select, params);
        },
        Select : function(params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;    // TODO: no args currently supported

            this.ns = "formulaic-select";
            this.elements = false;

            this.init = function() {
                this.elements = this.form.controlSelect.input({name: this.fieldDef.name});
                this.elements.select2({
                    allowClear: true
                });
            };

            this.init();
        },

        newTagList : function(params) {
            return edges.instantiate(formulaic.widgets.TagList, params);
        },
        TagList : function(params) {
            this.fieldDef = params.fieldDef;
            this.form = params.formulaic;
            this.args = params.args;

            this.ns = "formulaic-taglist";

            this.init = function() {

                var minInputLength = edges.getParam(this.args.minimumInputLength, 1);
                var tokenSeparators = edges.getParam(this.args.tokenSeparators, [","]);
                var maximumSelectionSize = edges.getParam(this.args.maximumSelectionSize, 6);
                var stopWords = edges.getParam(this.args.stopWords, []);

                this.elements = this.form.controlSelect.input({name: this.fieldDef.name});
                this.elements.select2({
                    minimumInputLength: minInputLength,
                    tags: [],
                    tokenSeparators: tokenSeparators,
                    maximumSelectionSize: maximumSelectionSize,
                    createSearchChoice : function(term) {   // NOTE: if we update select2, this has to change
                        if ($.inArray(term, stopWords) !== -1) {
                            return null;
                        }
                        return {id: $.trim(term), text: $.trim(term)};
                    }
                });
            };

            this.init();
        }
    }
};