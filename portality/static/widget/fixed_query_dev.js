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
    jQuery = window.jQuery;
    main();
}

/******** Called once jQuery has loaded ******/
function scriptLoadHandler() {
    // Restore $ and window.jQuery to their previous values and store the
    // new jQuery in our local jQuery variable
    jQuery = window.jQuery.noConflict(true);
    // Call our main function
    main();
}

/******** Our main function ********/
function main() {
    jQuery(document).ready(function($) {
        let url = doaj_url + "/static/widget/fixed_query_body_dev_edges.html";
        $("#doaj-fixed-query-widget").load(url);
        $.ajax({
            type: "POST",
            crossDomain: true,
            url: doaj_url + "/fqw_hit",
            data: {embedding_page: window.location.href}
        }).done(
            (response) => {console.log("ajax has been called: " + response);}
        );
    });
}

})(); // We call our anonymous function immediately

//# sourceURL=http://localhost:5004/static/widget/fixed_query_body_dev_edges.html
