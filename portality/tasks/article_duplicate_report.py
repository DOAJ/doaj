"""Task to generate a report on duplicated articles in the index"""

from portality.tasks.redis_huey import long_running
from portality.app_email import email_archive

from portality.background import BackgroundTask, BackgroundApi

import esprit
import codecs
import os
import shutil
import json
from portality import models
from portality.article import XWalk
from portality.lib import dates
from portality.core import app
from portality.clcsv import UnicodeWriter, UnicodeReader
import csv


class ArticleDuplicateReportBackgroundTask(BackgroundTask):
    __action__ = "article_duplicate_report"

    # Keep a cache of ISSNs to owners
    owner_cache = {}

    def run(self):
        job = self.background_job
        params = job.params

        # Set up the files we need to run this task - a dir to place the report, and a place to write the article csv
        outdir = self.get_param(params, "outdir", "article_duplicates_" + dates.today())
        job.add_audit_message("Saving reports to " + outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        global_reportfile = 'duplicate_articles_global_' + dates.today() + '.csv'
        global_reportpath = os.path.join(outdir, global_reportfile)

        # Location for our interim CSV file of articles
        tmpdir = self.get_param(params, "tmpdir", 'tmp_article_duplicate_report')
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)

        # Connection to the ES index, rely on esprit sorting out the port from the host
        conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None,
                                          app.config["ELASTIC_SEARCH_DB"])

        tmp_csvfile = 'tmp_articles_' + dates.today() + '.csv'
        tmp_csvpath = os.path.join(tmpdir, tmp_csvfile)

        with codecs.open(tmp_csvpath, 'wb', 'utf-8') as t:
            self._create_article_csv(conn, t)

        # Initialise our reports
        f = codecs.open(global_reportpath, "wb", "utf-8")
        global_report = UnicodeWriter(f)
        
        header = ["article_id", "article_created", "article_doi", "article_fulltext", "article_owner", "article_issns", "article_in_doaj", "n_matches", "match_type", "match_id", "match_created", "match_doi", "match_fulltext", "match_owner", "match_issns", "match_in_doaj", "owners_match", "titles_match", "article_title", "match_title"]
        global_report.writerow(header)

        # Record the sets of duplicated articles
        global_matches = []

        a_count = gd_count = 0

        # Read back in the article csv file we created earlier
        with codecs.open(tmp_csvpath, 'rb', 'utf-8') as t:
            article_reader = UnicodeReader(t)

            for a in article_reader:
                a_count += 1
                article = models.Article(_source={'id': a[0], 'created_date': a[1], 'bibjson': {'identifier': json.loads(a[2]), 'link': json.loads(a[3]), 'title': a[4]}, 'admin': {'in_doaj': json.loads(a[5])}})
                app.logger.debug('{0} {1}'.format(a_count, article.id))

                # Get the global duplicates
                global_duplicates = XWalk.discover_duplicates(article, owner=None, results_per_match_type=10000)
                if global_duplicates:
                    # Look up an article's owner
                    journal = article.get_journal()
                    owner = None
                    if journal:
                        owner = journal.owner
                        for issn in journal.bibjson().issns():
                            if issn not in self.owner_cache:
                                self.owner_cache[issn] = owner

                    # Deduplicate the DOI and fulltext duplicate lists
                    s = set([article.id] + [d.id for d in global_duplicates.get('doi', []) + global_duplicates.get('fulltext', [])])
                    gd_count += len(s) - 1
                    if s not in global_matches:
                        self._write_rows_from_duplicates(article, owner, global_duplicates, global_report)
                        global_matches.append(s)

        job.add_audit_message('{0} articles processed for duplicates. {1} global duplicates found.'.format(a_count, gd_count))
        f.close()

        # Delete the transient temporary files.
        shutil.rmtree(tmpdir)

        # Email the reports if that parameter has been set.
        send_email = self.get_param(params, "email", False)
        if send_email:
            archive_name = "article_duplicates_" + dates.today()
            email_archive(outdir, archive_name)
            job.add_audit_message("email alert sent")
        else:
            job.add_audit_message("no email alert sent")

    @staticmethod
    def _create_article_csv(connection, file_object):
        """ Create a CSV file with the minimum information we require to find and report duplicates. """

        csv_writer = UnicodeWriter(file_object, quoting=csv.QUOTE_ALL)

        # Scroll through all articles, newest to oldest
        scroll_query = {
            "_source": [
                "id",
                "created_date",
                "bibjson.identifier",
                "bibjson.link",
                "bibjson.title",
                "admin.in_doaj"
            ],
            "query": {
                "match_all": {}
            },
            "sort": [
                {"last_updated": {"order": "desc"}}
            ]
        }

        for a in esprit.tasks.scroll(connection, 'article', q=scroll_query, page_size=1000, keepalive='1m'):
            row = [
                a['id'],
                a['created_date'],
                json.dumps(a['bibjson']['identifier']),
                json.dumps(a['bibjson'].get('link', [])),
                a['bibjson'].get('title', ''),
                json.dumps(a.get('admin', {}).get('in_doaj', ''))
            ]
            csv_writer.writerow(row)

    def _summarise_article(self, article, owner=None):
        a_doi = article.bibjson().get_identifiers('doi')
        a_fulltext = article.bibjson().get_urls('fulltext')

        o = owner
        if o is None:
            for i in article.bibjson().issns():
                o = self.owner_cache.get(i, None)
                if o is not None:
                    break

        return {
            'created': article.created_date,
            'doi': a_doi[0] if len(a_doi) > 0 else '',
            'fulltext': a_fulltext[0] if len(a_fulltext) > 0 else '',
            'owner': o if o is not None else '',
            'issns': ','.join(article.bibjson().issns()),
            'title': article.bibjson().title,
            'in_doaj': article.is_in_doaj()
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
                   a_summary['owner'],
                   a_summary['issns'],
                   a_summary['in_doaj'],
                   str(len(dups)),
                   v['match_type'],
                   k,
                   v['created'],
                   v['doi'],
                   v['fulltext'],
                   v['owner'],
                   v['issns'],
                   v['in_doaj'],
                   str(a_summary['owner'] == v['owner']),
                   str(a_summary['title'] == v['title']),
                   a_summary['title'] if a_summary['title'] != v['title'] else '',
                   v['title'] if a_summary['title'] != v['title'] else '']
            report.writerow(row)

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

        # First prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__

        params = {}
        cls.set_param(params, "outdir", kwargs.get("outdir", "article_duplicates_" + dates.today()))
        cls.set_param(params, "email", kwargs.get("email", False))
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

'''
@long_running.periodic_task(schedule("article_duplicate_report"))
def scheduled_article_cleanup_sync():
    user = app.config.get("SYSTEM_USERNAME")
    job = ArticleDuplicateReportBackgroundTask.prepare(user)
    ArticleDuplicateReportBackgroundTask.submit(job)
'''

@long_running.task()
def article_duplicate_report(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ArticleDuplicateReportBackgroundTask(job)
    BackgroundApi.execute(task)
