"""
For each article in the DOAJ index:
    * Checks that it has a corresponding journal, deletes it otherwise
    * Ensures that the article in_doaj status is the same as the journal's
    * Applies the journal's information to the article metadata as needed
"""

from datetime import datetime

from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running


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

        # Scroll though all articles in the index
        i = 0
        for article_model in models.Article.iterate(q={"query": {"match_all": {}}, "sort": ["_doc"]}, page_size=100, wrap=True, keepalive='5m'):

            # for debugging, just print out the progress
            i += 1
            print(i, article_model.id, len(list(journal_cache.keys())), len(write_batch), len(delete_batch))

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
            if len(list(possibles.keys())) > 0:
                assoc_journal = self._get_best_journal(list(possibles.values()))

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

            # When we have reached the batch limit, do some writing or deleting
            if len(write_batch) >= batch_size:
                job.add_audit_message("Writing {x} articles".format(x=len(write_batch)))
                models.Article.bulk(documents=write_batch)
                write_batch = []

            if len(delete_batch) >= batch_size:
                job.add_audit_message("Deleting {x} articles".format(x=len(delete_batch)))
                models.Article.bulk_delete(delete_batch)
                delete_batch.clear()

        # Finish the last part-batches of writes or deletes
        if len(write_batch) > 0:
            job.add_audit_message("Writing {x} articles".format(x=len(write_batch)))
            models.Article.bulk(documents=write_batch)
        if len(delete_batch) > 0:
            job.add_audit_message("Deleting {x} articles".format(x=len(delete_batch)))
            models.Article.bulk_delete(delete_batch)
            delete_batch.clear()

        if write_changes:
            job.add_audit_message("Done. {0} articles updated, {1} remain unchanged, and {2} deleted.".format(updated_count, same_count, deleted_count))
        else:
            job.add_audit_message("Done. Changes not written to index. {0} articles to be updated, {1} to remain unchanged, and {2} to be deleted. Set 'write' to write changes.".format(updated_count, same_count, deleted_count))

        if len(failed_articles) > 0:
            job.add_audit_message("Failed to create models for {x} articles in the index. Something is quite wrong.".format(x=len(failed_articles)))
            job.add_audit_message("Failed article ids: {x}".format(x=", ".join(failed_articles)))
            job.fail()

    def _get_best_journal(self, journals):
        if len(journals) == 1:
            return list(journals)[0]

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
        if len(list(result["in_doaj"].keys())) > 0:
            context = result["in_doaj"]
        else:
            context = result["not_in_doaj"]

        lmus = list(context.keys())
        lmus.sort()
        context = context[lmus.pop()]

        lus = list(context.keys())
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
        job = background_helper.create_job(username=username,
                                           action=cls.__action__,
                                           params=params,
                                           queue_type=huey_helper.queue_type, )
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


huey_helper = ArticleCleanupSyncBackgroundTask.create_huey_helper(long_running)


@huey_helper.register_schedule
def scheduled_article_cleanup_sync():
    user = app.config.get("SYSTEM_USERNAME")
    job = ArticleCleanupSyncBackgroundTask.prepare(user)
    ArticleCleanupSyncBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def article_cleanup_sync(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ArticleCleanupSyncBackgroundTask(job)
    BackgroundApi.execute(task)
