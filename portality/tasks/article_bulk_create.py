import json
from pathlib import Path
from typing import List

from portality import models
from portality.background import BackgroundTask
from portality.core import app
from portality.models.uploads import BulkArticles
from portality.tasks.helpers import background_helper, articles_upload_helper
from portality.tasks.redis_huey import long_running


def get_upload_path(upload: BulkArticles) -> Path:
    p = Path(app.config.get("UPLOAD_ASYNC_DIR", "."))
    p.mkdir(parents=True, exist_ok=True)
    return p / upload.local_filename


#########################################################
# Background task implementation


class ArticleBulkCreateBackgroundTask(BackgroundTask):
    __action__ = "article_bulk_create"

    def run(self):
        job = self.background_job
        bulk_articles = BulkArticles.pull(self.get_param(job.params, "upload_id"))
        articles_path = get_upload_path(bulk_articles)

        def _articles_factory(path):
            return [models.Article(**raw) for raw in json.loads(Path(path).read_text())]

        articles_upload_helper.upload_process(bulk_articles, job, articles_path, _articles_factory)
        bulk_articles.save()

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, articles: List[dict] = None, **kwargs):
        bulk_articles = BulkArticles()
        bulk_articles.incoming(username)
        bulk_articles.save()

        # create articles json file in local for `run`
        articles_json_path = get_upload_path(bulk_articles)
        if articles_json_path.exists():
            app.logger.warning(f'bulk_articles file already exist. -- {articles_json_path.as_posix()}')
            articles_json_path.unlink()
        articles_json_path.write_text(json.dumps(articles))

        params = {}
        cls.set_param(params, "upload_id", bulk_articles.id)

        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            queue_id=huey_helper.queue_id,
                                            params=params, )

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(background_job, article_bulk_create)


huey_helper = ArticleBulkCreateBackgroundTask.create_huey_helper(long_running)

article_bulk_create = huey_helper.create_common_execute_fn(is_load_config=False)
