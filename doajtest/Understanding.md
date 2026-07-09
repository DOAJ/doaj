# DOAJ Testbook — Manual & Editing Guide

> Status: draft for maintainer review. Written 2026-07-09 by reading the `testbook`
> package source (`CottageLabs/testbook`, pinned in `setup.py`) and the YAML files
> in this directory. Please correct anything that doesn't match how the team
> actually uses it.

## 1. What Testbook is (and isn't)

**Testbook is DOAJ's catalogue of *manual* functional test scripts.** It is not
related to pytest, not run in CI, and does not touch a browser. It is a small
external tool (`CottageLabs/testbook`) that reads YAML "test script" files from
this directory and compiles them into:

- a browsable HTML site (step-by-step instructions for a human tester), and
- CSV files (one per test, one per testset, plus a zip of all of them) — these
  are the same content in a format QA can paste into a spreadsheet.

Think of it as a structured, version-controlled replacement for a QA test-case
spreadsheet — each YAML file is one "testset" of hand-executed test scripts, not
automated test code.

It is **not currently wired into CI** — nothing in `.github/` invokes it. It's
generated on demand via `docs/testbook.sh`, and the output is published into the
separate `doaj-docs` repo (GitHub Pages).

## 2. Where things live

| Path | What it is |
|---|---|
| `doajtest/testbook/**/*.yml` | The test scripts themselves — this directory, one subfolder per suite by convention |
| `docs/testbook.sh` | Script that runs the `testbook` CLI to build the HTML/CSV output and push it to `doaj-docs` |
| `portality/scripts/generate_docs_index.py` | Adds a "Functional Tests" link to the generated docs index if a `testbook/` output dir exists |
| `portality/scripts/functional_test_csv_to_testbook.py` | One-off legacy migration script (CSV → this YAML format). Not part of the normal workflow — historical only |
| `portality/view/testdrive.py` | Flask routes (`/testdrive/<id>`) that a tester visits to auto-provision test data/accounts referenced from a test script |
| `doajtest/testdrive/*.py` | The Python classes behind those routes — see §6 |
| `setup.py` (`docs` extra) | Pins the `testbook` package itself: `testbook @ git+https://github.com/CottageLabs/testbook.git@<sha>` |

The `testbook` **package** (the tool that renders the YAML) is separate from
DOAJ's own code — it's a pip dependency in the `docs` extras group, not
something in `portality/`. To get it locally: `pip install -e .[docs]`.

## 3. The YAML schema

This is the full schema the `testbook` tool understands (from `testbook/core.py`
and `testbook/cli.py` in the upstream package). Anything not listed here is
silently ignored by the renderer.

```yaml
suite: Name of the Test Suite        # required — tests with the same `suite` across
                                      # *different files* are grouped together
testset: Name for this set of tests  # required — same grouping behaviour as `suite`

fragments:                           # optional — reusable step blocks.
  fragment_id:                       #   ⚠ only usable within THIS file (see §9)
    - step: A reusable step
      results:
        - An expected result

tests:                               # required — the list of test scripts
  - title: Title of this specific test        # required, should be unique within the testset
    context:                                  # optional — free-form key/value, no semantics
      role: Admin                             #   to the tool itself. DOAJ convention: `role`
      testdrive: some_testdrive_id             #   (who executes it) and `testdrive` (see §6)
    depends:                                  # optional — tests that must be run first
      - suite: Other Suite Name
        testset: Other Testset Name
        test: Other Test Title
    setup:                                    # optional — free-text prep instructions
      - Do this before starting the test
    steps:                                    # required — the actual instructions
      - step: What the tester should do       # required per step
        path: /relative/path/to/page          # optional — link into the running app
        resource: /relative/path/to/file.csv  # optional — link to a test fixture file
        results:                              # optional — list of things to verify
          - An expected outcome
      - include:                              # step can ALSO just be an include directive —
          fragment: fragment_id               #   if present, nothing else in that step matters
```

Key rules (from reading the renderer, `render_testset()` / `test_rows()` in
`core.py`):

- **`suite` + `testset` aggregate across files.** Multiple `.yml` files can
  contribute tests to the same suite/testset — they get merged when rendered.
  DOAJ's convention is one file per testset, in a folder per suite (e.g.
  `report_export/report_export_application.yml`), but this is a convention, not
  a rule the tool enforces.
- **Names get slugified for URLs.** `suite`, `testset` and test `title` are all
  passed through `safe_id()` — lowercased, spaces → underscores, non-word chars
  stripped — to build the HTML filenames and anchors. Two titles that differ
  only in punctuation/case will collide.
- **Test titles should be unique within a testset.** The renderer doesn't error
  on duplicates, but the generated links/IDs will collide silently.
- **`fragments` are file-scoped.** You can't `include` a fragment defined in
  another `.yml` file — only ones defined in the same file.
- **`include` is exclusive.** If a step has `include`, every other key in that
  step (`step`, `path`, `resource`, `results`) is ignored.
- **There is no `teardown` key.** DOAJ's convention is to mention teardown as
  free text inside `setup`, e.g. *"At the end of the test please use the
  'teardown' link provided by the testdrive to remove test assets"* — see the
  worked example in §6.
- **Malformed YAML fails the whole build**, not just one file — `read_structure()`
  wraps the parse in a bare `try/except` that just prints `Error loading from
  <path>` and re-raises. There's no per-file isolation or schema validation, so
  a typo in one file breaks the entire generation run. (Live footgun example:
  writing a step whose text itself contains an unquoted `key:` — e.g. `step: It
  declares id: foo in the text` — is parsed as a nested YAML mapping and blows
  up the whole build with a `ScannerError`. Quote the string if it contains a
  colon.)

### A note on the `id` field — not usable in DOAJ's pinned version

The upstream repo has a newer `live_testing` branch (README:
`https://github.com/CottageLabs/testbook/tree/live_testing#testbook-format`)
whose documented schema adds one new field over what's above:

```yaml
tests:
  - id: optional-stable-test-id   # NEW in `live_testing`, not in DOAJ's pin
    title: Title of this specific test
    ...
```

If `id` is omitted, that branch derives one from the title (slugified, e.g.
`"Valid credentials"` → `"valid-credentials"`), kept stable across "syncs" even
if the test is later reordered or the file is regenerated.

**We verified hands-on (not just from the docs) that this field is currently
inert for DOAJ**, in two ways:

1. **It isn't even implemented in the same place as the renderer.** In the
   `live_testing` checkout, `id` is only read by `testbook/database.py` and
   `testbook/web.py` — a separate Flask "live testing" web app with an
   execution-tracking database (`testbook-web` / `flask --app testbook.web:create_app
   run`) that DOAJ doesn't use at all. `testbook/core.py` — the module that
   actually powers the `testbook <src> <out>` CLI DOAJ runs via
   `docs/testbook.sh` — never references `test["id"]` in either branch; it
   always derives the id/slug from `title` via `safe_id()`.
2. **Confirmed by actually rendering it.** Using DOAJ's currently pinned
   `testbook` install, we rendered this file:

   ```yaml
   suite: Id Field Demo
   testset: Id Field Demo
   tests:
     - id: explicit-stable-id
       title: Test with an explicit id
       context:
         role: Admin
       steps:
         - step: "This test declares an explicit id field in the YAML"
           results:
             - Under DOAJ's pinned testbook version, this id is parsed but never referenced anywhere in rendering
   ```

   ```bash
   testbook /path/to/src /path/to/out -t http://localhost:8123 -a http://localhost:5000 -r http://example.com
   grep -rn "explicit-stable-id" /path/to/out/
   # => no matches anywhere in the generated HTML/CSV
   ```

   The string `explicit-stable-id` never appears anywhere in the rendered
   output — the field is parsed (no error) but has zero effect. The generated
   filename was `id_field_demo__id_field_demo.html`, built the normal way from
   `suite`/`testset`, exactly as if `id` had never been present.

**Practical takeaway:** don't add `id:` to any DOAJ testbook YAML today — it
would do nothing under the current pin, and would only become meaningful if
DOAJ ever upgrades to (a working release of) the `live_testing` branch *and*
adopts its web app/database sync feature. Also worth flagging to the
maintainer: as of this check, `live_testing`'s own `pyproject.toml` fails to
`pip install` from git at all (`setuptools` error: "Multiple top-level
packages discovered in a flat-layout: ['design', 'testbook']") — so upgrading
isn't a drop-in pin bump even if desired.

## 4. Generating the output locally

```bash
# one-time: install the testbook tool itself
source <your doaj venv>/bin/activate
pip install -e ".[docs]"   # note: quote this — zsh treats an unquoted [docs]
                            # as a glob pattern and errors with "no matches found"
```

In practice, `pip install -e ".[docs]"` pulls in **all** of DOAJ's base
`install_requires`, not just the `docs` extra — and on a machine without
`python3-dev`/`python3.10-dev` headers installed, that fails building the
`setproctitle` C extension (`fatal error: Python.h: No such file or
directory`), even though `setproctitle` has nothing to do with testbook. If
you hit that and just want the testbook tool itself (e.g. to try edits
without setting up the full app), install it standalone instead — its own
deps (`click`, `jinja2`, `pyyaml`) are pure Python and always work:

```bash
pip install "testbook @ git+https://github.com/CottageLabs/testbook.git@edede0987fe2f9fe806bbc74b635f415ab645166#egg=testbook"
```

```bash
# from the repo root
bash docs/testbook.sh
```

Or invoke the CLI directly against just this directory, without the docs-repo
plumbing `docs/testbook.sh` does:

```bash
testbook doajtest/testbook /tmp/testbook_out \
  -t http://localhost:8000 \
  -a http://localhost:5000 \
  -r https://raw.githubusercontent.com/DOAJ/doaj/develop/doajtest

cd /tmp/testbook_out && python3 -m http.server
# open http://localhost:8000
```

(`-t`/`-a`/`-r` are base URLs for the testbook site itself, the running DOAJ app
under test, and where `resource:` files are hosted — see `docs/testbook.sh` for
how DOAJ sets these for a real deploy.)

`docs/testbook.sh` additionally checks out the sibling `doaj-docs` repo,
generates into `doaj-docs/<branch>/testbook`, and expects you to commit/push
that separately — it is **not** committed inside `doaj`.

## 5. Editing an existing test

Say you want to tweak a step in `report_export/report_export_application.yml`
because the UI copy changed from "Export Data as CSV" to "Export as CSV":

```diff
   - title: Facet Export
     context:
       role: Admin
     steps:
       - step: Go to the application search page in the admin area
         path: /admin/applications
         results:
           - At the bottom of the list of facets is a "Reporting Tools" section
-      - step: Click on "Export Data as CSV"
+      - step: Click on "Export as CSV"
         results:
           - An export section expands which includes a section to "download the current facets"
```

That's it — just edit the YAML in place. Nothing needs regenerating for the
change to "take" in git; regeneration (§4) is only needed to produce the
browsable HTML/CSV, which isn't committed to this repo.

**Checklist when editing:**
- Keep `title` stable if other tests `depends` on it (search for the exact
  title string first — `depends` matches on the literal `suite`/`testset`/`test`
  text, not an ID).
- If you rename a `title`, grep the whole `doajtest/testbook/` tree for that
  string in a `depends:` block first.

## 6. Adding a new test to an existing testset

Add a new entry to the `tests:` list in the relevant file, e.g. appending to
`report_export/report_export_application.yml`:

```yaml
  - title: Export with no filters applied
    context:
      role: Admin
    steps:
      - step: Go to the application search page in the admin area
        path: /admin/applications
      - step: Without applying any filters, click on "Export Data as CSV"
        results:
          - The export includes every application in the system
```

## 7. Adding a brand-new suite/testset (new file)

Create a new folder + `.yml` file, following the existing convention of
`<suite_slug>/<testset_slug>.yml`:

```
doajtest/testbook/subject_indexing/reindex_by_subject.yml
```

```yaml
suite: Subject Indexing
testset: Reindex by Subject

tests:
  - title: Reindex a single subject
    context:
      role: Admin
    setup:
      - Ensure there are at least 2 journals classified under the same LCC subject code
    steps:
      - step: Go to the admin subject management page
        path: /admin/subjects
        results:
          - A list of subject codes with journal counts is displayed
      - step: Select a subject and click "Reindex"
        results:
          - A background job is queued
          - A flash message confirms the reindex has started
      - step: Go to the background jobs page and wait for the job to complete
        path: /admin/background_jobs
        results:
          - The job status becomes "complete"
```

Nothing else needs registering — the renderer walks the whole `doajtest/testbook/`
tree (`os.walk`) and treats every file it finds as a testbook file, so a new
file is picked up automatically on the next `docs/testbook.sh` run.

## 8. Adding a reusable fragment

Fragments only apply **within one file** (§3). Worked example, adding a
"log out and back in" fragment reused by two tests in the same file:

```yaml
suite: Subject Indexing
testset: Reindex by Subject

fragments:
  relogin:
    - step: Click "logout" on the top right of the page
      results:
        - You are returned to the home page and no longer logged in
    - step: Log back in with the same account
      results:
        - You see a "Welcome back" message

tests:
  - title: Reindex a single subject
    context:
      role: Admin
    steps:
      - step: Go to the admin subject management page
        path: /admin/subjects
      - include:
          fragment: relogin
      - step: Select a subject and click "Reindex"
        results:
          - A background job is queued

  - title: Reindex all subjects
    context:
      role: Admin
    steps:
      - step: Go to the admin subject management page
        path: /admin/subjects
      - include:
          fragment: relogin
      - step: Click "Reindex All"
        results:
          - A background job is queued for every subject
```

## 9. Adding a dependency between tests

`depends` just tells the human tester "run this other test first" — it isn't
enforced by tooling, only rendered as a note. Match the target's exact `suite`
/ `testset` / `test` (title) strings:

```yaml
  - title: Manage existing reports
    context:
      role: Admin
    depends:
      - suite: Report Export
        testset: Report Export Application
        test: Export Search as CSV
    steps:
      - step: Ensure you have exported at least one CSV as per the "Export Search as CSV" test
      ...
```

## 10. Tests backed by a `testdrive` (auto-provisioned test data)

Many tests need pre-existing data (a publisher account, some journals) before a
human can execute the steps. Rather than writing manual setup instructions,
DOAJ's convention is to point at a **testdrive** — a small Python class that
provisions (and later tears down) fixtures, exposed at `/testdrive/<id>`.

The link between the YAML and the Python class is by **naming convention only**,
resolved in `doajtest/testdrive/factory.py::TestFactory.get()`:

```python
modname = test_id                                          # e.g. "publisher_csv_upload"
classname = test_id.replace("_", " ").title().replace(" ", "")  # e.g. "PublisherCsvUpload"
classpath = "doajtest.testdrive." + modname + "." + classname
```

So `context.testdrive: publisher_csv_upload` in a YAML file resolves to
`doajtest/testdrive/publisher_csv_upload.py`, class `PublisherCsvUpload`, which
must subclass `TestDrive` (`doajtest/testdrive/factory.py`) and implement
`setup()` / `teardown()`.

**Worked example — real usage in `publisher_csv/validate_csv.yml`:**

```yaml
tests:
- title: Invalid headers in upload
  context:
    role: Publisher
    testdrive: publisher_csv_upload
  setup:
    - Use the publisher_csv_upload testdrive to setup for this test at /testdrive/publisher_csv_upload
    - At the end of the test please use the 'teardown' link provided by the testdrive to remove test assets from the system
  steps:
  - step: Log in as the publisher account specified by the testdrive result
  ...
```

If you're adding a *new* test that needs a testdrive, and no suitable one
exists yet, add a class alongside the existing ones:

```python
# doajtest/testdrive/reindex_subject_setup.py
from doajtest.testdrive.factory import TestDrive

class ReindexSubjectSetup(TestDrive):
    def setup(self) -> dict:
        journals = self.journals_in_doaj(owner=..., n=2)   # helpers from TestDrive base
        report = {}
        self.report_journal_ids(journals, report)
        return report

    def teardown(self, setup_params) -> dict:
        self.teardown_journals(setup_params)
        return self.SUCCESS
```

then reference it as `context.testdrive: reindex_subject_setup` in the YAML —
the class name `ReindexSubjectSetup` is derived automatically from that string,
so the filename and class name must follow the exact `snake_case` →
`PascalCase` mapping above or `TestFactory.get()` will fail to import it.

## 11. Gotchas / footguns to flag in review

1. **No schema validation.** A typo (e.g. `step:` misspelled) doesn't error
   loudly at the point of the mistake — it either gets silently dropped by the
   renderer or blows up the entire build with a bare traceback pointing at
   `read_structure()`, not your file. Worth eyeballing a diff carefully before
   committing.
2. **No CI hook.** Broken YAML here won't fail a PR build — it'll only surface
   next time someone manually runs `docs/testbook.sh`.
3. **`depends` and fragment `include` are string-matched, not ID-matched.**
   Renaming a `title` silently breaks anything that referenced it.
4. **Fragments don't cross files.** If you want to share a fragment across
   testsets in different files, you currently have to duplicate it (upstream
   `testbook` has no support for shared/global fragments).
5. **Output isn't committed to this repo.** The generated HTML/CSV lives in the
   separate `doaj-docs` repo, pushed manually via `docs/testbook.sh` — there's
   no way to preview a testbook change through DOAJ's own CI/PR process.

## 12. Quick reference — what to check in review

- [ ] New/edited `.yml` files parse (`python3 -c "import yaml; yaml.safe_load(open('path'))"` per file, or just run `docs/testbook.sh`/the raw `testbook` CLI locally)
- [ ] `title` is unique within its `testset`
- [ ] Any `depends:` or `include: {fragment: ...}` references match an existing, exactly-spelled target
- [ ] If `context.testdrive` is set, a matching `doajtest/testdrive/<id>.py` class exists with the exact `PascalCase` name derived from the id
- [ ] File placed under `doajtest/testbook/<suite_slug>/<testset_slug>.yml` following existing convention
