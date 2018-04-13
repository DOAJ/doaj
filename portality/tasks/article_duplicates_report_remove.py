"""Task to generate a report on duplicated articles in the index"""

from portality.tasks.redis_huey import long_running, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException

import esprit
import codecs
import os
from portality import models
from portality.article import XWalk
from portality.lib import dates
from portality.core import app
from portality.clcsv import UnicodeWriter


class ArticleDuplicateReportBackgroundTask(BackgroundTask):
    __action__ = "article_duplicate_report"

    def run(self):
        job = self.background_job
        params = job.params

        outdir = self.get_param(params, "outdir", "article_duplicates_" + dates.today())
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        global_reportfile = 'duplicate_articles_global_' + dates.today() + '.csv'
        owner_reportfile = 'duplicate_articles_per_owner_' + dates.today() + '.csv'
        global_reportpath = os.path.join(outdir, global_reportfile)
        owner_reportpath = os.path.join(outdir, owner_reportfile)

        # Connection to the ES index, rely on esprit sorting out the port from the host
        conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None,
                                          app.config["ELASTIC_SEARCH_DB"])

        # scroll through all articles
        scroll_query = {  # scroll from newest to oldest
            "query": {"match_all": {}},
            "sort": [{"last_updated": {"order": "desc"}}]
        }
        
        # Initialise our reports
        f = codecs.open(global_reportpath, "wb", "utf-8")
        global_report = UnicodeWriter(f)
        g = codecs.open(owner_reportpath, 'wb', 'utf-8')
        owner_report = UnicodeWriter(g)
        
        header = ["article_id", "article_created", "article_doi", "article_fulltext", "article_owner", "article_issns", "n_matches", "match_type", "match_id", "match_created", "match_doi", "match_fulltext", "match_owner", "match_issns"]
        print ' '.join(header)
        global_report.writerow(header)
        owner_report.writerow(header)

        # Record the sets of duplicated articles
        global_matches = []
        owner_matches = {}

        for a in esprit.tasks.scroll(conn, 'article', q=scroll_query):
            article = models.Article(_source=a)
            print article.id
            journal = article.get_journal()
            owner = None
            if journal:
                owner = journal.owner                                                # TODO: cache ISSN -> owner lookups

            # Get the global duplicates
            global_duplicates = XWalk.discover_duplicates(article, owner=None)
            if global_duplicates:
                s = set([article.id] + [d.id for d in global_duplicates.get('doi', []) + global_duplicates.get('fulltext', [])])
                if s not in global_matches:
                    self._write_rows_from_duplicates(article, owner, global_duplicates, global_report)
                    global_matches.append(s)

            # Get the duplicates within the owner's records
            if owner is not None:
                owner_duplicates = XWalk.discover_duplicates(article, owner)
                if owner_duplicates:
                    if owner not in owner_matches:
                        owner_matches[owner] = []
                    s = set([article.id] + [d.id for d in global_duplicates.get('doi', []) + global_duplicates.get('fulltext', [])])
                    if s not in owner_matches[owner]:
                        self._write_rows_from_duplicates(article, owner, owner_duplicates, owner_report)
                        owner_matches[owner].append(s)

        f.close()
        g.close()

    def _summarise_article(self, article, owner):
        a_doi = article.bibjson().get_identifiers('doi')
        a_fulltext = article.bibjson().get_urls('fulltext')

        return {
            'created': article.created_date,
            'doi': a_doi[0] if len(a_doi) > 0 else '',
            'fulltext': a_fulltext[0] if len(a_fulltext) > 0 else '',
            'owner': owner,
            'issns': ','.join(article.bibjson().issns())
        }

    def _write_rows_from_duplicates(self, article, owner, duplicates, report):
        dups = {}
        for d in duplicates.get('doi', []):
            dups[d.id] = self._summarise_article(d, owner=owner)
            dups[d.id]['match_type'] = 'doi'

        for d in duplicates.get('fulltext', []):
            if d.id in dups:
                dups[d.id]['match_type'] = 'doi+fulltext'
            else:
                dups[d.id] = self._summarise_article(d, owner=owner)
                dups[d.id]['match_type'] = 'fulltext'

        # write rows to report
        a_summary = self._summarise_article(article, owner)
        for k, v in dups.iteritems():
            row = [article.id,
                   a_summary['created'],
                   a_summary['doi'],
                   a_summary['fulltext'],
                   owner,
                   a_summary['issns'],
                   len(dups),
                   v['match_type'],
                   k,
                   v['created'],
                   v['doi'],
                   v['fulltext'],
                   v['owner'],
                   v['issns']]
            report.writerow(row)
            print row


    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        params = {}
        cls.set_param(params, "outdir", kwargs.get("outdir", "article_duplicates_" + dates.today()))

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        job.params = params
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        article_duplicate_report.schedule(args=(background_job.id,), delay=10)

"""
@long_running.periodic_task(schedule("article_duplicate_report"))
@write_required(script=True)
def scheduled_article_cleanup_sync():
    user = app.config.get("SYSTEM_USERNAME")
    job = ArticleDuplicateReportBackgroundTask.prepare(user)
    ArticleDuplicateReportBackgroundTask.submit(job)
"""


@long_running.task()
@write_required(script=True)
def article_duplicate_report(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ArticleDuplicateReportBackgroundTask(job)
    BackgroundApi.execute(task)
