var formulaic = {

    newFormulaic : function(params) {
        return edges.instantiate(formulaic.Formulaic, params);
    },
    Formulaic : function(params) {
        this.formSelector = edges.getParam(params.formSelector, "#formulaic");

        this.context = $(this.formSelector);

        this.fieldsets = edges.getParam(params.fieldsets, {});

        this.functions = edges.getParam(params.functions, {});

        // list of fields whose values are synchronised
        this.synchronised = {};

        // an inverted map of conditionals: keys are fields which are conditions of other fields
        this.conditionals = {};

        this.init = function() {
            // first detect any sychronised fields and register them
            this._registerSynchronised();

            // bind any conditional fields
            this._bindConditional();
        };

        this._registerSynchronised = function() {
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
                var allByName = this._controlSelect({name: name});
                allByName.each(function() {
                    $(this).attr("data-formulaic-sync", name);
                });

                var fieldsets = this.synchronised[name];
                for (var j = 0; j < fieldsets.length; j++) {
                    var fieldset = fieldsets[j];
                    var elements = this._controlSelect({fieldset: fieldset, name: name});
                    elements.each(function() {
                        $(this).attr("name", fieldset + "__" + name);
                    });
                }

                edges.on(allByName, "change.Synchronise", this, "synchroniseChange");
            }
        };

        this._bindConditional = function() {
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
                        var element = this._controlSelect({name: condField});
                        edges.on(element, "change.Conditional", this, "checkConditional");
                    }
                }
            }
        };

        this.checkConditional = function(element) {
            var name = this._getElementName($(element));
            var downstream = this.conditionals[name];
            for (var i = 0; i < downstream.length; i++) {
                var field = downstream[i];
                var el = this._controlSelect({name: field});
                if (this._isConditionSatisfied({field: field})) {
                    el.parents("." + field + "_container").show();
                } else {
                    el.parents("." + field + "_container").hide();
                }
            }
        };

        this._isConditionSatisfied = function(params) {
            var field = params.field;
            var definition = this.getFieldDefinition(params);
            for (var i = 0; i < definition.conditional.length; i++) {
                var condField = definition.conditional[i];
                var element = this._controlSelect({name: condField.field});
                var type = element.attr("type");
                var val = condField.value;

                if (type === "radio" || type === "checkbox") {
                    var checked = element.is(":checked");
                    if (checked !== val) {
                        return false;
                    }
                }
            }
            return true;
        };

        this.synchroniseChange = function(element) {
            var that = $(element);
            var name = that.attr("data-formulaic-sync");
            var id = that.attr("id");
            var type = that.attr("type");

            if (type === "radio" || type === "checkbox") {
                var checked = that.is(":checked");
                var toSync = this._controlSelect({syncName: name});
                toSync.each(function() {
                    var el = $(this);
                    if (el.attr("id") === id) {
                        el.prop("checked", checked);
                    } else {
                        el.prop("checked", !checked);
                    }
                });
            }
        };

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
        };

        this._getElementName = function(element) {
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

        this.init();
    }
};