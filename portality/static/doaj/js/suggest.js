jQuery(document).ready(function($) {

    // define a new highlight function, letting us highlight any element
    // on a page
    // adapted from http://stackoverflow.com/a/11589350
    jQuery.fn.highlight = function(color, fade_time) {
       // some defaults
       var color = color || "#F68B1F";  // the DOAJ color
       var fade_time = fade_time || 1500;  // milliseconds

       $(this).each(function() {
            var el = $(this);
            el.before("<div/>")
            el.prev()
                .width(el.width())
                .height(el.height())
                .css({
                    "position": "absolute",
                    "background-color": color,
                    "opacity": ".9"   
                })
                .fadeOut(fade_time);
        });
    }

    // animated scrolling to an anchor
    jQuery.fn.anchorAnimate = function(settings) {

        settings = jQuery.extend({
            speed : 700
        }, settings);   
    
        return this.each(function(){
            var caller = this
            $(caller).click(function (event) {  
                event.preventDefault()
                var locationHref = window.location.href
                var elementClick = $(caller).attr("href")
    
                var destination = $(elementClick).offset().top;

                $("html:not(:animated),body:not(:animated)").animate({ scrollTop: destination}, settings.speed, function() {
                    window.location.hash = elementClick;  // ... but it also needs to be getting set here for the animation itself to work
                });

                setTimeout(function(){
                    highlight_target();
                }, settings.speed + 50);

                return false;
            })
        })
    }

    /*
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
    */
    
    
    toggle_optional_field('waiver_policy', ['#waiver_policy_url']);
    toggle_optional_field('download_statistics', ['#download_statistics_url']);
    toggle_optional_field('plagiarism_screening', ['#plagiarism_screening_url']);
    toggle_optional_field('publishing_rights', ['#publishing_rights_url'], ["True", "Other"]);
    toggle_optional_field('copyright', ['#copyright_url'], ["True", "Other"]);
    toggle_optional_field('license_embedded', ['#license_embedded_url']);
    toggle_optional_field('processing_charges', ['#processing_charges_amount', '#processing_charges_currency']);
    toggle_optional_field('submission_charges', ['#submission_charges_amount', '#submission_charges_currency']);
    toggle_optional_field('license', ['#license_checkbox'], ["Other"]);
    
    $('#country').select2();
    $('#processing_charges_currency').select2();
    $('#submission_charges_currency').select2();
    
    $("#keywords").select2({
        minimumInputLength: 1,
        tags: [],
        tokenSeparators: [","],
        maximumSelectionSize: 6
    });
    
    $("#languages").select2();
          
    autocomplete('#publisher', 'bibjson.publisher');
    autocomplete('#society_institution', 'bibjson.institution');
    autocomplete('#platform', 'bibjson.provider');

    exclusive_checkbox('digital_archiving_policy', 'No policy in place');
    exclusive_checkbox('article_identifiers', 'None');
    exclusive_checkbox('deposit_policy', 'None');
    
    if ("onhashchange" in window) {
        window.onhashchange = highlight_target();
        $('a.animated').anchorAnimate();
    }

    $(function () {
        $('#subject_tree').jstree({
        'plugins':["wholerow","checkbox","sort"],
        'core' : {
            'data' : [
                {
                    "text" : "Medicine",
                    "children" : [
                        { "text" : "Medicine (General)", "state" : { "opened" : true }},
                        { "text" : "Health Sciences", "state" : { "opened" : true },
                            "children" : [
                                {"text": "Public Health", "state" : { "opened" : true }, "a_attr": {"code": "somecode"}}
                            ]
                        },
                    ],
                    "state" : { "opened" : true }
                }
            ]
        },
        "checkbox" : {
            "three_state" : false
        },
        });
    });
});

function toggle_optional_field(field_name, optional_field_selectors, values_to_show_for) {
    var values_to_show_for = values_to_show_for || ["True"];
    var main_field_selector = 'input[name=' + field_name + '][type="radio"]';

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
            }
        }
    });
}

function __init_optional_field(elem, optional_field_selectors, values_to_show_for) {
    var values_to_show_for = values_to_show_for || ["True"];
    var main_field = $(elem);

    if (main_field.is(':checked') && $.inArray(main_field.val(), values_to_show_for) >= 0) {
        for (var i = 0; i < optional_field_selectors.length; i++) {
            $(optional_field_selectors[i]).parents('.control-group').show();
        }
    }
}

function autocomplete(selector, doc_field, doc_type) {
    var doc_type = doc_type || "journal";
    $(selector).select2({
        minimumInputLength: 3,
        ajax: {
            url: current_scheme + "//" + current_domain + "/autocomplete/" + doc_type + "/" + doc_field,
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
        createSearchChoice: function(term) {return {"id":term, "text": term};},
        initSelection : function (element, callback) {
            var data = {id: element.val(), text: element.val()};
            callback(data);
        }
    });
}

function exclusive_checkbox(field_name, exclusive_val) {
    var doit = function() {
        if (this.checked) {
            $('#' + field_name + ' :checkbox:not([value="' + exclusive_val + '"])').prop('disabled', true);
            $('#' + field_name + ' .extra_input_field').prop('disabled', true);
        } else {
            $('#' + field_name + ' :checkbox:not([value="' + exclusive_val + '"])').prop('disabled', false);
            $('#' + field_name + ' .extra_input_field').prop('disabled', false);
        }
    };

    $('#' + field_name + ' :checkbox[value="' + exclusive_val + '"]').each(doit); // on page load too
    $('#' + field_name + ' :checkbox[value="' + exclusive_val + '"]').change(doit); // when exclusive checkbox ticked
}

function highlight_target() {
    $(window.location.hash).highlight()
}

function add_more_nested_fields(button_selector, nested_field_prefix, nested_field_suffix) {
    var nested_field_suffix = nested_field_suffix || '-container';

    $(button_selector).click( function (event) {
        event.preventDefault();

        // get the last div in the list
        var all_e = $('[id^=' + nested_field_prefix + '][id$="' + nested_field_suffix + '"]');
        var e = all_e.last();

        // make a clone of the last div
        var ne = e.clone()[0];

        // extract the last number from the div id and increment it
        var items = ne.id.split('-');
        var number = parseInt(items[1]);
        number = number + 1;

        // increment all the numbers
        _prepare_nested_container({
            nested_field_prefix: nested_field_prefix,
            nested_field_suffix: nested_field_suffix,
            element : ne,
            number : number,
            reset_value : true
        })

        e.after(ne);

        $(".remove_button").unbind("click")
        $(".remove_button").click(removeAuthor)
	});
}

function remove_nested_field(nested_field_prefix, nested_field_suffix) {
    var nested_field_suffix = nested_field_suffix || '-container';
    event.preventDefault();

    var id = $(this).attr("id")
    var short_name = id.split("_")[1]
    var container = short_name + nested_field_suffix

    $("#" + container).remove()

    var count = 0
    $('[id^=' + nested_field_prefix + '][id$="' + nested_field_suffix + '"]').each(function() {
        _prepare_nested_container({
            nested_field_prefix: nested_field_prefix,
            nested_field_suffix: nested_field_suffix,
            element : this,
            number: count,
            reset_value: false
        })
        count++;
    })
}

function _prepare_nested_container(params) {
    var nested_field_prefix = params.nested_field_prefix
    var nested_field_suffix = params.nested_field_suffix
    var ne = params.element
    var reset = params.reset_value
    var number = params.number
    
    var new_id = nested_field_prefix + number + nested_field_suffix;
    ne.id = new_id;
    
    ne = $(ne)
    ne.find('[id^=' + nested_field_prefix + ']').each( function () {
        var ce = $(this);
        
        // reset the value
        if (reset) {
            ce.attr('value', '');
        }
        
        // set the id as requestsed
        items = ce.attr('id').split('-');
        var id = nested_field_prefix + number + '-' + items[2];
        
        // set both the id and the name to the new id, as per wtforms requirements
        ce.attr('id', id);
        ce.attr('name', id);
    });
    
    // we also need to update the remove button
    ne.find("[id^=remove_' + nested_field_prefix + ']").each(function() {
        var ce = $(this);
        
        // update the id as above - saving us a closure again
        items = ce.attr('id').split('-');
        var id = 'remove_' + nested_field_prefix + number;
        
        // set both the id and the name to the new id
        ce.attr('id', id);
        ce.attr('name', id);
    })
}