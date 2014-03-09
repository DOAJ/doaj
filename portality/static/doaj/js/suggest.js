jQuery(document).ready(function($) {

    $("#submit_status").click(function(event) {
        event.preventDefault()
        
        var newstatus = $("select[name=application_status]").val()
        var suggestion_id = $("input[name=suggestion_id]").val()
        var original = $("input[name=current_status]").val()
        var obj = {"status" : newstatus}
        
        $.ajax({
            type: "POST",
            url: "/admin/suggestion/" + suggestion_id,
            contentType: "application/json",
            dataType: "json",
            data: JSON.stringify(obj),
            success: function() {
                // alert("status updated")
                // update the hidden field
                $("input[name=current_status]").val(newstatus)
                $("#submit_status").attr("disabled", "disabled")
                $("#submit_status").attr("class", "btn")
            },
            error: function() {
                alert("ERROR: unable to update status.  If the problem persists, please contact your sysadmin.")
                // reset the pull-down
                $("select[name=application_status] option").filter(function() {return $(this).val() === original}).prop("selected", true)
                $("#submit_status").attr("disabled", "disabled")
                $("#submit_status").attr("class", "btn")
            },
            complete: function(req, status) {
                // alert(status)
            }
        })

    });
    
    $("select[name=application_status]").change(function() {
        var original = $("input[name=current_status]").val()
        var newstatus = $("select[name=application_status]").val()
        
        if (newstatus !== original) {
            $("#submit_status").removeAttr("disabled")
            $("#submit_status").attr("class", "btn btn-info")
        } else {
            $("#submit_status").attr("disabled", "disabled")
            $("#submit_status").attr("class", "btn")
        }
    });
    
    $('#processing_charges_amount').parents('.control-group').hide();
    $('#processing_charges_currency').parents('.control-group').hide();
    $('#submission_charges_amount').parents('.control-group').hide();
    $('#submission_charges_currency').parents('.control-group').hide();
    $('#waiver_policy_url').parents('.control-group').hide();
    $('#download_statistics_url').parents('.control-group').hide();
    $('#plagiarism_screening_url').parents('.control-group').hide();
    $('#license_checkbox').parents('.control-group').hide();
    $('#copyright_url').parents('.control-group').hide();
    $('#publishing_rights_url').parents('.control-group').hide();
    $('#license_embedded_url').parents('.control-group').hide();
    
    
    
    toggle_optional_field('waiver_policy', ['#waiver_policy_url']);
    toggle_optional_field('download_statistics', ['#download_statistics_url']);
    toggle_optional_field('plagiarism_screening', ['#plagiarism_screening_url']);
    toggle_optional_field('publishing_rights', ['#publishing_rights_url']);
    toggle_optional_field('copyright', ['#copyright_url']);
    toggle_optional_field('license_embedded', ['#license_embedded_url']);
    toggle_optional_field('processing_charges', ['#processing_charges_amount', '#processing_charges_currency']);
    toggle_optional_field('submission_charges', ['#submission_charges_amount', '#submission_charges_currency']);
    toggle_optional_field('license', ['#license_checkbox'], "Other");
    
    $('#country').select2();
    $('#processing_charges_currency').select2();
    $('#submission_charges_currency').select2();
    
    $("#keywords").select2({
        minimumInputLength: 1,
        tags: [],
        tokenSeparators: [","]
    });
    
    $("#languages").select2();
          
    autocomplete('#publisher', 'bibjson.publisher');
    autocomplete('#society_institution', 'bibjson.institution');
    autocomplete('#platform', 'bibjson.provider');
    
});

function toggle_optional_field(field_name, optional_field_selectors, value_to_show_for) {
    value_to_show_for = value_to_show_for || "True";
    main_field_selector = 'input[name=' + field_name + '][type="radio"]';

    $(main_field_selector + ':checked').each( function () {
        __init_optional_field(this, optional_field_selectors, value_to_show_for);
    });

    $(main_field_selector).change( function () {
        if (this.value == value_to_show_for) {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.control-group').show();
            }
        } else {
            for (var i = 0; i < optional_field_selectors.length; i++) {
                $(optional_field_selectors[i]).parents('.control-group').hide();
            }
        }
    });
}

function __init_optional_field(elem, optional_field_selectors, value_to_show_for) {
    value_to_show_for = value_to_show_for || "True";
    main_field = $(elem);

    if (main_field.val() == value_to_show_for) {
        for (var i = 0; i < optional_field_selectors.length; i++) {
            $(optional_field_selectors[i]).parents('.control-group').show();
        }
    } else {
        for (var i = 0; i < optional_field_selectors.length; i++) {
            $(optional_field_selectors[i]).parents('.control-group').hide();
        }
    }
}

function autocomplete(selector, doc_field, doc_type) {
    var doc_type = doc_type || "journal";
    $(selector).select2({
        minimumInputLength: 3,
        ajax: {
            url: "../autocomplete/" + doc_type + "/" + doc_field,
            dataType: 'json',
            data: function (term, page) {
                return {
                    q: term
                };
            },
            results: function (data, page) {
                return { results: data["suggestions"] };
            }
        },
        createSearchChoice: function(term) {return {"id":term, "text": term};}
    });
}
