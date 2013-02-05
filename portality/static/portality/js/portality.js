
jQuery(document).ready(function() {    
    
    // show the loading page on ajax call
    $.ajaxSetup({
        beforeSend:function(){
            $("#loadcover").show();
            $("#loading").show();
        },
        complete:function(){
            $("#loadcover").hide();
            $("#loading").hide();
        }
    });

    
    // show search options
    if ( jQuery('input[name="showopts"]').val() != undefined && jQuery('input[name="showopts"]').val() != "" ) {
        jQuery('#search_options').addClass('shown').show();
    }
    var show_search_options = function(event) {
        event.preventDefault();
        if ( jQuery('#search_options').hasClass('shown') ) {
            jQuery('#search_options').removeClass('shown').hide();
            jQuery('input[name="showopts"]').remove();
        } else {
            jQuery('#search_options').addClass('shown').show();
            if ( jQuery('input[name="showopts"]').val() == undefined) {
                jQuery('form').append('<input type="hidden" name="showopts" value="true" />');
            }
        }
    }
    jQuery('#show_search_options').bind('click',show_search_options);


    var show_view_options = function(event) {
        event.preventDefault();
        if (jQuery('.view_options').hasClass('shown')) {
            jQuery('.view_options').removeClass('shown').hide();
        } else {
            jQuery('.view_options').addClass('shown').show();
        }
    }
    jQuery('#show_view_options').bind('click',show_view_options);


    // attach functionality to trigger rpp, page, sort selections
    jQuery('#paging_trigger').remove();
    var rpp_select = function(event) {
        jQuery('#page_select').val($("#page_select option:first").val());
        jQuery(this).closest('form').trigger('submit');
    }
    var page_select = function(event) {
        jQuery(this).closest('form').trigger('submit');
    }
    jQuery('#rpp_select').bind('change',rpp_select);
    jQuery('#sort_select').bind('change',rpp_select);
    jQuery('#order_select').bind('change',rpp_select);
    jQuery('#page_select').bind('change',page_select);

    // do search options
    var fixmatch = function(event) {
        event.preventDefault();
        if ( jQuery(this).attr('id') == "partial_match" ) {
            var newvals = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').split(' ');
            var newstring = "";
            for (item in newvals) {
                if (newvals[item].length > 0 && newvals[item] != ' ') {
                    if (newvals[item] == 'OR' || newvals[item] == 'AND') {
                        newstring += newvals[item] + ' ';
                    } else {
                        newstring += '*' + newvals[item] + '* ';
                    }
                }
            }
            jQuery('#searchbox').val(newstring);
        } else if ( jQuery(this).attr('id') == "exact_match" ) {
            var newvals = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').split(' ');
            var newstring = "";
            for (item in newvals) {
                if (newvals[item].length > 0 && newvals[item] != ' ') {
                    if (newvals[item] == 'OR' || newvals[item] == 'AND') {
                        newstring += newvals[item] + ' ';
                    } else {
                        newstring += '"' + newvals[item] + '" ';
                    }
                }
            }
            $.trim(newstring,' ');
            jQuery('#searchbox').val(newstring);
        } else if ( jQuery(this).attr('id') == "match_any" ) {
            jQuery('#default_operator').remove();
            if (jQuery(this).hasClass('match_all')) {
                jQuery('#searchform').append('<input type="hidden" id="default_operator" name="default_operator" value="OR" />');
                jQuery('#searchbox').val(jQuery.trim(jQuery('#searchbox').val().replace(/ AND /gi,' ')));
                jQuery('#searchbox').val(jQuery('#searchbox').val().replace(/ /gi,' OR '));
            } else {
                jQuery('#searchbox').val(jQuery.trim(jQuery('#searchbox').val().replace(/ OR /gi,' ')));
                jQuery('#searchbox').val(jQuery('#searchbox').val().replace(/ /gi,' AND '));
            }
        }
        jQuery('#submit_main_search').trigger('click');
    }
    jQuery('#partial_match').bind('click',fixmatch);
    jQuery('#exact_match').bind('click',fixmatch);
    jQuery('#match_any').bind('click',fixmatch);
    
    var search_key = function(event) {
        event.preventDefault();
        var val = jQuery('#searchbox').val().replace(/"/gi,'').replace(/\*/gi,'').replace(/.*\.exact:/,'');
        if ( !(val[0] == '"' && val[val.length-1] == '"') ) {
            val = '"' + val + '"';
        }
        jQuery('#searchbox').val(jQuery(this).val() + ':' + val);
        jQuery('#submit_main_search').trigger('click');
    }
    jQuery('#search_key').bind('change',search_key);

});


