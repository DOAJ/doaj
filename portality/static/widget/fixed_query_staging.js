(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        $('#doaj-fixed-query-widget').load(doaj_url + "/static/widget/fixed_query_body_staging.html");
        $.ajax({
            type: "POST",
            crossDomain: true,
            url: doaj_url + "/fqw_hit",
            data: {embedding_page: window.location.href}
        })
    });
})();
