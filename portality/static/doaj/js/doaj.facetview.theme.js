
/////////////////////////////////////////////////////////////////
// functions for use as plugins to be passed to facetview instances
////////////////////////////////////////////////////////////////

function doajFixedQueryWidgetPostRender(options, context) {
    doajToggleAbstract(options, context);
}


//////////////////////////////////////////////////////
// value functions for facet displays
/////////////////////////////////////////////////////


function publisherStatusMap(value) {
    if (applicationStatusMapping.hasOwnProperty(value)) {
        return applicationStatusMapping[value];
    }
    return value;
}


//////////////////////////////////////////////////////
// date formatting function
/////////////////////////////////////////////////////



//////////////////////////////////////////////////////
// fixed query widget generation
/////////////////////////////////////////////////////

var doajenvmap = {
    "http://localhost:5004" : "dev",
    "https://testdoaj.cottagelabs.com" : "test",
    "https://stagingdoaj.cottagelabs.com" : "staging"
};

function doajDetectCurrentEnv(){
    // Return env, if one of recognised locations, default to production.
    return doajenvmap[document.location.origin] || "production";
}

function doajGenFixedQueryWidget(widget_fv_opts){
    // Generates code for the fixed query widget

    var source = elasticSearchQuery({"options" : widget_fv_opts, "include_facets" : widget_fv_opts.include_facets_in_url, "include_fields" : widget_fv_opts.include_fields_in_url});

    // Code to get a version of jQuery
    var jq = '<script type="text/javascript">!window.jQuery && document.write("<scr" + "ipt type=\\"text/javascript\\" src=\\"http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js\\"></scr" + "ipt>"); </script>';

    // Get the env to serve the correct version of the widget file
    var env_suffix = "";
    var doaj_env = doajDetectCurrentEnv();
    if (doaj_env != "production") {
        env_suffix = "_" + doaj_env;
    }

    // Code to configure the widget
    var frag = '<script type="text/javascript">var doaj_url="'+ document.location.origin + '"; var SEARCH_CONFIGURED_OPTIONS=' + JSON.stringify(source) + '</script>';
    frag += '<script src="' + document.location.origin +'/static/widget/fixed_query' + env_suffix + '.js" type="text/javascript"></script><div id="doaj-fixed-query-widget"></div></div>';
    return jq + frag
}
