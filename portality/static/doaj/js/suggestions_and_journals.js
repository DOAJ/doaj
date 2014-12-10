jQuery(document).ready(function($) {

    ////// functions for handling edit locks ///////////////////////

    function setLockTimeout() {
        var ts = $("#lock_expires").attr("data-timestamp")
        var d = new Date(ts)
        var hours = d.getHours()
        var minutes = d.getMinutes()
        if (String(minutes).length == 1) { minutes = "0" + minutes }
        var formatted = hours + ":" + minutes
        $("#lock_expires").html(formatted)
    }
    setLockTimeout()

    function unlock(params) {
        var type = params.type
        var id = params.id

        function success_callback(data) {
            var newWindow = window.open('', '_self', ''); //open the current window
            window.close(url);
        }

        function error_callback(jqXHR, textStatus, errorThrown) {
            alert("error releasing lock: " + textStatus + " " + errorThrown)
        }

        $.ajax({
            type: "POST",
            url: "/service/unlock/" + type + "/" + id,
            contentType: "application/json",
            dataType: "json",
            success : success_callback,
            error: error_callback
        })
    }

    $("#unlock").click(function(event) {
        event.preventDefault()
        var id = $(this).attr("data-id")
        var type = $(this).attr("data-type")
        unlock({type : type, id : id})
    })

    // NOTE: this does not play well with page reloads, so not using it
    //$(window).unload(function() {
    //   var id = $("#unlock").attr("data-id")
    //    var type = $("#unlock").attr("data-type")
    //    unlock({type : type, id : id})
    //});

    ////////////////////////////////////////////////////


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
    autocomplete('#owner', 'id', 'account');
    autocomplete('#editor_group', 'name', 'editor_group', 1, false);

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

    $("#editor_group").change(function(event) {
        event.preventDefault()
        $("#editor").html("<option val='' selected='selected'></option>")
    })
});

function setup_subject_tree() {
    $(function () {
        $('#subject_tree').jstree({
            'plugins':["checkbox","sort","search"],
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
            var subjects = $('#subject').val() || [];
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

function autocomplete(selector, doc_field, doc_type, mininput, include_input, allow_clear) {
    var doc_type = doc_type || "journal";
    var mininput = mininput === undefined ? 3 : mininput
    var include_input = include_input === undefined ? true : include_input
    var allow_clear = allow_clear === undefined ? true : allow_clear

    var ajax = {
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
        }
    var csc = function(term) {return {"id":term, "text": term};}
    var initSel = function (element, callback) {
            var data = {id: element.val(), text: element.val()};
            callback(data);
        }

    if (include_input) {
        // apply the create search choice
        $(selector).select2({
            minimumInputLength: mininput,
            ajax: ajax,
            createSearchChoice: csc,
            initSelection : initSel,
            placeholder: "",
            allowClear: allow_clear
        });
    } else {
        // go without the create search choice option
        $(selector).select2({
            minimumInputLength: mininput,
            ajax: ajax,
            initSelection : initSel,
            placeholder: "",
            allowClear: allow_clear
        });
    }
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
    
    var add_note_btn = function (event) {
        event.preventDefault();

        if (typeof cur_number_of_notes == 'undefined') {
            cur_number_of_notes = 0; // yes, global

            $('[id^=notes-][id$="-container"]').each(function(){
                cur_number_of_notes += 1;  // it doesn't have to be sequential or exact or anything like that,
                                           // it just needs to be DIFFERENT for every note
                                           // so count the number of notes already on the page
            });
        }

        // FIXME: this is a duplicate of what the jinja template does, meaning we have 2 places
        // where we need to update it if it changes.  Should clone a similar element instead.
        var delclass = ""
        if (notes_deletable) { // global variable set by template
            delclass = " deletable "
        }
        thefield = [
            '<div class="control-group row-fluid' + delclass + '" id="notes-' + cur_number_of_notes + '-container">',
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
        if (notes_deletable) {
            setup_remove_buttons();
        }
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
    $(".remove_button").click( function(event) {
        event.preventDefault();
        var toremove = $(this).attr('target');
        $('#' + toremove).remove();
    });
}
