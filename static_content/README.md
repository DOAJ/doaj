# doaj-templates

Jekyll-based static pages for the new doaj.org. 

[![Netlify Status](https://api.netlify.com/api/v1/badges/6c8421b5-baef-482e-a9ae-729954cec42f/deploy-status)](https://app.netlify.com/sites/doaj-static/deploys)

## Install Jekyll

Ruby is required.

1. `gem install jekyll`

## Running the site locally

1. `git clone https://github.com/DOAJ/doaj.git`
2. `git checkout feature/af_redesign__static_content`
3. `cd doaj/static_content/`
4. `jekyll s`
5. Navigate to `http://127.0.0.1:4000` in your browser
6. You must make changes locally (and not via Github) to see them.

## Building the site

1. `git clone https://github.com/DOAJ/doaj.git`
2. `cd doaj/static_content/`
3. `jekyll build`
4. Compiled static HTML, CSS, & JS will be found in `_site/`

## Updating static content & data

Each static page is represented by a single `.md` file.

Most of the content of doaj.org’s pages can be edited in either Markdown (`.md`) or input into a database-like YAML file (`.yml`). 

### Markdown static pages

Static content is usually long-form, unstructured texts, as seen in the Data documentation and About pages.

This content is found in the following directories (each representing a section of the site):

- `about/`
  - `index.md`: the main About section page (_Mission_, _History_)
  - `advisory-board-council.md`
  - `faq.md`
  - `team-ambassadors.md`
  - `volunteers.md`
- `apply/`
  - `guide.md`
  - `seal.md`
  - `transparency.md`
  - `why-index.md`
- `docs/`
  - `openurl.md`
  - `public-data-dump.md`
  - `widgets.md`
  - `xml.md`
- `support/`
  - `index.md`: the main Support section page (_Support DOAJ_)
  - `publisher-supporters.md`
  - `sponsors.md`
  - `supporters.md`

Each static Markdown page includes YAML front matter at the top of the document which indicates:

- `layout`:
  - the layout to be used for that page
  - for now, we only have `sidenav`, `data`, `two-col-data`: **TO BE RENAMED**
- `title`:
  - the page title displayed in `<h1>` and `<title>` tags
- `toc` (`true` or `false`):
  - whether or not we want a table of contents on the side, for in-page navigation
- `highlight` (`true` or `false`):
  - whether or not the page should start with a highlight section (slightly darker background, as seen in the homepage’s search box)

### Data files

Whenever we have structured content that could be stored in a database (e.g. records of people or organisations with metadata), we use Jekyll’s _data files_. 

Data files can be in `CSV`, `YAML`, or `JSON` and are uploaded in the **`_data/`** directory (not to be confused with the `data/` section).

We are currently using the `YAML` (`.yml`) format, but are not restricted to it.

The following information is represented in data files:
- _About_ section
  - Advisory Board: `advisory-board.yml`
  - Council: `council.yml`
  - Team: `team.yml`
  - Ambassadors: `ambassadors.yml`
  - Volunteers: `volunteers.yml`
- _Support_ section
  - Publisher supporters: `publisher-supporters.yml`
  - Sponsors: `sponsors.yml`
  - Supporters: `supporters.yml`
- Other
  - Promotional snippet (in page sidebar): `promo.yml`

**Make sure** to follow the indentation and line breaks of already-existing records when adding a new line or entry.

---

# Tools for writing in Markdown 

- [Table generator](https://www.tablesgenerator.com/markdown_tables)
- [Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) 

Advanced tools: 
- [StackEdit](https://stackedit.io/), an in-browser Markdown editor (might be useful for much longer text and helps with the creation of UML diagrams) 
- [Typora](https://typora.io/), a downloadable Markdown editor app

---

# TODO

- [x] Rename and harmonise base templates (`sidenav`, `data`) 
- [ ] Add a promo post category so we can target content for specific pages
- [ ] Finish inputting data in `volunteers.yml`
- [x] Add & style bio photos for `team.yml` + `team-ambassadors.md`
- [ ] Add appropriate Paypal forms for each page of the Support section 
- [x] Make menu responsive
- [ ] Create Footer content pages (legal / admin pages)
- [ ] Create Thank you pages (application form, Paypal support form) 
- [ ] Check content for broken or missing links, typos
- [ ] Review all content with the team with Hypothesis & update text
- [ ] Run HTML5 validator on all pages & fix errors 
- [ ] Run Lighthouse’s automated a11y tests on all pages & fix errors
