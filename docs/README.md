# Generated Documentation

The scripts and configuration in this directory allow us to auto-generate documentation and publish it to the doc site.

Once you have run any of the scripts below, you must push to the `master` branch of the doc site to publish your documentation updates.  They will then appear on the doc site at https://doaj.github.io/doaj-docs 

## Generating documentation for the current branch for publish to the doc site

The default setup for generating documentation assumes that you have a repo called `doaj-docs` that is a sibling directory to your `doaj` code directory.  That is

```
- My Code
  + doaj
  + doaj-docs
  \ etc
```

If this is not the case then you will either need to change your local directory layout or follw the instructions in **Generating documentation for local use** below.

It will also assume that the Testbook is being deployed for the current branch on `https://testdoaj.cottagelabs.com`.  If you are deploying on a different server, you will need to generate the testbook with custom arguments as per **Generating documentation for local use** below.

You can run the default documentation generation for any branch to be published to the doc site from the `docs` directory with

```bash
bash gendocs.sh
```

Once you have generated the docs make sure to push them to the `master` branch of the doc site.


## Generating documentation for local use

To generate documentation for local use (or if you need to customise any arguments for the scripts) you need to run each command with your appropriate arguments:


### Forms

```bash
bash forms.sh -d [docs directory]
```

The docs directory will default to `../../doaj-docs` (relative to the script) if omitted


### Data Models

You must run the **Forms** documentation before running the Data Models documentation

```bash
bash data_models.sh -d [docs directory]
```

The docs directory will default to `../../doaj-docs` (relative to the script) if omitted

### Feature Map

```bash
bash featuremap.sh -d [docs directory]
```

The docs directory will default to `../../doaj-docs` (relative to the script) if omitted

### Testbook

```bash
bash testbook.sh -d [docs directory] -b [base url where testbook will be hosted] -t [DOAJ test instance to point to ] -f [resource files base url]
```

The `docs directory` will default to `../../doaj-docs` (relative to the script) if omitted

The `base url where testbook will be hosted` will default to `https://doaj.github.io/doaj-docs/$BRANCH/testbook` if omitted

The `DOAJ test instance to point to` will default to `http://testdoaj.cottagelabs.com/` if omitted

The `resource files base url` will default to `https://raw.githubusercontent.com/DOAJ/doaj/$BRANCH/doajtest` if omitted

For example, to build the testbook for your own local use, you might issue the command

```bash
bash testbook.sh -d ~/tmp/testbook \
                 -b http://localhost:8000
                 -t http://localhost:5004
                 -f file:///home/user/code/doaj/doajtest
```

(note that if the `docs directory` is not a git repo you will see git errors running this script, but they should not interfere with the actual operation)
