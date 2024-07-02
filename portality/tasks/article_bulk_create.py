import json
from pathlib import Path
from typing import List

from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.core import app
from portality.crosswalks.exceptions import CrosswalkException
from portality.lib import dataobj
from portality.models.uploads import BulkArticles
from portality.tasks.helpers import background_helper, articles_upload_helper
from portality.tasks.redis_huey import main_queue


def get_upload_dir_path() -> Path:
    return Path(app.config.get("UPLOAD_ASYNC_DIR", "."))


def get_upload_path(upload: BulkArticles) -> Path:
    p = get_upload_dir_path()
    p.mkdir(parents=True, exist_ok=True)
    return p / upload.local_filename


def prep_article(data, account) -> models.Article:
    from portality.api.current import ArticlesCrudApi
    try:
        return ArticlesCrudApi.prep_article(data, account)
    except (
            dataobj.DataStructureException,
            dataobj.ScriptTagFoundException,
    ) as e:
        raise CrosswalkException(message=str(e))


class ArticleBulkCreateBackgroundTask(BackgroundTask):
    __action__ = "article_bulk_create"

    def run(self):
        job = self.background_job
        bulk_articles = BulkArticles.pull(self.get_param(job.params, "upload_id"))
        articles_path = get_upload_path(bulk_articles)
        uploader = models.Account.pull(job.user) or {}

        def _articles_factory(path):
            articles = (prep_article(d, uploader) for d in json.loads(Path(path).read_text()))
            return [models.Article(**raw) for raw in articles]

        articles_upload_helper.upload_process(bulk_articles, job, articles_path, _articles_factory)
        bulk_articles.save()

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, incoming_articles: List[dict] = None, **kwargs):
        bulk_articles = BulkArticles()
        bulk_articles.incoming(username)
        bulk_articles.save()

        # create articles json file in local for `run`
        articles_json_path = get_upload_path(bulk_articles)
        if articles_json_path.exists():
            app.logger.warning(f'bulk_articles file already exist. -- {articles_json_path.as_posix()}')
            articles_json_path.unlink()
        articles_json_path.write_text(json.dumps(incoming_articles))

        params = {}
        cls.set_param(params, "upload_id", bulk_articles.id)

        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            queue_id=huey_helper.queue_id,
                                            params=params, )

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(background_job, article_bulk_create)


huey_helper = ArticleBulkCreateBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_execute(is_load_config=False)
def article_bulk_create(job_id):
    background_helper.execute_by_job_id(job_id, ArticleBulkCreateBackgroundTask)