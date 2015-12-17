(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        $.getScript("http://localhost:5004/static/widget/fq_widget_depends_compiled.js", $('#doaj-fixed-query-widget').load("http://localhost:5004/static/widget/fixed_query_body.html"));
        });
})();
