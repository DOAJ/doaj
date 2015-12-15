(function() {

    // Localize jQuery variable
    //var jQuery;

    /******** Load jQuery if not present *********/
    /*
    if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.9.1') {
        var script_tag = document.createElement('script');
        script_tag.setAttribute("type","text/javascript");
        script_tag.setAttribute("src",
            "https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js");
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
    */
    main();

    /******** Called once jQuery has loaded ******/
    function scriptLoadHandler() {
        // Restore $ and window.jQuery to their previous values and store the
        // new jQuery in our local jQuery variable
        jQuery = window.jQuery.noConflict(true);
        // Call our main function
        main();
        //loadWidgetScripts(main);
    }


/*    function loadWidgetScripts(callback){
        // Load the scripts the widget requires
        jQuery.when(
            jQuery.getScript('http://localhost:5004/static/portality/vendor/facetview2/es.js'),
            jQuery.getScript('http://localhost:5004/static/portality/vendor/facetview2/bootstrap2.facetview.theme.js'),
            jQuery.getScript('http://localhost:5004/static/doaj/js/doaj.facetview.theme.js'),
            jQuery.getScript('http://localhost:5004/static/portality/vendor/facetview2/jquery.facetview2.js'),

            jQuery.getScript('http://localhost:5004/static/doaj/js/available_facetviews/public.fixedquerywidget.facetview.js'),
            jQuery.getScript('http://localhost:5004/static/doaj/js/doaj.js'),
            jQuery.getScript('http://localhost:5004/static/doaj/js/facetview_results_render_callbacks.js')
        ).done(callback);
    }*/


    /******** Our main function ********/
    function main() {
        jQuery(document).ready(function($) {
            $('#doaj-fixed-query-widget').load("http://localhost:5004/static/widget/fixed_query_body.html");
        });
    }
})();
