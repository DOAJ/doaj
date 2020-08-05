# ES query library examples

## Creating a query:

    var q = es.newQuery();

This creates the most basic kind of ES query, which is a match-all query.  To convert a query into a plain 
javascript object the correct structure to be sent to ES, use

    q.objectify();
    
So you can output your query, as follows:

    > JSON.stringify(q.objectify())
    
    < "{"query":{"match_all":{}}}"
    
To create a more advanced query, you can pass in parameters during construction:

    var q = es.newQuery({
        size: 100,
        from: 25
        aggs: [<list of aggregations>],
        must: [<list of must filters>],
        queryString: "query string",
        sort: [<sort options>]
    });
    
See below for information about creating and adding filters, aggregations and sort options.  Using just the simple options:

    > var q = es.newQuery({size: 100, from: 25, queryString: "test"});
    > JSON.stringify(q.objectify())
    
    < "{"query":{"query_string":{"query":"test","default_operator":"OR"}},"size":100,"from":25}"

## Adding/Removing Aggregations

The following aggregations are supported:

* terms: es.newTermsAggregation,
* range: es.newRangeAggregation,
* geo_distance: es.newGeoDistanceAggregation,
* date_histogram: es.newDateHistogramAggregation,
* stats: es.newStatsAggregation,
* cardinality: es.newCardinalityAggregation

All aggregations have their own specific details, as per the ES documentation.  They are all constructed in a similar
way; for example a simple terms aggregation:

    > var a = es.newTermsAggregation({name: "myterms", field: "myfield.exact", size: 25})
    > JSON.stringify(a.objectify())
    
    < "{"myterms":{"terms":{"field":"myfield.exact","size":25,"order":{"_count":"desc"}}}}"

Aggregations can be added during construction, or via addAggregation on the query object:

    > q.addAggregation(a);
    > JSON.stringify(q.objectify())
    
    < "{"query":{"query_string":{"query":"test","default_operator":"OR"}},"size":100,"from":25,"aggs":{"myterms":{"terms":{"field":"myfield.exact","size":25,"order":{"_count":"desc"}}}}}"

Aggregations can also be removed by name:

    > q.removeAggregation("myterms")
    > JSON.stringify(q.objectify())
    
    < "{"query":{"query_string":{"query":"test","default_operator":"OR"}},"size":100,"from":25}"
    
## Adding/Removing/Listing Filters

es.js only supports MUST filters, which means queries of the form

    {
        "query" : {
            "bool": {
                "must" : [<filters go here>]
            }
        }
    }

The following filters are available:

* query_string: es.newQueryString,
* term: es.newTermFilter,
* terms: es.newTermsFilter,
* range: es.newRangeFilter,
* geo_distance_range: es.newGeoDistanceRangeFilter

All filters have their own specific details, as per the ES documentation.  They are all constructed in a simlar way; for
example a simple terms filter:

    > var f = es.newTermsFilter({field: "myfield", values: ["value1", "value2"]})
    > JSON.stringify(f.objectify())
    
    < "{"terms":{"myfield":["value1","value2"]}}"
    
Filters can be added during construction, or via addMust on the query object:

    > q.addMust(f)
    > JSON.stringify(q.objectify())
    
    < "{"query":{"filtered":{"filter":{"bool":{"must":[{"terms":{"myfield":["value1","value2"]}}]}},"query":{"query_string":{"query":"test","default_operator":"OR"}}}},"size":100,"from":25}"
    
Note that es.js creates filtered queries where possible unless otherwise specified in the constructor.

Once a query has filters attached to it, they can be listed and filtered using listMust on the query object.  You pass a partial filter object to the listMust function and it will return to you a list
of filters which match the provided criteria:

    > q.listMust(es.newTermsFilter({field: "myfield"}))
    
    < [TermsFilter]

You can also remove a filter using removeMust on the query object.  Again, you pass a partial filter object to removeMust, and any matching filters are removed (and the number of removed filters
is returned):

    > q.removeMust(es.newTermsFilter({field: "myfield"}))
    
    < 1
    
    > JSON.stringify(q.objectify())
    
    < "{"query":{"query_string":{"query":"test","default_operator":"OR"}},"size":100,"from":25}"


# Adding Sort Options

You can specify sort options using the es.newSort object:

    > var s = es.newSort({field: "myfield", order : "asc"})
    > JSON.stringify(s.objectify())

    < "{"myfield":{"order":"asc"}}"
    
Set the sort criteria on the query with setSortBy:

    > q.setSortBy(s)
    > JSON.stringify(q.objectify())

    < "{"query":{"query_string":{"query":"test","default_operator":"OR"}},"size":100,"from":25,"sort":[{"myfield":{"order":"asc"}}]}"
    
You can also interact with the sort options using the following functions:

* addSortBy - add another sort criteria to the list of sort criteria (as the last element)
* prependSortBy - add another sort criteria to the list of sort criteria (as the first element)
* removeSortBy - removes any sort criteria on a matching field.