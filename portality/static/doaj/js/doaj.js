function customise_facetview() {
    //$('#facetview_filters .table-striped tbody tr:nth-child(2n+1) td, .table-striped tbody tr:nth-child(2n+1) th').css('background-color', '#ffeece');
    $('.facetview_filtershow').bind('click', toggle_bottom_border);
    $('.facetview_orderby').css('background-color', 'white');
    $('.facetview_orderby').css('width', 'auto');
    $('.facetview_searchfield').css('width', 'auto');
    $('.facetview_metadata div').css('border-color', '#F68B1F');
    $('.facetview_decrement, .facetview_increment').css('color', '#F68B1F');
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
