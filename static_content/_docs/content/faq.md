## Contribute

### How can I contribute to DOAJ?

1. [Support us]() with a financial donation
  + All donations received are spent on DOAJ activities or developments.
2. If you have evidence that a journal in DOAJ might be questionable, [contact us]().
  + All information shared with DOAJ is done so in confidence and is never published.
3. If you find a broken link or something that is out of date or incomplete, [contact us]().
  + We are always grateful when our users are our eyes and ears.
4. Become a volunteer
  + From time to time, we put out a call for volunteers. Follow us on [Twitter](https://twitter.com/doajplus) or [our blog](https://blog.doaj.org/) to find out when the next call is published.

### I have found a broken link. What should I do?

  [Contact us]() with the details. For broken links in articles, include the journal's ISSN, title and the title of the article.

### I think that a questionable journal is indexed in DOAJ. What should I do?

  Please [contact us]() with the details, including the ISSN, and we will investigate. Information shared with DOAJ is done so in confidence.

### I know a journal which should be in DOAJ but isn’t. What should I do?

  Contact the journal and ask them to submit an application. You can also send us the details of the journal—title and ISSN—and we will contact them.

### The journal I am looking for isn't in DOAJ. Why? What should I do?

  Maybe the journal hasn't applied to us or its application is still in progress. It may be that the journal was removed from DOAJ. [Contact us]() to see if the journal has a pending application.

### How do I report a bug or ask for technical help?

  There is a specific set of information that you need to provide to us. You may not be able to provide the details for all of these but fill in as many as you can:

  1. The contact details for the person reporting the bug (or a proxy for them) so that we can request more detail if needed.
    + That might be you or someone working on your behalf.
  2. The user account you are logged in to when the problem occurred.
  3. Tell us which area of the system this happened in. Generally: in the UI/API/OAI; and ideally specifically:
    + which URL were you on when it happened, or
    + which URL were you trying to access?
  4. At what date and time the incident occurred.
    + If it happened several times, then all dates/times that were recorded, or a range.
  5. What were you trying to do? As much detail and context as possible.
    + Send a screenshot. An image always helps.
  6. What happened, what error message was received?
    + Provide the exact error message, don't paraphrase.
    + Send a screenshot.
    + What did you expect to happen?
    + Was the problem repeatable?
    + Did you try several times with the same result?
  7. What environment are you in?
    + Specifically which browser or,
    + If not in the browser, any useful information about your API client such as the user agent.
  8. Send copies of any data you sent to the system.
    + For example, article XML files uploaded, or payloads sent to the API.

Send the information to [feedback@doaj.org](mailto:feedback@doaj.org). If you are familiar with GitHub, you can [create the bug ticket](https://github.com/DOAJ/doaj/issues/new/choose) yourself. Don’t send us your passwords or API keys.

---

## Metadata

### How can I get journal metadata from DOAJ?

#### API

A [search API]() is available. Some functions require an API key. To get your API key, go to your account page. If no API key is available, [contact us]().

#### Atom feed

We have [an Atom feed](/feed) of journals which is updated every time a new journal is added to DOAJ.

#### Crawling

You may crawl DOAJ as long as you follow our good behaviour guidelines for crawling:
+ follow our robot.txt file http://doaj.org/robots.txt
+ use our sitemap
+ obey our rate limit

If your crawler hits our servers too often, or your crawler starts to affect DOAJ's performance in any way, then your access will be restricted or even blocked. (It's faster and easier for you to collect our metadata if you connect via the API.)

#### CSV file

You can download the list of journals as a CSV (comma-separated) file. This can be imported into any compatible analysis program. The CSV file is updated every 30 minutes.
  + Download the file to your computer
  + Import the file into a spreadsheet processing program (like Excel or OpenOffice)
  +  Make sure you choose Unicode (UTF-8) as the file origin.

#### Data dumps

You can [download all of our journal and article metadata]() as two static files. They are refreshed weekly.

#### OAI-PMH

DOAJ supports the OAI protocol for metadata harvesting (OAI-PMH). Any OAI compatible service can obtain records from DOAJ. The base URL is `http://www.doaj.org/oai`. You can add most OAI verbs and other commands directly on to that. There is a full description of this service on the [OAI-PMH documentation page](). Our current OAI offering is standardised around Dublin Core.

### Why do some journals have no or very little article metadata in DOAJ?

We do not yet crawl publisher sites to collect article metadata. Instead, we ask publishers to upload the metadata to us. If a journal in DOAJ has no articles, it is because the metadata hasn't been sent to us.

---

## Do you have any restrictions on the reuse of your metadata?

The data in DOAJ is currently licensed to you under a [Creative Commons Attribution-ShareAlike License (CC BY-SA)](https://creativecommons.org/licenses/by-sa/4.0/). You should familiarise yourself with [the legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode) for this license.

The rights of the site-generated metadata in the Atom feed are listed in the feed.

---

## What code is DOAJ built with?

DOAJ is a Python/Flask web app with a JSON document store. The code is open source and can be found in [our GitHub repository](https://github.com/DOAJ/doaj).

DOAJ uses Bootstrap which is the framework used to build the DOAJ website. This contains some Javascript for some of its features.

---

## Finding content in DOAJ

### Browsing by subject

The subject classifications used to [Browse by subject]() page are structured as follows:

+ subjects separated by a full stop (.) are part of the same category. For example: 'Philosophy. Psychology. Religion' is one category.
+ where two subjects are separated by a colon (:), the second subject is a subcategory of the first. For example: 'Philosophy. Psychology. Religion: Philosophy (General)'. This journal has been categorised as General Philosophy.
+ where subjects are separated by a pipe (\|), the second category has no relation to the first. For example: 'Philosophy. Psychology. Religion: Philosophy (General) \| Social Sciences: Social sciences (General)' means that this journal has been categorised both as General Philosophy and General Social Sciences.

### Searching by keyword

You can choose to filter your search results by ‘keyword’.

Journal keywords are chosen by the person applying for a journal. They are reviewed and edited by the DOAJ Team. They are more arbitrary than the subject classification.
