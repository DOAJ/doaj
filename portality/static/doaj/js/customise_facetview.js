function customise_facetview_init() {
    insert_progress_bar();
    $('.facetview_orderby').css('background-color', 'white');
    $('.facetview_orderby').css('width', 'auto');
    $('.facetview_searchfield').css('width', 'auto');
    $('.facetview_filtershow').bind('click', toggle_bottom_border);
}

function customise_facetview_results() {
    $('.facetview_metadata div').css('border-color', '#F68B1F');
    $('.facetview_decrement, .facetview_increment').css('color', '#F68B1F');
    $('.date-month').each(expand_month)
    customise_facets();
}

function customise_facets() {
    $('#facetview_bibjson_author_pays_exact .facetview_filterchoice_text').each(
            function() {
                thespan = $(this);
                if (fv_author_pays.mapping[thespan.html()]) {
                    thespan.html(fv_author_pays.mapping[thespan.html()]);
                }
            }
        );
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
    $('#facetview_selectedfilters').prepend('<div class="progress progress-danger progress-striped active notify_loading" id="search-progress-bar"><div class="bar"></div></div>');
}
