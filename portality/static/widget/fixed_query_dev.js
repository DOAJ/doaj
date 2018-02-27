(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        $('#doaj-fixed-query-widget').load(doaj_url + "/static/widget/fixed_query_body_dev.html");
        $.ajax({
            type: "POST",
            url: doaj_url + "/fqw_hit",
            headers: {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache"
            },
            processData: false,
            data: {embedding_page: window.location.href}
        })
    });
})();
