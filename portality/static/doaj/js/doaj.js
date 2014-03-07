jQuery(document).ready(function() {
    $.noop(); // just a placeholder, delete when adding code here
});


function iso_datetime2date(isodate_str) {
    /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
     * "2003-04-03"
     */
    return isodate_str.substring(0,10);
}

function iso_datetime2date_and_time(isodate_str) {
    /* >>> "2013-12-13T22:35:42Z".replace('T',' ').replace('Z','')
     * "2013-12-13 22:35:42"
     */
    return isodate_str.replace('T',' ').replace('Z','')
}

