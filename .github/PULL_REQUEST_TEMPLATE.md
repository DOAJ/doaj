# Title <- provide a title for the PR

*Please don't delete any sections when completing this PR template; instead enter **N/A** for checkboxes or sections which are not applicable, unless otherwise stated below*

See # <- enter link to issue on main board

Describe the scope/purpose of the PR here in as much detail as you like

## Categorisation

This PR...
- [ ] has scripts to run
- [ ] has migrations to run
- [ ] adds new infrastructure
- [ ] changes the CI pipeline
- [ ] affects the public site
- [ ] affects the editorial area
- [ ] affects the publisher area
- [ ] affects the monitoring

## Basic PR Checklist

Instructions for developers:
* For each checklist item, if it is N/A to your PR check the N/A box
* For each item that you have done and confirmed for yourself, check Developer box (including if you have checked the N/A box)

Instructions for reviewers:
* For each checklist item that has been confirmed by the Developer, check the Reviewer box if you agree
* For multiple reviewers, feel free to add your own checkbox with your github username next to it if that helps with review tracking

### Code Style

- No deprecated methods are used
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

- No magic strings/numbers - all strings are in `constants` or `messages` files
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- ES queries are wrapped in a Query object rather than inlined in the code
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Where possible our common library functions have been used (e.g. dates manipulated via `dates`)
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Cleaned up commented out code, etc
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

- Urls are constructed with `url_for` not hard-coded
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
### Testing

- Unit tests have been added/modified
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Functional tests have been added/modified
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Code has been run manually in development, and functional tests followed locally
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

### Documentation

- FeatureMap annotations have been added
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Documentation updates - if needed - have been identified and prepared for inclusion into main documentation (e.g. added and highlighted/commented as appropriate to this PR)
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- Core model documentation has been added to if needed: https://docs.google.com/spreadsheets/d/1lun2S9vwGbyfy3WjIjgXBm05D-3wWDZ4bp8xiIYfImM/edit
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

- Events and consumers documentation has been added if needed: https://docs.google.com/spreadsheets/d/1oIeG5vg-blm2MZCE-7YhwulUlSz6TOUeY8jAftdP9JE/edit
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer
  
- The docs for this branch have been generated and pushed to the doc site (see docs/README.md for details)
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer


### Release Readiness

- If needed, migration has been created and tested locally
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

- Release sheet has been created, and completed as far as is possible https://docs.google.com/spreadsheets/d/1Bqx23J1MwXzjrmAygbqlU3YHxN1Wf7zkkRv14eTVLZQ/edit
  - [ ] N/A
  - [ ] Developer
  - [ ] Reviewer

- There has been a recent merge up from `develop` (or other base branch).  List the dates of the merges up from develop below
  - [date of merge up]


## Testing

List the Functional Tests that must be run to confirm this feature

1. ...
2. ...



## Deployment

What deployment considerations are there? (delete any sections you don't need)

### Configuration changes

What configuration changes are included in this PR, and do we need to set specific values for production

### Scripts

What scripts need to be run from the PR (e.g. if this is a report generating feature), and when (once, regularly, etc).

### Migrations

What migrations need to be run to deploy this

### Monitoring

What additional monitoring is required of the application as a result of this feature

### New Infrastructure

What new infrastructure does this PR require (e.g. new services that need to run on the back-end).

### Continuous Integration

What CI changes are required for this


