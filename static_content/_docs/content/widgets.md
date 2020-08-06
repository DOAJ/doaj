Widgets are tools that allow you to embed DOAJ into your site. There are two widgets available:

1. A Simple Search widget which embeds a search box on your page. Upon submitting the search, the user is taken to their search results on DOAJ.
2. A Fixed Query widget which allows you to embed, into your site, a specific set of results from a predefined DOAJ search.

## Simple Search

Copy and paste the code below into your page where you want the search box to be displayed.

```html
<script src="https://doaj.org/static/widget/simple_search.js" type="text/javascript"></script>
<div id="doaj-simple-search-widget"></div>
```

## Fixed Query

Copy and paste the code below into your page where you want the widget to be displayed.

```html
<script type="text/javascript">
    !window.jQuery && document.write("<scr" + "ipt type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js\"></scr" + "ipt>");
</script>

<script type="text/javascript">
var doaj_url = "https://doaj.org";
var QUERY_OPTIONS = {
    query_string : 'medicine',                   // The plain-text query string
    query_field: 'bibjson.title',                // The field we are querying
    sort_field: 'index.unpunctitle.exact',       // Field to order results by
    sort_direction:  'asc',                      // Direction of sort "asc" | "desc"
    search_operator : 'AND',                     // Which sort operator to use "AND" | "OR"
    search_type: 'journal',                      // Which type to search upon (omit for both) "article" | "journal"
    page_size : 5,                               // How many results to show per widget page
    page_from : 0                                // Which result to start from
    }
</script>
<script src="https://doaj.org/static/widget/fixed_query.js" type="text/javascript"></script>
<div id="doaj-fixed-query-widget"></div>
```

### Configuring via `QUERY_OPTIONS`

The parameter `QUERY_OPTIONS` takes a subset of fields to define which results to retrieve. The example above displays, in alphabetical order, journals that contain the word `medicine` in the title. Configuration via these `QUERY_OPTIONS` provides a simplified way to display results by keyword. There are a handful of options available. All are optional; omit them from `QUERY_OPTIONS` for the default behaviour.

{:.tabular-list}
- `query_string`
  - Accepts plain text: any text you might put in the search box
- `query_field`
  - The field to query. Omit to search in any field, or specify one of these:
      - `bibjson.title`: title
      - `bibjson.keywords`: keywords
      - `index.classification`: subject
      - `index.issn.exact`: ISSN
      - `bibjson.identifier.id`: DOI
      - `index.country`: country of publisher
      - `index.language`: journal language
      - `index.publisher`: publisher name
- `sort_field`
    - `created_date`: sort by date added to DOAJ (default)
    - `index.unpunctitle.exact`: sort by title
- `sort_direction`
    - `asc`: ascending (default)
    - `desc`: descending
- `search_operator`
    - `AND`: use AND for the terms in the query string (default)
    - `OR`: use OR for the terms in the query string
- `search_type`
  - The type of result to show. Omit this property to show results of both type    
      - `journal`: only show journals
      - `article`: only show articles
- `page_size`
  - `integer`: how many results to show per page, 1 or more (default: 10)
- `page_from`
  - `integer`: which result to start from initially, 0 or higher, (default 0)


For more control over which results to display, configure your query on the [Search](/search/journals/) page. Use the controls to find the results you want to show then click the 'Share' button and copy the shortened URL provided for inclusion on your page.

The widget can be resized to fit within available horizontal space. Use the `page_size` property to minimise its vertical requirement by reducing the number of results per page.

Notes: The vertical size can change depending on the number of results shown on each page. You can only embed one fixed query widget per page. If you see strange characters in the results, try declaring the encoding in the `<head>` element of your HTML page by adding `<meta charset="utf-8">`.
