---
layout: sidenav
title: Widgets
toc: true
highlight: false
---

Widgets are tools that allow you to embed DOAJ into your site. There are two widgets available:

1. A Simple Search widget which embeds a search box on your page. Upon submitting the search, the user is taken to their search results on DOAJ.
2. A Fixed Query widget which allows you to embed, into your site, a specific set of results from a predefined DOAJ search.

## Simple Search

Copy and paste the code below into your page where you want the search box to be displayed.

CODE SNIPPET AND EXAMPLE FROM https://doaj.org/widgets

## Fixed Query

Copy and paste the code below into your page where you want the widget to be displayed.

CODE SNIPPET AND EXAMPLE FROM https://doaj.org/widgets

### Configuring via QUERY_OPTIONS

There are a handful of options available, all are optional; omit them from `QUERY_OPTIONS` for the default behaviour.

The parameter `QUERY_OPTIONS` takes a subset of fields to define which results to retrieve. The example above displays the journals containing the word `medicine` in the title and in alphabetical order. Configuration via these `QUERY_OPTIONS` provides a simplified way to display results by keyword.

For more control over which results to display, we recommend configuring your query via the _Search_ page. Use the controls to find the results you want to show then click the _Share_ button and copy the text provided in the box below _Embed this search_ for inclusion on your page.

The widget can be resized to fit within available horizontal space. Use the `page_size` property to minimise its vertical requirement by reducing the number of results per page. 

Note: the vertical size can change depending on the number of results shown on each page.

You can only embed one fixed query widget per page. If you see strange characters in the results, try declaring the encoding in the `<head>` element of your HTML page by adding `<meta charset="utf-8">`.
  
| query_string    | <plain text> - any text you might put in the search box                                                                                                                                                                                                                                                                                       |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| query_field     | The field to query. Omit for any field, or specify one of these below    + bibjson.title - Title   + bibjson.keywords - Keywords   + index.classification- Subject   + index.issn.exact - ISSN   + bibjson.identifier.id - DOI   + index.country - Country of publisher   + index.language - Journal Language   + index.publisher - Publisher |
| sort_field      | + created_date - Date added to DOAJ (default) + index.unpunctitle.exact - Title                                                                                                                                                                                                                                                               |
| sort_direction  | + asc - Ascending (default) + desc - Descending                                                                                                                                                                                                                                                                                               |
| search_operator | + AND - AND the terms in the query string. (default) + OR - OR the terms in the query string.                                                                                                                                                                                                                                                 |
| search_type     | The type of result to show. Omit this property to show results of both type   + journal - Only show journals   + article - Only show articles                                                                                                                                                                                                 |
| page_size       | <integer> - how many results to show per page, 1+, (default 10)                                                                                                                                                                                                                                                                               |
| page_from       | <integer> - which result to start from initially, 0+, (default 0)                                                                                                                                                                                                                                                                             |
