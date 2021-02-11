
function autocomplete(selector, doc_field, doc_type, mininput, include_input, allow_clear) {
    var doc_type = doc_type || "journal";
    var mininput = mininput === undefined ? 3 : mininput;
    var include_input = include_input === undefined ? true : include_input;
    var allow_clear = allow_clear === undefined ? true : allow_clear;

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
        };
    var csc = function(term) {return {"id":term, "text": term};};
    var initSel = function (element, callback) {
            var data = {id: element.val(), text: element.val()};
            callback(data);
        };

    if (include_input) {
        // apply the create search choice
        $(selector).select2({
            minimumInputLength: mininput,
            ajax: ajax,
            createSearchChoice: csc,
            initSelection : initSel,
            placeholder: "Start typing…",
            allowClear: allow_clear
        });
    } else {
        // go without the create search choice option
        $(selector).select2({
            minimumInputLength: mininput,
            ajax: ajax,
            initSelection : initSel,
            placeholder: "Start typing…",
            allowClear: allow_clear
        });
    }
}
