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
    $('#plagiarsm_screening_url').parents('.control-group').hide();
    $('#license_checkbox').parents('.control-group').hide();
    
    
    toggle_url_field('waiver_policy');
    toggle_url_field('download_statistics');
    toggle_url_field('plagiarism_screening');
    
    toggle_charges_amount('processing_charges');
    toggle_charges_amount('submission_charges');
    
    expand_with_checkboxes('license');
    
    $('#country').select2()
          
    
});

function toggle_url_field(field_name) {
    $('input[name=' + field_name + ']:radio').change( function () {
        $('#' + field_name + '_url').parent().parent().toggle();
        
    });

}

function toggle_charges_amount(field_name) {
    $('input[name=' + field_name + ']:radio').change( function () {
        $('#' + field_name + '_amount').parent().parent().toggle();
        $('#' + field_name + '_currency').parent().parent().toggle();
    });
}

function expand_with_checkboxes(field_name) {
    $('input[name=' + field_name + ']:radio').change(function () {
        if (this.value == 'Other') {
            $('#license_checkbox').parent().parent().show();
        } else {
            $('#license_checkbox').parent().parent().hide();
        }
    });    
     
}
