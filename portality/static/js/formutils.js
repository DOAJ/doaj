function toggle_optional_field(field_name, optional_field_selectors, values_to_show_for) {
    var values_to_show_for = values_to_show_for || ["True"];
    var main_field_selector = '[name=' + field_name + ']';

    // hide all optional fields first
    for (var i = 0; i < optional_field_selectors.length; i++) {
        $(optional_field_selectors[i]).parents('.form-group').hide();
    }

    // show them again if the correct radio button is chosen
    $(main_field_selector).each( function () {
        __init_optional_field(this, optional_field_selectors, values_to_show_for);
    });

    $(main_field_selector).change( function () {
        if ($.inArray(this.value, values_to_show_for) >= 0) {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.form-group').show();
            }
        } else {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.form-group').hide();
                $(optional_field_selectors[i]).val(undefined);
            }
        }
    });
}

function __init_optional_field(elem, optional_field_selectors, values_to_show_for) {
    var values_to_show_for_l = values_to_show_for || ['True'];
    var main_field = $(elem);

    // For radio buttons, the checked attribute must be present. For other fields, the just the value must be correct
    if ((main_field.is(':checked')  || main_field.is('select') ) && $.inArray(main_field.val(), values_to_show_for_l) >= 0) {
        for (var i = 0; i < optional_field_selectors.length; i++) {
            $(optional_field_selectors[i]).parents('.form-group').show();
        }
    }
}
