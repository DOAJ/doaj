function customise_facetview_init() {
    $('.facetview_orderby').css('background-color', 'white');
    $('.facetview_orderby').css('width', 'auto');
    $('.facetview_searchfield').css('width', 'auto');
    $('.facetview_filtershow').bind('click', toggle_bottom_border);
    customise_help_buttons_on_init();
}

function customise_facetview_presearch() {
    setTimeout(insert_progress_bar, 400);
}

function customise_facetview_results() {
    $('.facetview_metadata div').css('border-color', '#F68B1F');
    $('.facetview_decrement, .facetview_increment').css('color', '#F68B1F');
    $('.date-month').each(expand_month)
    $('.abstract_action').click(abstract_toggle);
    $('.abstract_text').hide();
    customise_facets();
    $('#facetview_selectedfilters #search-progress-bar').remove();
}

function customise_facets() {
    // make help button the last option on the facet options
    $('.facetview_filteroptions').each(function()
        {
            var thediv=$(this);
            var thehelpbtn=$(thediv.children('.facetview_learnmore')[0]);
            thehelpbtn.remove();
            thediv.append(thehelpbtn);
            thehelpbtn.click(function(event) {
                event.stopPropagation();
                event.preventDefault();
                $('#facetview_learnmore').fadeToggle(300);
            });
        });

    // bibjson.author_pays
    // 1. facet itself
    $('#facetview_bibjson_author_pays_exact .facetview_filterchoice_text').each(
            function() {
                thespan = $(this);
                if (fv_author_pays.mapping[thespan.html()]['text']) {
                    thespan.html(fv_author_pays.mapping[thespan.html()]['text']);
                }
            }
        );
    // bibjson.author_pays
    // 2. don't forget filter buttons
    $('a.facetview_filterselected[rel="bibjson.author_pays.exact"] > .facetview_filterselected_text').each(
            function() {
                thespan = $(this);
                if (fv_author_pays.mapping[thespan.text()]['text']) {
                    thespan.text(fv_author_pays.mapping[thespan.text()]['text']);
                }
            }
        );

    // always open some facets
    var alwaysopen = [/*'_type', 'index_classification_exact', 'index_language_exact'*/]
    for (var i = 0; i < alwaysopen.length; i++) {
        var cur = '#facetview_' + alwaysopen[i];
        var a = $(cur).find(".facetview_filtershow")
        a.trigger("click")
        // $(cur).find('.facetview_filtervalue').show();
        //$(cur).find('i').removeClass('icon-plus');
        //$(cur).find('i').addClass('icon-minus');
        //$(cur).addClass('facetview_open');
        //$('#facetview_' + cur).find('.facetview_filtervalue').show();
        //$(cur).find('.facetview_filteroptions').show();
    }
}

function toggle_bottom_border() {
    which_facet = this.rel;
    theanchor = $(this);
    if ( theanchor.hasClass('facetview_open') ) {
       $('#facetview_' + which_facet).addClass('no-bottom');
    } else {
       $('#facetview_' + which_facet).removeClass('no-bottom');
    }
}

months_english = {
    '1': 'January',
    '2': 'February',
    '3': 'March',
    '4': 'April',
    '5': 'May',
    '6': 'June',
    '7': 'July',
    '8': 'August',
    '9': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December'
}

function expand_month() {
    this.innerHTML = months_english[this.innerHTML.replace(/^0+/,"")];
}

function insert_progress_bar() {
    if ($.fn.facetview.options.searching) {
        $('#facetview_selectedfilters').prepend('<div class="progress progress-danger progress-striped active notify_loading" id="search-progress-bar"><div class="bar">Loading, please wait...</div></div>');
    }
}

function abstract_toggle(_event) {
    _event.preventDefault();
    _anchor = $(this);
    article_id = _anchor.attr('rel');
    if (_anchor.text() == '(expand)') { _anchor.text('(collapse)'); }
    else if(_anchor.text() == '(collapse)') { _anchor.text('(expand)'); }
    $('.abstract_text[rel="' + article_id + '"]').fadeToggle(300);
    return true;
}

function customise_help_buttons_on_init() {
    // close the help on clicking outside of the help
    // first, close it on clicking anywhere at all
    $('html').click(function() {
        if($('#facetview_learnmore').is(":visible")) {
            $('#facetview_learnmore').fadeOut(300);
        }
    });
    
    // but don't close it when clicking on the help itself
    $('#facetview_learnmore').click(function(event){
        event.stopPropagation();
    });

    // fade out the help when closing using the label
    $('.facetview_learnmore.label').unbind('click').click(function(event){
        event.preventDefault();
        $('#facetview_learnmore').fadeOut(300);
    });

    // help button in search options - don't close help when clicked
    // (it's the button that shows it after all). Also fade show/hide
    // the help when clicked.
    $('.facetview_learnmore').unbind('click').click(function(event){
        event.stopPropagation();
        event.preventDefault();
        $('#facetview_learnmore').fadeToggle(300);
    });
}
