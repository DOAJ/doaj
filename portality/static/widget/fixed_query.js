(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        console.log("this is js");
        $('#doaj-fixed-query-widget').load(doaj_url + "/static/widget/fixed_query_body.html");
        $.ajax({
            type: "POST",
            url: doaj_url + "/fqw_hit",
            data: {embedding_page: window.location.href}
        })
    });
})();
