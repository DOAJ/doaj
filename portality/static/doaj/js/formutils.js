function toggle_optional_field(field_name, optional_field_selectors, values_to_show_for) {
    var values_to_show_for = values_to_show_for || ["True"];
    var main_field_selector = '[name=' + field_name + ']';

    // hide all optional fields first
    for (var i = 0; i < optional_field_selectors.length; i++) {
        $(optional_field_selectors[i]).parents('.control-group').hide();
    }

    // show them again if the correct radio button is chosen
    $(main_field_selector).each( function () {
        __init_optional_field(this, optional_field_selectors, values_to_show_for);
    });

    $(main_field_selector).change( function () {
        if ($.inArray(this.value, values_to_show_for) >= 0) {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.control-group').show();
            }
        } else {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.control-group').hide();
                $(optional_field_selectors[i]).val(undefined);
            }
        }
    });
}

function __init_optional_field(elem, optional_field_selectors, values_to_show_for) {
    var values_to_show_for = values_to_show_for || ["True"];
    var main_field = $(elem);

    // For radio buttons, the checked attribute must be present. For other fields, the just the value must be correct
    if ((main_field.is(':checked')  || main_field.is('select') ) && $.inArray(main_field.val(), values_to_show_for) >= 0) {
        for (var i = 0; i < optional_field_selectors.length; i++) {
            $(optional_field_selectors[i]).parents('.control-group').show();
        }
    }
}

function toggle_section(sectionSelector, pullDownSelector, value, container, containerWidth) {
    var originalWidth = $(container).width();
    var state = "closed";

    $(pullDownSelector).on("change", function(event) {
        if ($(pullDownSelector).val() ===  value) {
            originalWidth = $(container).width();
            $(container).animate({width: containerWidth},
                {
                    duration: 200,
                    step: function() {
                        $(container).css("overflow", "");
                    },
                    complete: function() {
                        $(sectionSelector).slideDown(400);
                    }
                }
            );
            state = "open";
        } else {
            if (state === "open") {
                $(sectionSelector).slideUp(400, function() {
                    $(container).animate({width: originalWidth},
                        {
                            duration: 200,
                            step: function() {
                                $(container).css("overflow", "");
                            }
                        }
                    );
                });
                state = "closed";
            }
        }
    });
}
