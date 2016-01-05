(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        $('#doaj-fixed-query-widget').load(doaj_url + "/static/widget/fixed_query_body_dev.html");
        });
})();
