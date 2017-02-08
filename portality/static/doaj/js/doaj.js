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
    if (!isodate_str) { return "" }
    return isodate_str.replace('T',' ').replace('Z','')
}

function journal_toc_id(journal) {
    // if e-issn is available, use that
    // if not, but a p-issn is available, use that
    // if neither ISSN is available, use the internal ID
    var ids = journal.bibjson.identifier;
    var pissns = [];
    var eissns = [];
    if (ids) {
        for (var i = 0; i < ids.length; i++) {
            if (ids[i].type === "pissn") {
                pissns.push(ids[i].id)
            } else if (ids[i].type === "eissn") {
                eissns.push(ids[i].id)
            }
        }
    }

    var toc_id = undefined;
    if (eissns.length > 0) { toc_id = eissns[0]; }
    if (!toc_id && pissns.length > 0) { toc_id = pissns[0]; }
    if (!toc_id) { toc_id = journal.id; }

    return toc_id;
}