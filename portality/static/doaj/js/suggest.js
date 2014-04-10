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

    setup_subject_tree();
    setup_remove_buttons();
    setup_add_buttons();
});

function setup_subject_tree() {
    $(function () {
        $('#subject_tree').jstree({
            'plugins':["wholerow","checkbox","sort","search"],
            'core' : {
                'data' : lcc_jstree
            },
            "checkbox" : {
                "three_state" : false
            },
            "search" : {
                "fuzzy" : false,
                "show_only_matches" : true
            },
        });
    });

    $('#subject_tree')
        .on('ready.jstree', function (e, data) {
            var subjects = $('#subject').val();
            for (var i = 0; i < subjects.length; i++) {
                $('#subject_tree').jstree('select_node', subjects[i]);
            }
        });

    $('#subject_tree')
        .on('changed.jstree', function (e, data) {
            var subjects = $('#subject').val(data.selected);
        });

    
    $('#subject_tree_container').prepend('<div class="control-group" id="subject_tree_search-container"><label class="control-label" for="subject_tree_search">Search through the subjects</label><div class="controls"><input class="input-large" id="subject_tree_search" type="text" placeholder="start typing..."><p class="help-block">Selecting a subject will <strong>not automatically select its sub-categories</strong>.</p></div></div>')

    var to = false;
    $('#subject_tree_search').keyup(function () {
        if(to) { clearTimeout(to); }
        to = setTimeout(function () {
          var v = $('#subject_tree_search').val();
          $('#subject_tree').jstree(true).search(v);
        }, 750);
    });

    $('#subject-container').hide();
}

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
        $(".remove_button").click(remove_nested_field(nested_field_prefix, nested_field_suffix))
	});
}

function setup_add_buttons() {
    var customisations = {
        // by container element id - container of the add more button and the fields being added
        'notes-outer-container': {'value': 'Add a note', 'id': 'add_note_btn'}
    };

    $('.addable-field-container').each(function() {
        e = $(this);
        id = e.attr('id')
        var value = customisations[id]['value'] || 'Add';

        var thebtn = '<button class="btn btn-info add_button"';
        thebtn += ' value="' + value + '"';
        if (customisations[id]['id']) {
            thebtn += ' id="' + customisations[id]['id'] + '"';
        }
        thebtn += '>' + value + '</button>';
        e.append(thebtn);
    });
    setup_add_button_handlers();
}

function setup_add_button_handlers() {
    // this isn't as generic as the other functions - each button has to
    // have its own click handler defined here for it to work
    
    var add_note_btn = function () {
        event.preventDefault();

        if (typeof cur_number_of_notes == 'undefined') {
            cur_number_of_notes = 0; // yes, global

            $('[id^=notes-][id$="-container"]').each(function(){
                cur_number_of_notes += 1;  // it doesn't have to be sequential or exact or anything like that,
                                           // it just needs to be DIFFERENT for every note
                                           // so count the number of notes already on the page
            });
        }

        thefield = [
            '<div class="control-group row-fluid deletable " id="notes-' + cur_number_of_notes + '-container">',
            '    <div class="span8 nested-field-container">',
            '        <label class="control-label" for="note">',
            '          Note',
            '        </label>',
            '        <div class="controls ">',
            '                <textarea class="span11" id="notes-' + cur_number_of_notes + '-note" name="notes-' + cur_number_of_notes + '-note"></textarea>',
            '        </div>',
            '    </div>',
            '    <div class="span3 nested-field-container">',
            '        <label class="control-label" for="date">',
            '          Date',
            '        </label>',
            '        <div class="controls ">',
            '                <input class="span11" disabled="" id="notes-' + cur_number_of_notes + '-date" name="notes-' + cur_number_of_notes + '-date" type="text" value="">',
            '        </div>',
            '    </div>',
            '</div>',
        ].join('\n');

        cur_number_of_notes += 1;  // this doesn't get decremented in the remove button because there's no point, WTForms will understand it
            // even if the ID-s go 0, 2, 7, 13 etc.
        $(this).before(thefield);
        setup_remove_buttons();
    };

    var button_handlers = {
        // by button element id
        'add_note_btn': add_note_btn
    };
    for (var button_id in button_handlers) {
        $('#' + button_id).unbind('click');
        $('#' + button_id).click(button_handlers[button_id]);
    }
}

function setup_remove_buttons() {
    $('.deletable').each(function() {
        e = $(this);
        id = e.attr('id');
        if(e.find('button[id="remove_'+id+'"]').length == 0) {
            e.append('<button id="remove_'+id+'" target="'+id+'" class="btn btn-danger remove_button"><i class="icon icon-remove-sign"></i></button>');
        }
        setup_remove_button_handler();
    });
}

function setup_remove_button_handler() {
    $(".remove_button").unbind("click")
    $(".remove_button").click( function() {
        event.preventDefault();
        var toremove = $(this).attr('target');
        $('#' + toremove).remove();
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
