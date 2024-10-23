# Template directory structure

Every level of the template directory structure can look like this:

```
├── base.html => the base file for all templates in this level or below.  It must inherit from the template in the level above
├── [sub level]  => All template files associated with the next level down in the hierarcy.  For example, the `management` directory under the base
├── _[common infrastructure] => application forms, email templates, anything else that is used in many places at this level or below
├── includes => Any files that are included generally at this level or below
├── layouts => any layouts that are used generally at this level or below
```

For example

```
├── base.html
├── management
    ├── base.html => extends ../base.html
    ├── maned
    ├── editor
    ├── assed
├──public
    ├── layouts
         ├── static-pages.html
    ├── publisher
├── _application_forms
├── _emails
├── includes
     ├── _cookie-consent.html
├── layouts
    ├── sidenav.html
```

Files should be named according to these rules:

* If a file is called directly by a view, it should be named with `-` providing any spaces in the name. For example `static-pages.html`
* If a file is included or imported within a template, it should be named with a `_` prefix and `-` providing any spaces in the name.  For example: `_edges-common-css.html`
* If a file has a close relationship with another template file, it may be prefixed with an `_` that template's name, and separated with a `_`.  For example: `_static-pages_no-sidenav.html`


# Block hierarchy

