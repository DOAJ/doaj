---
layout: sidenav
title: Journal CSV
section: Docs
toc: true
sticky_sidenav: true
preface: /public/includes/_csv-access.html
featuremap: 
  - ~~JournalCSV:Fragment->JournalCSV:WebRoute~~

---

The Journal CSV provides a full list of all public journals in the DOAJ database.

## Premium users

For Premium users, the CSV file is up-to-date to within 1 hour of the current data in the system.  To access the Premium CSV you need to be logged into your DOAJ account to download, and have an active Premium subscription.  If you are accessing the CSV using a machine-to-machine process, you can ensure you are 
receiving the up-to-date CSV by including your api key in the URL.  For example:

```https://doaj.org/csv?api_key=[your api key]```

If you do not have an API key, go to your account settings page where you can access your key, or generate a new one.

## Free users

For Free users, the CSV is up-to-date to within 30 days of the current data in the system.  This version of the CSV is available to all users, and does not require a login.  The CSV file is available for download at the following URL:

```https://doaj.org/csv```

If you wish to get more up-to-date data, you can subscribe to the Premium service.  For more information on the Premium service, please see the [Premium page](/docs/premium).