"""
For each article in the DOAJ index:
    * Checks that it has a corresponding journal, deletes it otherwise
    * Ensures that the article in_doaj status is the same as the journal's
    * Applies the journal's information to the article metadata as needed
"""

from portality.tasks.redis_huey import long_running, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException

import esprit
import json
from portality import models
from portality.core import app
from datetime import datetime

class ArticleCleanupSyncBackgroundTask(BackgroundTask):

    __action__ = "article_cleanup_sync"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params
        prep_all = self.get_param(params, "prepall", False)
        write_changes = self.get_param(params, "write", True)

        batch_size = 100
        journal_cache = {}
        failed_articles = []

        write_batch = []
        delete_batch = set()

        updated_count = 0
        same_count = 0
        deleted_count = 0

        # Connection to the ES index, rely on esprit sorting out the port from the host
        conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

        # Scroll though all articles in the index
        i = 0
        for a in esprit.tasks.scroll(conn, 'article', q={"query" : {"match_all" : {}}, "sort" : ["_doc"]}, page_size=100, keepalive='5m'):
            try:
                article_model = models.Article(_source=a)

                # for debugging, just print out the progress
                i += 1
                print i, article_model.id, len(journal_cache.keys()), len(write_batch), len(delete_batch)

                # Try to find journal in our cache
                bibjson = article_model.bibjson()
                allissns = bibjson.issns()

                cache_miss = False
                possibles = {}
                for issn in allissns:
                    if issn in journal_cache:
                        inst = models.Journal(**journal_cache[issn])
                        possibles[inst.id] = inst
                    else:
                        cache_miss = True
                assoc_journal = None
                if len(possibles.keys()) > 0:
                    assoc_journal = self._get_best_journal(possibles.values())

                # Cache miss; ask the article model to try to find its journal
                if assoc_journal is None or cache_miss:
                    journals = models.Journal.find_by_issn(allissns)
                    if len(journals) > 0:
                        assoc_journal = self._get_best_journal(journals)

                # By the time we get to here, we still might not have a Journal, but we tried.
                if assoc_journal is not None:
                    # Update the article's metadata, including in_doaj status
                    reg = models.Journal()
                    reg.set_id(assoc_journal.id)
                    changed = article_model.add_journal_metadata(assoc_journal, reg)

                    # cache the minified journal register
                    for issn in reg.bibjson().issns():
                        if issn not in journal_cache:
                            journal_cache[issn] = reg.data

                    if not changed:
                        same_count += 1
                        if prep_all:                    # This gets done below, but can override to prep unchanged ones here
                            article_model.prep()
                            write_batch.append(article_model.data)
                    else:
                        updated_count += 1
                        if write_changes:
                            article_model.prep()
                            write_batch.append(article_model.data)

                else:
                    # This article's Journal is no-more, or has evaded us; we delete the article.
                    deleted_count += 1
                    if write_changes:
                        delete_batch.add(article_model.id)

            except ValueError:
                # Failed to create model (this shouldn't happen!)
                failed_articles.append(json.dumps(a))
                continue

            # When we have reached the batch limit, do some writing or deleting
            if len(write_batch) >= batch_size:
                job.add_audit_message(u"Writing {x} articles".format(x=len(write_batch)))
                models.Article.bulk(write_batch)
                write_batch = []

            if len(delete_batch) >= batch_size:
                job.add_audit_message(u"Deleting {x} articles".format(x=len(delete_batch)))
                esprit.raw.bulk_delete(conn, 'article', delete_batch)
                delete_batch.clear()

        # Finish the last part-batches of writes or deletes
        if len(write_batch) > 0:
            job.add_audit_message(u"Writing {x} articles".format(x=len(write_batch)))
            models.Article.bulk(write_batch)
        if len(delete_batch) > 0:
            job.add_audit_message(u"Deleting {x} articles".format(x=len(delete_batch)))
            esprit.raw.bulk_delete(conn, 'article', delete_batch)
            delete_batch.clear()

        if write_changes:
            job.add_audit_message(u"Done. {0} articles updated, {1} remain unchanged, and {2} deleted.".format(updated_count, same_count, deleted_count))
        else:
            job.add_audit_message(u"Done. Changes not written to index. {0} articles to be updated, {1} to remain unchanged, and {2} to be deleted. Set 'write' to write changes.".format(updated_count, same_count, deleted_count))

        if len(failed_articles) > 0:
            job.add_audit_message(u"Failed to create models for {x} articles in the index. Something is quite wrong.".format(x=len(failed_articles)))
            job.add_audit_message("Failed article ids: {x}".format(x=", ".join(failed_articles)))
            job.fail()

    def _get_best_journal(self, journals):
        if len(journals) == 1:
            return journals[0]

        # in_doaj
        # most recently updated (manual, then automatic)
        # both issns match
        result = { "in_doaj" : {}, "not_in_doaj" : {}}
        for j in journals:
            in_doaj = j.is_in_doaj()
            lmu = j.last_manual_update_timestamp
            lu = j.last_updated_timestamp

            context = None
            if in_doaj:
                context = result["in_doaj"]
            else:
                context = result["not_in_doaj"]

            if lmu is None:
                lmu = datetime.utcfromtimestamp(0)
            if lmu not in context:
                context[lmu] = {}
            context[lmu][lu] = j

        context = None
        if len(result["in_doaj"].keys()) > 0:
            context = result["in_doaj"]
        else:
            context = result["not_in_doaj"]

        lmus = context.keys()
        lmus.sort()
        context = context[lmus.pop()]

        lus = context.keys()
        lus.sort()
        best = context[lus.pop()]
        return best

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

        write = kwargs.get("write", True)
        prepall = kwargs.get("prepall", False)

        if not write and prepall:
            raise BackgroundException("'prepall' must be used with the 'write' parameter set to True (why prep but not save?)")

        params = {}
        cls.set_param(params, "write", write)
        cls.set_param(params, "prepall", prepall)

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        job.params = params
        if prepall:
            job.add_audit_message("'prepall' arg set. 'unchanged' articles will also have their indexes refreshed.")
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        article_cleanup_sync.schedule(args=(background_job.id,), delay=10)


@long_running.periodic_task(schedule("article_cleanup_sync"))
@write_required(script=True)
def scheduled_article_cleanup_sync():
    user = app.config.get("SYSTEM_USERNAME")
    job = ArticleCleanupSyncBackgroundTask.prepare(user)
    ArticleCleanupSyncBackgroundTask.submit(job)

@long_running.task()
@write_required(script=True)
def article_cleanup_sync(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ArticleCleanupSyncBackgroundTask(job)
    BackgroundApi.execute(task)
