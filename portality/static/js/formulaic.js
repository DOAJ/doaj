var formulaic = {
    // FIXME: we should base this on edges to take advantage of the framework tools
    init : function(params) {
        // FIXME: this should instantiate an object, which we can set properties on, rather than
        // being a static lib
        var formSelector = params.formSelector;
        var context = $(formSelector);

        var cfg = formulaicSettings.config;
        for (var i = 0; i < cfg.fieldsets.length; i++) {
            var fieldset = cfg.fieldsets[i];
            for (var j = 0; j < fieldset.fields.length; j++) {
                var field = fieldset.fields[j];
                var formControl = formulaic._controlSelect({name : field.name, context: context});
                formulaic.bindConditional({field: field, formControl: formControl, context: context});
            }
        }
    },

    bindConditional : function(params) {
        var field = params.field;
        var formControl = params.formControl;
        var context = params.context;

        if (!field.hasOwnProperty("conditional")) {
            return;
        }

        for (var i = 0; i < field.conditional.length; i++) {
            var condition = field.conditional[i];
            var control = formulaic._controlSelect({name: condition.field, context: context});
            control.on("change", function(event) {
                if (formulaic._conditionsSatisfied({field: field, formControl: formControl, context: context})) {
                    $("#" + field.name + "_container").show();
                } else {
                    $("#" + field.name + "_container").hide();
                }
            });
        }
    },

    _conditionsSatisfied : function(params) {
        var field = params.field;
        var formControl = params.formControl;
        var context = params.context;

        for (var i = 0; i < field.conditional.length; i++) {
            var condition = field.conditional[i];
            var control = formulaic._controlSelect({name: condition.field, context: context});
            if (condition.value !== control.val()) {
                return false;
            }
        }

        return true;
    },

    _controlSelect : function(params) {
        return $("[name=" + params.name + "]", params.context).filter(":input");
    }
};