(function() {
    // Load the widget's js scripts then HTML content. We assume jQuery is available.
    jQuery(document).ready(function($) {
        $('body').load(doaj_url + "/static/widget/fixed_query_body.html");
        $('#doaj-fixed-query-widget').appendChild($('<div class="facetview"></div>'));
        $.ajax({
            type: "POST",
            crossDomain: true,
            url: doaj_url + "/fqw_hit",
            data: {embedding_page: window.location.href}
        })
    });
})();
