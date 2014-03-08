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
    
    
    
    toggle_url_field('waiver_policy', '#waiver_policy_url');
    toggle_url_field('download_statistics', '#download_statistics_url');
    toggle_url_field('plagiarism_screening', '#plagiarism_screening_url');
    toggle_url_field('publishing_rights', '#publishing_rights_url');
    toggle_url_field('copyright', '#copyright_url');
    toggle_url_field('license_embedded', '#license_embedded_url');
    
    toggle_charges_amount('processing_charges');
    toggle_charges_amount('submission_charges');
    
    toggle_other_field('license', '#license_checkbox');
    
    
    $('#country').select2();
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

function toggle_url_field(field_name, url_id) {
    $('input[name=' + field_name + ']:radio').change( function () {
        if (this.value == 'False') {
            $(url_id).parents('.control-group').hide();
        } else {
            $(url_id).parents('.control-group').show();
        }
        
    });

}

function toggle_charges_amount(field_name) {
    $('input[name=' + field_name + ']:radio').change( function () {
        $('#' + field_name + '_amount').parent().parent().toggle();
        $('#' + field_name + '_currency').parent().parent().toggle();
    });
}

function toggle_other_field(field_name, selector) {
    $('input[name=' + field_name + ']:radio').change(function () {
        if (this.value == 'Other') {
            $(selector).parents('.control-group').show();
        } else {
            $(selector).parents('.control-group').hide();
        }
    });  
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
