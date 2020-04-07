# doaj-templates

A static Jekyll site for doaj.org


## Install Jekyll

1. `gem install jekyll`

## Building the site

1. `git clone https://github.com/DOAJ/doaj-static.git`
2. `cd doaj-static`
3. `jekyll build`
4. Content will be found in `_site/`

## Updating & editing content

Most of the content of doaj.org’s static pages can be written in Markdown (`.md`) and modified in the following directories (representing a section of the site):
- `about/`
- `apply/`
- `data/`
- `support/`

Each `.md` file represents a single page. Each page includes YAML front matter which indicates: 
- the layout to be used for that page (for now, we only have `sidenav`) 
- the page title (displayed in an `<h1>` tag)
- whether or not we want a table of contents on the side
- whether or not the page should start with a highlight section (slightly darker background, as seen in the homepage’s search box)
