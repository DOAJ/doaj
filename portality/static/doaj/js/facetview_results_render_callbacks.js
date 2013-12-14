// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner
fv_author_pays = (function(resultobj) {
    var that = function(resultobj) {
        if(that.mapping[resultobj['bibjson']['author_pays']]) {
            var result = '<span class=' + that.mapping[resultobj['bibjson']['author_pays']]['class'] + '>';
            result += that.mapping[resultobj['bibjson']['author_pays']]['text'];
            result += '</span>';
            return result;
        } else {
            return resultobj['bibjson']['author_pays'];
        }
    };
    return that;
})();

fv_author_pays.mapping = {
    "Y": {"text": "Has charges", "class": "red"},
    "N": {"text": "No charges", "class": "green"},
    "CON": {"text": "Conditional charges", "class": "blue"},
    "NY": {"text": "No info available", "class": ""},
}

fv_created_date = (function (resultobj) {
    var that = function(resultobj) {
        return iso_datetime2date(resultobj['created_date']);
    };
    return that;
})();
