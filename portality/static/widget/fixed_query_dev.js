"use strict";
(function() {
// Localize jQuery variable
let jQuery;

/******** Load jQuery if not present *********/
if (window.jQuery === undefined || window.jQuery.fn.jquery !== "1.9.1") {
    let script_tag = document.createElement("script");
    script_tag.setAttribute("type","text/javascript");
    script_tag.setAttribute("src",
        "http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js");
    if (script_tag.readyState) {
      script_tag.onreadystatechange = function () { // For old versions of IE
          if (this.readyState === "complete" || this.readyState === "loaded") {
              scriptLoadHandler();
          }
      };
    } else { // Other browsers
      script_tag.onload = scriptLoadHandler;
    }
    // Try to find the head, otherwise default to the documentElement
    (document.getElementsByTagName("head")[0] || document.documentElement).appendChild(script_tag);
} else {
    // The jQuery version on the window is the one we want to use
    // jQuery = window.jQuery;
    main();
}

/******** Called once jQuery has loaded ******/
function scriptLoadHandler() {
    // Restore $ and window.jQuery to their previous values and store the
    // new jQuery in our local jQuery variable
    // jQuery = window.jQuery.noConflict(true);
    // Call our main function
    main();
}

/******** Our main function ********/
function main() {
    $(document).ready(function($) {

        let head = document.head || document.getElementsByTagName('head')[0];

        let scr  = document.createElement('script');
        scr.src = 'https://unpkg.com/feather-icons';
        scr.async = false;
        scr.defer = false;
        head.insertBefore(scr, head.firstChild);

        scr  = document.createElement('script');
        scr.src = 'http://localhost:5004/static/widget/fq_widget_depends_compiled.js';
        scr.async = false;
        scr.defer = false;
        head.insertBefore(scr, head.firstChild);

        scr  = document.createElement('script');
        scr.src = 'http://localhost:5004/static/widget/fixed_query_src_edges.js';
        scr.async = false;
        scr.defer = false;
        head.insertBefore(scr, head.firstChild);

        scr = document.createElement('link');
        scr.rel = 'stylesheet';
        scr.href = 'http://localhost:5004/static_content/_site/css/main.css';
        head.insertBefore(scr, head.firstChild);

        $('#doaj-fixed-query-widget').append($('<div class="facetview"></div>'));

        $.ajax({
            type: "POST",
            crossDomain: true,
            url: doaj_url + "/fqw_hit",
            data: {embedding_page: window.location.href}
        })
    });
}

})(); // We call our anonymous function immediately

//# sourceURL=http://localhost:5004/static/widget/fixed_query_body_dev_edges.html
