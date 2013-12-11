// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner
fv_author_pays = (function(resultobj) {
    var that = function(resultobj) {
        if(that.mapping[resultobj['bibjson']['author_pays']]) {
            return that.mapping[resultobj['bibjson']['author_pays']];
        } else {
            return resultobj['bibjson']['author_pays'];
        }
    };
    return that;
})();

fv_author_pays.mapping = {
    "Y": "Has charges",
    "N": "No charges",
    "CON": "Conditional charges",
}
