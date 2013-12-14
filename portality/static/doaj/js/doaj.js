jQuery(document).ready(function() {
    $.noop(); // just a placeholder, delete when adding code here
});


function iso_datetime2date(isodate_str) {
    /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
     * "2003-04-03"
     */
    return isodate_str.substring(0,10);
}
