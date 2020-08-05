# Edges

Data Visualisation Suite.  

* Load data from a variety of sources: elastic, static data files
* Query and filter data
* Display data using a variety of components: filter selectors, search widgets, graphs and charts
* Handle user interactions, and re-render visualisations

Extensible and flexible.


## Sources and Dependencies

Edges has a critical dependency on jQuery (tested to <= 0.12.x).

In addition, each component may have its own dependencies.  All dependencies that are needed by the current components can be found in `/vendor`

Once you have your base dependencies chosen, you then need to include the core Edges library `/src/edges.js`

Depending on your data sources, you will need one or both of the following

* `/src/es.js` for elastic (or `es5x.js` if using version 5 or above)
* `/src/edges.csv.js` for static csvs

Components are then available in `/components` and renderers available in `/renderers`

There is a full build available in `/build/releases/current`


## Edges instance structure

Each deployment of Edges consists of constructing the core Edges object around your parameters.  Parameters are documented inline
so you should check the source for full details.

The most basic setup would be something like this:

```
e = edges.newEdge({
    selector: "#edges",
    template: edges.bs3.newTabbed(),
    
    components: [
        edges.newSimpleLineChart({
            id: "line_chart",
            display: "Line Chart",
            dataSeries: [
                {
                    key: "Series 1",
                    values: [
                        {label: 1980, value: 100},
                        {label: 1981, value: 120},
                        {label: 1982, value: 122},
                        {label: 1983, value: 130}
                    ]
                },
                {
                    key: "Series 2",
                    values: [
                        {label: 1980, value: 200},
                        {label: 1981, value: 220},
                        {label: 1982, value: 222},
                        {label: 1983, value: 230}
                    ]
                }
            ],
            category: "tab",
            renderer : edges.nvd3.newSimpleLineChartRenderer({
                xTickFormat: '.0f',
                yTickFormat: ',.0f'
            })
        })
    ]
});
```

This specifies a **selector** which identifies the HTML element into which the Edge will be inserted.  It then specifies a **template** which
is an optional feature which will render an HTML template into the selected element.  If not specified, you are responsible for providing
your own template explicitly in your own HTML.

Finally it specifies a list of **components** which define the actual functionality of the Edge.  Each component, in turn, specifies
a **renderer** which is responsible for visualising the data in the component.


You can bind an Edge to one or more data sources as follows:

For elastic:

```
e = edges.newEdge({
    search_url: "http://localhost:9200/allapc/institutional/_search",
    ...
});
```

For static CSVs:

```
e4 = edges.newEdge({
    staticFiles : [
        {
            id: "mycsv",
            url: "http://localhost:5029/static/vendor/edges/docs/static.csv",
            datatype: "text"
        }
    ]
});
```

You can see more detailed examples of how Edges is initialised in `/docs/example.js`


## Edges lifecycle

When a new Edge is constructed, the following processes happen:

1. The page template is rendered (if provided)
2. All components are instructed to draw themselves.  This means they can provide a "loading" state to the user at that point.
3. Any static resources are loaded (if provided)
4. Any initial elastic query is executed (if a search_url is available)
    * After the initial query is executed, any secondary queries are constructed and executed
5. All components are instructed to synchronise themselves with the core data
6. All components are instructed to render themselves.

At this point processing is paused, as the full visualisation will have been displayed to the user.  The user may then interact with
any interactive components on the page.  The details of the interaction are dependent on the components involved, but any component may
trigger a "cycle" of the core data, as follows:

1. The component modifies one or more filtering/querying aspects of the Edge
2. Any static resources have the new filters applied to them
3. Any elastic binding has the new query run
    * After this query has completed, any secondary queries are regenerated and executed
5. All components are instructed to synchronise themselves with the core data
6. All components are instructed to render themselves.

The sequence can be re-executed as many times as the user desired, allowing the entire system to be a fully responsive visualisation
environment which maintains complete consistency across all components for the data that the user is focused on.


## Working with Elastic



