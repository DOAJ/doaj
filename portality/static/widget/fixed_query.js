"use strict";
let script = document.querySelector("script[src$='/static/widget/fixed_query.js']");
let parser = document.createElement('a');
parser.href = script.attributes.src.value;
var doaj_url = parser.protocol + '//' + parser.host;

    let jQuery;

(function(){
    /******** Load jQuery if not present *********/
    if (window.jQuery === undefined || window.jQuery.fn.jquery !== "1.9.1") {
        let script_tag = document.createElement("script");
        script_tag.setAttribute("type","text/javascript");
        script_tag.setAttribute("src", doaj_url + '/static/vendor/jquery-3.4.1/jquery-3.4.1.min.js');
        if (script_tag.readyState) {
            script_tag.onreadystatechange = function () { // For old versions of IE
                if (this.readyState === "complete" || this.readyState === "loaded") {
                    main();
                }
            };
        } else { // Other browsers
            script_tag.onload = main;
        }
        // Try to find the head, otherwise default to the documentElement
        (document.getElementsByTagName("head")[0] || document.documentElement).appendChild(script_tag);
    } else {
        // The jQuery version on the window is the one we want to use
        // jQuery = window.jQuery;
        main();
    }
})();

    /******** Load scripts *********/

    function loadCustomScript() {
        let head = document.head || document.getElementsByTagName('head')[0];

        let scr = document.createElement('link');
        scr.rel = 'stylesheet';
        scr.href = doaj_url + '/static/doaj/css/fq_widget.css';
        head.appendChild(scr);

        scr = document.createElement('script');
        scr.src = doaj_url + '/static/vendor/feather-4.28.0/feather.min.js';
        scr.async = false;
        scr.defer = false;
        head.appendChild(scr);

        scr = document.createElement('script');
        scr.src = doaj_url + '/static/widget/fq_widget_depends_compiled.js';
        scr.async = false;
        scr.defer = false;
        head.appendChild(scr);

        scr = document.createElement('script');
        scr.src = doaj_url + '/static/widget/fixed_query_src.js';
        scr.async = false;
        scr.defer = false;
        head.appendChild(scr);
    }

    /******** Our main function ********/
    function main() {
        loadCustomScript();


            $('#doaj-fixed-query-widget').append($('<div class="facetview"></div>'));

            $.ajax({
                type: "POST",
                crossDomain: true,
                url: doaj_url + "/fqw_hit",
                data: {embedding_page: window.location.href}
            });

    }