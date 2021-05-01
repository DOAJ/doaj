(function() {

// Localize jQuery variable
var jQuery;
// doaj_url values:
// dev: 'http://localhost:5004'
// test: 'https://testdoaj.cottagelabs.com'
// production: 'https://www.doaj.org'
let doaj_url = 'https://testdoaj.cottagelabs.com';

/******** Load jQuery if not present *********/
if (window.jQuery === undefined || window.jQuery.fn.jquery !== '3.4.1') {
    var script_tag = document.createElement('script');
    script_tag.setAttribute("type","text/javascript");
    script_tag.setAttribute("src", doaj_url + '/static/vendor/jquery-3.4.1/jquery-3.4.1.min.js');
    if (script_tag.readyState) {
      script_tag.onreadystatechange = function () { // For old versions of IE
          if (this.readyState == 'complete' || this.readyState == 'loaded') {
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
        let head = document.head || document.getElementsByTagName('head')[0];

        let scr  = document.createElement('script');
        scr.src = doaj_url + '/static/vendor/feather/feather.min.js';
        scr.async = false;
        scr.defer = false;
        head.insertBefore(scr, head.firstChild);

        scr = document.createElement('link');
        scr.rel = 'stylesheet';
        scr.href = doaj_url + '/static/doaj/css/simple_widget.css';
        head.insertBefore(scr, head.firstChild);

        $('#doaj-simple-search-widget').load(doaj_url + '/static/widget/simple_search_body.html', () => {
            $("form").attr("action", doaj_url + "/search");
            feather.replace();
        });

    });
}

})();