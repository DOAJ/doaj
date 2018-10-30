jQuery(document).ready(function($) {

    function toggleMoreInformation(options, context) {
        // toggle the abstracts
        $('.more_information', context).hide();
        $(".more_information_action", context).unbind("click").click(function(event) {
            event.preventDefault();
            var el = $(this);
            $('.more_information[data-id="' + el.attr("data-id") + '"]').slideToggle(300);
            return true;
        });
    }

    function backgroundJobResult(options, resultobj) {

        var firstRow = "";
        if (resultobj.action) {
            firstRow += "<strong>" + resultobj.action + "</strong>";
        }
        if (resultobj.user) {
            firstRow += " by <strong>" + resultobj.user + "</strong>";
        }
        if (resultobj.status) {
            var color = "#000088";
            if (resultobj.status === "complete") {
                color = "#008800"
            } else if (resultobj.status === "error") {
                color = "#880000";
            } else if (resultobj.status === "cancelled") {
                color = "#b47e18";
            }
            firstRow += " status: <strong style='color: " + color + "'>" + resultobj.status + "</strong>";
        }

        var dateRow = "";

        // add the date added to doaj
        if (resultobj.created_date) {
            dateRow += "Job Created: " + humanDateTime(resultobj.created_date) + "<br>";
        }
        if (resultobj.last_updated) {
            dateRow += "Job Last Updated: " + humanDateTime(resultobj.last_updated) + "<br>";
        }

        var paramsBlock = "";
        if (resultobj.params) {
            paramsBlock += "<strong>Parameters:</strong><br>";
            for (var key in resultobj.params) {
                var val = resultobj.params[key];
                if ($.isArray(val)) {
                    val = val.join(', ');
                }
                paramsBlock += key + " -- " + escapeHtml(val) + "<br>";
            }
        }

        var refsBlock = "";
        if (resultobj.reference) {
            paramsBlock += "<strong>Reference:</strong><br>";
            for (var key in resultobj.reference) {
                var val = resultobj.reference[key];
                if ($.isArray(val) || $.isPlainObject(val))
                {
                    val = JSON.stringify(val);
                }
                refsBlock += key + " -- " + escapeHtml(val) + "<br>";
            }
        }

        var auditBlock = "";
        if (resultobj.audit) {
            auditBlock += "<strong>Audit Messages:</strong><br>";
            for (var i = 0; i < resultobj.audit.length; i++) {
                var audit = resultobj.audit[i];
                auditBlock += audit.timestamp + " -- " + escapeHtml(audit.message) + "<br>";
            }
        }

        var expandBlock = "<div data-id='" + resultobj.id + "' class='more_information'>";
        expandBlock += paramsBlock;
        expandBlock += refsBlock;
        expandBlock += auditBlock;
        expandBlock += "</div>";

        // start off the string to be rendered
        var result = options.resultwrap_start;

        // start the main box that all the details go in
        result += "<div class='row-fluid'><div class='span12'>";

        result += firstRow + "<br>";
        result += "Job ID: " + resultobj.id + "<br>";
        result += dateRow + "<br>";

        result += '<a href="#" data-id="' + resultobj.id + '" class="more_information_action">More Information</a><br>';
        result += expandBlock;

        // close off the result with the ending strings, and then return
        result += "</div></div>";
        result += options.resultwrap_end;

        return result;
    }

    $('.facetview.background_jobs').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/background,job/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        render_result_record: backgroundJobResult,

        post_render_callback: toggleMoreInformation,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': 'action.exact', 'display': 'Action'},
            {'field': 'user.exact', 'display': 'Submitted By'},
            {'field': 'status.exact', 'display': 'Status'}
        ],

        search_sortby: [
            {'display':'Created Date','field':'created_date'},
            {'display':'Last Modified Date','field':'last_updated'}
        ],

        sort : [
            {"created_date" : {"order" : "desc"}}
        ],

        searchbox_fieldselect: [
            {'display':'ID','field':'id.exact'},
            {'display':'Action','field':'action.exact'},
            {'display':'User','field':'user.exact'},
            {'display':'Status','field':'status.exact'}
        ],

        page_size : 25,
        from : 0
    });
});
