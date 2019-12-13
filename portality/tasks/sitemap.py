from portality import models
from portality.core import app

from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException

import os
from lxml import etree
from datetime import datetime
from operator import itemgetter

class SitemapBackgroundTask(BackgroundTask):

    __action__ = "sitemap"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job

        base_url = app.config.get("BASE_URL")
        if not base_url.endswith("/"):
            base_url += "/"
        cdir = app.config.get("CACHE_DIR")
        smdir = os.path.join(cdir, "sitemap")
        toc_changefreq = app.config.get("TOC_CHANGEFREQ", "monthly")

        if not os.path.exists(smdir):
            os.makedirs(smdir)

        NSMAP = {None : "http://www.sitemaps.org/schemas/sitemap/0.9"}
        NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urlset = etree.Element(NS + "urlset", nsmap=NSMAP)

        counter = 0

        # do the static pages
        statics = app.config.get("STATIC_PAGES", [])
        for path, change in statics:
            if path.startswith("/"):
                path = path[1:]
            stat_loc = base_url + path
            url = etree.SubElement(urlset, NS + "url")
            loc = etree.SubElement(url, NS + "loc")
            loc.text = stat_loc
            cf = etree.SubElement(url, NS + "changefreq")
            cf.text = change
            counter += 1

        # do all the journal ToCs
        for j in models.Journal.all_in_doaj():

            # first create an entry purely for the journal
            toc_loc = base_url + "toc/" + j.toc_id
            lastmod = j.last_updated

            url = etree.SubElement(urlset, NS + "url")
            loc = etree.SubElement(url, NS + "loc")
            loc.text = toc_loc
            if lastmod is not None:
                lm = etree.SubElement(url, NS + "lastmod")
                lm.text = lastmod
            cf = etree.SubElement(url, NS + "changefreq")
            cf.text = toc_changefreq
            counter += 1

        # log to the screen
        job.add_audit_message("{x} urls written to sitemap".format(x=counter))

        # save it into the cache directory
        attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '.xml'
        out = os.path.join(smdir, attachment_name)
        tree = etree.ElementTree(urlset)
        with open(out, "wb") as f:
            tree.write(f, encoding="UTF-8", xml_declaration=True, pretty_print=True)

        # update the ES record to point to the new file
        models.Cache.cache_sitemap(attachment_name)

        job.add_audit_message("Sitemap written to cache directory with name {x}".format(x=attachment_name))

        # remove all but the two latest sitemaps
        sms = [(c, os.path.getmtime(os.path.join(smdir, c)) ) for c in os.listdir(smdir) if c.endswith(".xml")]
        sorted_sms = sorted(sms, key=itemgetter(1), reverse=True)

        if len(sorted_sms) > 2:
            for c, lm in sorted_sms[2:]:
                os.remove(os.path.join(smdir, c))

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

        base_url = app.config.get("BASE_URL")
        if base_url is None:
            raise BackgroundException("BASE_URL must be set in configuration before we can generate a sitemap")

        cdir = app.config.get("CACHE_DIR")
        if cdir is None:
            raise BackgroundException("You must set CACHE_DIR in the config")

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        generate_sitemap.schedule(args=(background_job.id,), delay=10)

@main_queue.periodic_task(schedule("sitemap"))
@write_required(script=True)
def scheduled_sitemap():
    user = app.config.get("SYSTEM_USERNAME")
    job = SitemapBackgroundTask.prepare(user)
    SitemapBackgroundTask.submit(job)

@main_queue.task()
@write_required(script=True)
def generate_sitemap(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SitemapBackgroundTask(job)
    BackgroundApi.execute(task)
