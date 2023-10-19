import os
import shutil
import traceback
from typing import List, Callable

from portality import models
from portality.bll import DOAJ
from portality.bll.exceptions import IngestException, DuplicateArticleException, ArticleNotAcceptable
from portality.core import app
from portality.crosswalks.exceptions import CrosswalkException
from portality.models.uploads import BaseArticlesUpload


def file_failed(path):
    filename = os.path.split(path)[1]
    fad = app.config.get("FAILED_ARTICLE_DIR")
    dest = os.path.join(fad, filename)
    shutil.move(path, dest)


def mv_failed_file(path, job: models.BackgroundJob):
    try:
        file_failed(path)
        return True
    except:
        job.add_audit_message("Error cleaning up file which caused Exception: {x}"
                              .format(x=traceback.format_exc()))
        return False


def upload_process(articles_upload: BaseArticlesUpload,
                   job: models.BackgroundJob,
                   articles_path,
                   articles_factory: Callable[[str], List[models.Article]], ):
    """
    save articles and handle exception and status

    this function will update status `articles_upload` and `job`, but NOT save them.

    :param articles_upload:
    :param job:
    :param articles_path:
    :param articles_factory:
    :return:
    """

    ingest_exception = False
    result = {}
    articles = []
    try:
        articles = articles_factory(articles_path)
        account = models.Account.pull(articles_upload.owner)
        result = DOAJ.articleService().batch_create_articles(articles, account, add_journal_info=True)
    except (IngestException, CrosswalkException, ArticleNotAcceptable) as e:
        if hasattr(e, 'inner_message'):
            msg = "{exception}: {msg}. Inner message: {inner}. Stack: {x}".format(
                exception=e.__class__.__name__, msg=e.message, inner=e.inner_message, x=e.trace())
            upload_detail = e.inner_message
        else:
            msg = "{exception}: {msg}.".format(exception=e.__class__.__name__, msg=e.message)
            upload_detail = None

        result = e.result
        mark_fail_status(job, articles_upload, msg=msg, upload_msg=e.message, upload_detail=upload_detail)
        if mv_failed_file(articles_path, job):
            ingest_exception = True

    except DuplicateArticleException as e:
        mark_fail_status(job, articles_upload, msg=str(e))
        if not mv_failed_file(articles_path, job):
            return

    except Exception as e:
        mark_fail_status(job, articles_upload,
                         msg="Unanticipated error: {x}".format(x=traceback.format_exc()),
                         upload_msg="Unanticipated error when importing articles")
        if not mv_failed_file(articles_path, job):
            return

    success = result.get("success", 0)
    fail = result.get("fail", 0)
    update = result.get("update", 0)
    new = result.get("new", 0)
    shared = result.get("shared", [])
    unowned = result.get("unowned", [])
    unmatched = result.get("unmatched", [])

    if success == 0 and fail > 0 and not ingest_exception:
        articles_upload.failed("All articles in file failed to import")
        job.add_audit_message("All articles in file failed to import")
        job.outcome_fail()
    if success > 0 and fail == 0:
        articles_upload.processed(success, update, new)
    if success > 0 and fail > 0:
        articles_upload.partial(success, fail, update, new)
        job.add_audit_message("Some articles in file failed to import correctly, so no articles imported")

    articles_upload.set_failure_reasons(list(shared), list(unowned), list(unmatched))
    job.add_audit_message("Shared ISSNs: " + ", ".join(list(shared)))
    job.add_audit_message("Unowned ISSNs: " + ", ".join(list(unowned)))
    job.add_audit_message("Unmatched ISSNs: " + ", ".join(list(unmatched)))

    if new:
        ids = [a.id for a in articles]
        job.add_audit_message("Created/updated articles: " + ", ".join(list(ids)))

    if not ingest_exception:
        try:
            os.remove(articles_path)  # just remove the file, no need to keep it
        except Exception as e:
            job.add_audit_message(u"Error while deleting file {x}: {y}".format(x=articles_path, y=str(e)))


def mark_fail_status(job: models.BackgroundJob, file_upload: BaseArticlesUpload,
                     msg: str, upload_msg: str = None, upload_detail: str = None):
    upload_msg = upload_msg or msg
    job.add_audit_message(msg)
    job.outcome_fail()
    file_upload.failed(upload_msg, details=upload_detail)
