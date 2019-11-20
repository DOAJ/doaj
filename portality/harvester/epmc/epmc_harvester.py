from portality.models.harvester import HarvesterPlugin
from portality.harvester.epmc import client, queries
from portality.lib import dates
from portality.api.v1.client import models as doaj
from portality.core import app
from datetime import datetime
import time

class EPMCHarvester(HarvesterPlugin):
    def get_name(self):
        return "epmc"

    def iterate(self, issn, since, to=None):
        # set the default value for to, if not already set
        if to is None:
            to = dates.now()

        # get the dates into a datestamp
        sd = dates.parse(since)
        td = dates.parse(to)

        # calculate the ranges we're going to want to query by
        # We're going to query epmc one day at a time, so that we can effectively
        # iterate through in updated date order (though within each day, there will
        # be no ordering, there is little we can do about that except reduce the
        # request granularity further, which would massively increase the number
        # of requests)
        ranges = dates.day_ranges(sd, td)
        throttle = app.config.get("EPMC_HARVESTER_THROTTLE")

        last = None
        for fr, until in ranges:
            # throttle each day
            if last is not None and throttle is not None:
                diff = (datetime.utcnow() - last).total_seconds()
                app.logger.debug("Last day request at {x}, {y}s ago; throttle {z}s".format(x=last, y=diff, z=throttle))
                if diff < throttle:
                    waitfor = throttle - diff
                    app.logger.debug("Throttling EPMC requests for {x}s".format(x=waitfor))
                    time.sleep(waitfor)

            # build the query for the oa articles in that issn for the specified day (note we don't use the range, as the granularity in EPMC means we'd double count
            # note that we use date_sort=True as a weak proxy for ordering by updated date (it actually orders by publication date, which may be partially the same as updated date)
            query = queries.oa_issn_updated(issn, fr, date_sort=True)
            for record in client.EuropePMC.complex_search_iterator(query, throttle=throttle):   # also throttle paging requests
                article = self.crosswalk(record)
                yield article, fr

            last = datetime.utcnow()

    def crosswalk(self, record):
        article = doaj.Article()
        article.bibjson = {"title" : "", "identifier" : []}
        bj = article.bibjson
        # FIXME: this is a hack; to use DataObj in this way, we need to create article.bibjson with valid data (as we have set data
        # requirements on the struct).  So above we create it with the requried data, and now we remove the field so that it isn't
        # populated later when we do actual data validation.
        # The longer term fix for this is a review of the DataObj code, but for the time being this is good.
        bj._delete("title")
        bj.journal = {}
        journal = bj.journal

        # sort out the issns - EPMC sometimes puts the same value in the issn and essn fields.  I guess this is
        # because they regard the issn to be the essn if there is no print issn.  This little trick below extracts
        # the values to pissn and eissn, and then if they are the same, gets rid of the pissn.
        pissn = record.issn
        eissn = record.essn
        if pissn == eissn:
            pissn = None

        if pissn is not None:
            article.add_identifier("pissn", pissn)
        if eissn is not None:
            article.add_identifier("eissn", eissn)

        bj.title = record.title
        article.add_identifier("doi", record.doi)
        journal.volume = record.journal_volume
        journal.number = record.journal_issue
        journal.title = record.journal
        journal.language = record.language
        bj.year = record.year_of_publication
        bj.month = record.month_of_publication
        journal.start_page = record.start_page
        journal.end_page = record.end_page
        article.add_link("fulltext", record.get_first_fulltext_url())
        bj.abstract = record.abstract

        for a in record.authors:
            cn = a.get("collectiveName")
            fn = a.get("firstName")
            ln = a.get("lastName")

            if fn is None and ln is None and cn is None:
                fn = record.author_string
                if fn is None:
                    continue

            n = ""
            if cn is not None:
                n += cn
            if fn is not None:
                if n != "":
                    n += " "
                n += fn
            if ln is not None:
                if n != "":
                    n += " "
                n += ln
            article.add_author(name=n)

        return article

