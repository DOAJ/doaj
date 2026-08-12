## Changelog

**Note, issue refs on the doajPM (project management) board aren't public.**

### 8.6.11

Adds a 'Last Full Review' checkbox to the admin update request form.
https://github.com/DOAJ/doajPM/issues/4287

Required fields assignee and deadline for flagged journals, notifications on flags.
https://github.com/DOAJ/doajPM/issues/4202
https://github.com/DOAJ/doajPM/issues/4203

Fix for API article validation errors failing to reach the user due to translation

### 8.6.10

Static pages release and upgrade some dependencies, move advisory board page path.

### 8.6.9

Bugfixes to login form and change ES error code 400 to 500

https://github.com/DOAJ/doajPM/issues/4120
https://github.com/DOAJ/doajPM/issues/4394
https://github.com/DOAJ/doajPM/issues/4395
https://github.com/DOAJ/doajPM/issues/4396

### 8.6.8

Nginx routing update

### 8.6.7

Bugfixes for passwordless login

### 8.6.6

Passwordless login method

https://github.com/DOAJ/doajPM/issues/3942

### 8.6.5

Rearrange editorial form

https://github.com/DOAJ/doajPM/issues/4102

### 8.6.4

Show complete date in Admin background jobs search interface

### 8.6.3

Fix for JournalCSV - initialise internationalisation in background job processor.

### 8.6.2

Fix for the logout button found on admin forms not working.

https://github.com/DOAJ/doajPM/issues/4350

### 8.6.1

Update to static pages & translation fixes

### 8.6.0

French translation of application form, introducing numerous internationalisation features.

https://github.com/DOAJ/doajPM/issues/3916

### 8.5.6 - 2026-03-31

Fix for quick search (via menu bar) selector scope

https://github.com/DOAJ/doajPM/issues/4330

### 8.5.5 - 2026-03-26

Allow uploads when articles match one in_doaj journal even if there are duplicates not in_doaj.

https://github.com/DOAJ/doajPM/issues/1891

### 8.5.4 - VERSION SKIPPED

I bumped from .3 to .5 by mistake >_<

### 8.5.3 - 2026-03-19

Premium metadata services: 
Phase-in of 2-tier data currency as served in Public Data Dump, OAI-PMH, and Journal CSV features

https://github.com/DOAJ/doajPM/issues/4008

### 8.5.2 - 2026-01-15

Add created and last updated dates to individual account pages.

https://github.com/DOAJ/doajPM/issues/4072

### 8.5.1 - 2026-01-15

Add additional date fields to Journals and Applications:

Scope | Field | Data Model
-- | -- | --
Journal | Last Fully Reviewed | admin.last_full_review
Journal | Date Applied | admin.date_applied
Journal | Last Withdrawn Date | admin.last_withdrawn
Journal | Last Reinstated Date | admin.last_reinstated
Journal | Last Owner Transfer | admin.last_owner_transfer
Application | Date Rejected | admin.date_rejected

https://github.com/DOAJ/doajPM/issues/4080
