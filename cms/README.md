# DOAJ CMS

This directory in the source contains all the content, data and other assets that are managed separately from the
main software.  This is:

1. **assets** - the static assets, such as images, that are part of the content
2. **data** - YAML files of structured data to be used in the informational parts of the site
3. **pages** - a directory structure of markdown files which reflect the structure of the pages on the DOAJ site
4. **sass** - the source SASS which is compiled into the main site CSS

See below for details for each of these.

## Compiling content

All the markdown and SASS needs to be compiled to HTML and CSS respectively before the site can function.  This can 
be done in several ways:

### For developers on their local machines

The Markdown and SASS is compiled automatically each time DOAJ restarts, provided you have set `DEBUG=True` in your
developer configuration.

The content **will not** recompile automatically if you are not in debug mode.  The prevents it from happening on live
if the system is restarted unexpectedly.

If you think your static pages or CSS is out of date, just restart the app, and everything will be updated.

### On demand

You can compile the Markdown and SASS directly using scripts provided:

To compile only the static content:

```
python portality/cms/build_fragments.py
```

Note that if you compile the static content, the updated pages will be available immediately in your running app (if you
are a developer running this locally).  If you have made any changes to the front matter or the data files, though, 
these will not be picked up until the app is restarted, as data is loaded into memory on startup and not re-read until
the next startup.


To compile only the SASS:

```
python portality/cms/build_sass.py
```

### Compiling the CSS for the widgets

The CSS for the widgets is compiled separately from the main CSS and committed to the codebase. This is so that we don't
 break the widgets accidentally via a change to the main CSS. To run this process add the `--widgets` or `-w` argument
(for both the Fixed Query Widget and the Simple Search Widget):

```
python portality/cms/build_sass.py -w
```

Keep in mind the CSS isn't the only requirement for the fixed query widget - collating the JavaScript requires you to run the shell script `portality/static/widget/fixed_query_build.sh`

## Managing Assets

Static assets include images and other content-like objects that form part of the site content, such as downloadable
files.

It is recommended that the structure of this directory follow a sensible pattern, though there are no constraints.  For
example:

* **img** for images
* **downloads** for downloadable files
* etc

Once you place some content in the **assets** directory, it becomes available to be linked or included into the main
DOAJ site.  You can link to a static asset as follows in the Markdown files:

```
Here's a [link to a download](/downloads/file.pdf).
```

If you are adding an image to attach to a record in a data file (e.g. an Ambassador's photo) then you should put
the image in the correct folder (e.g. `assets/img/ambassadors`) and then you only need to include the name of the image
file in the YAML data file.  For example:

```
- name: P. Enguine
  region: Antarctica
  bio: "Stands around in the cold a lot"
  photo: "p-enguine.png"
```

## Managing Data

Data files MUST be in `YAML` and are uploaded in the **`cms/data/`** directory.

If you wish to add a data file in an alternative format (`csv` or `json` for example, you will need to talk to the developers
to add this capability)

The following information is represented in data files:

- _About_ section
  - Advisory Board: `advisory-board-council.yml`
  - Team: `team.yml`
  - Ambassadors: `ambassadors.yml`
  - Volunteers: `volunteers.yml`
  - Editorial Sub Committee: `editorial-subcommittee.yml`
- _Support_ section
  - Publisher supporters: `publisher-supporters.yml`
  - Sponsors: `sponsors.yml`
  - Supporters: `supporters.yml`
- Other
  - Promotional snippet (in page sidebar): `promo.yml`
  - Overall Site Navigation: `nav.yml`

**Make sure** to follow the indentation and line breaks of already-existing records when adding a new line or entry.


## Managing Static Content

Each static page is represented by a single `.md` file.

Static content is usually long-form, unstructured texts, as seen in the Data documentation and About pages.

This content is found in the following directories (each representing a section of the site):

- `about/`: pages that appear in the `/about` URL space and under the "About" menu
- `apply/`: pages that appear in the `/apply` URL space and under the "Apply" menu
- `docs/` : pages that appear in the `/docs` URL space and under the "Documentation" menu
- `legal/` : pages that appear in the root of the URL space (i.e. `doaj.org/`) and appear under the "Legal & Admin" section of the footer
- `support/`: pages that appear in the `/support` URL space and under the "Support" menu

Each static Markdown page includes YAML front matter at the top of the document which indicates:

- `title`:
  - the page title displayed in `<h1>` and `<title>` tags
- `section`:
  - the section title displayed above the page title
- `highlight` (`true` or `false`):
  - whether or not the page should start with a highlight section (slightly darker background, as seen in the homepage’s search box)
  - if `false` you can omit this
- `layout`:
  - the layout to be used for that page
  - you may use `sidenav` or `no-sidenav`
- `include`:
  - reference to a template file to include after the main content
  - works on all layout types
  - use this, for example, to include the data template for the list of volunteers on the volunteers page
- `aside`:
  - reference to a template file to include as an aside
  - only applicable to layout type `no-sidenav`
- `preface`:
  - reference to a template file to include first on the page before the main content
  - Only applicable to layout type `sidenav`
- `sidenav_include`:
  - reference to a template file to include in the sidenav
  - Only applicable to layout type `sidenav`
- `sticky_sidenav` (`true` or `false`):
  - If the `toc` is present, should it stick to the user's page.  Activates scroll-spy for automatic highlighting.
  - Only applicable to layout type `sidenav`
  - if `false` you can omit this
- `toc` (`true` or `false`):
  - whether or not we want a table of contents on the side, for in-page navigation
  - Only applicable to layout type `sidenav`
  - if `false` you can omit this
  

### Adding new pages

You can add a new Markdown file in the appropriate directory to create new page content.

Once this is done, you must let the developers know so that page can be attached to the website.

New pages in the `pages` directory cannot automatically be added to the website.


### Tools for writing in Markdown 

- [Table generator](https://www.tablesgenerator.com/markdown_tables)
- [Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) 

Advanced tools: 
- [StackEdit](https://stackedit.io/), an in-browser Markdown editor (might be useful for much longer text and helps with the creation of UML diagrams) 
- [Typora](https://typora.io/), a downloadable Markdown editor app


## Managing SASS

SASS should be built in the normal way in the `sass` directory.  There should be a single `main.scss` file which can be
compiled to the site's css.  This is done automatically on deployment, or via the `portality.cms.build_sass.py` script.

If you wish to have more than one top level SASS file (that is, in addition to `main.scss`) this will need to be added
to the build script too.