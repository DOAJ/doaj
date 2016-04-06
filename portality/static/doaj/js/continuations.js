jQuery(document).ready(function($) {
    $("#replaces").select2({
        minimumInputLength: 1,
        tags: [],
        tokenSeparators: [","]
    });

    $("#is_replaced_by").select2({
        minimumInputLength: 1,
        tags: [],
        tokenSeparators: [","]
    });

    $("#discontinued_date").datepicker({
        dateFormat: "yy-mm-dd",
        constrainInput: true,
        changeYear: true,
        maxDate: 0
    });
});