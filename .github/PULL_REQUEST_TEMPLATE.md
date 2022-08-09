# Title <- provide a title for the PR

For: # <- enter link to issue on main board

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

## Basic PR Checklist

- [ ] FeatureMap annotations have been added
- [ ] Unit tests have been added/modified
- [ ] Functional tests have been added/modified
- [ ] Code has been run manually in development, and functional tests followed locally
- [ ] No deprecated methods are used
- [ ] No magic strings/numbers - all strings are in `constants` or `messages` files
- [ ] Where possible our common library functions have been used (e.g. dates manipulated via `dates`)
- [ ] If needed, migration has been created and tested locally
- [ ] Have you done a recent merge up from `develop`
- [ ] Release sheet has been created, and completed as far as is possible https://docs.google.com/spreadsheets/d/1Bqx23J1MwXzjrmAygbqlU3YHxN1Wf7zkkRv14eTVLZQ/edit
- [ ] Documentation updates - if needed - have been identified and prepared for inclusion into main documentation (e.g. added and highlighted/commented as appropriate to this PR)
    - [ ] Core model documentation: https://docs.google.com/spreadsheets/d/1lun2S9vwGbyfy3WjIjgXBm05D-3wWDZ4bp8xiIYfImM/edit
    - [ ] Events and consumers documentation: https://docs.google.com/spreadsheets/d/1oIeG5vg-blm2MZCE-7YhwulUlSz6TOUeY8jAftdP9JE/edit

## Testing

List the Functional Tests that must be run to confirm this feature

1. ...
2. ...



## Deployment

What deployment considerations are there? (delete any sections you don't need)

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


