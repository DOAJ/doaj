"""Weekly notifications to publishers about articles deleted in the last week.
Collect article details from ArticleTombstone and send a Notification per owner.
"""
from typing import Dict, List

from portality import models, constants
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.lib import dates
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_short_queue as queue
from portality.util import url_for


class ArticleDeletionNotificationsBackgroundTask(BackgroundTask):
    __action__ = "article_deletion_notifications"

    def run(self):
        job = self.background_job

        # note we're using the doaj url_for wrapper, not the flask url_for directly, due to the request context hack required
        action_url = url_for("publisher.upload_file")

        # Query tombstones created in the last week
        # Determine date range: last 7 days
        since = dates.before_now(7 * 24 * 60 * 60)
        q = models.ArticleTombstoneRecentlyDeletedQuery(since=since)

        owner_to_items: Dict[str, List[dict]] = {}

        for stone in models.ArticleTombstone.iterate_unstable(q.query(), page_size=1000):
            owner = stone.owner
            if not owner:
                continue

            bj = stone.bibjson()
            title = bj.title
            authors = []
            for a in bj.author or []:
                n = a.get('name') if isinstance(a, dict) else None
                if n:
                    authors.append(n)

            volume = bj.volume
            issue = bj.number
            start_page = bj.start_page
            end_page = bj.end_page
            pages = None
            if start_page and end_page:
                pages = f"{start_page}-{end_page}"
            elif start_page:
                pages = str(start_page)
            issns = bj.issns()
            journal_name = bj.journal_title

            item = {
                'title': title,
                'authors': authors,
                'volume': volume,
                'issue': issue,
                'pages': pages,
                'issns': issns,
                'journal': journal_name,
            }

            owner_to_items.setdefault(owner, []).append(item)

        if not owner_to_items:
            job.add_audit_message("No deleted articles in the last week; no notifications sent.")
            return

        notify_svc = DOAJ.notificationsService()

        total_notes = 0
        for owner, items in owner_to_items.items():
            acc = models.Account.pull(owner)
            if acc is None:
                job.add_audit_message(f"Owner account {owner} not found; skipping {len(items)} items")
                continue

            source_id = "bg:job:" + self.__action__ + ":publisher"

            lines = []
            for it in items:
                auth = (", ".join(it['authors'])) if it['authors'] else "Unknown author"
                issn_str = ", ".join([i for i in (it.get('issns') or []) if i])
                vol_str = f", vol {it['volume']}" if it.get('volume') else ""
                iss_str = f", issue {it['issue']}" if it.get('issue') else ""
                pg_str = f", pages {it['pages']}" if it.get('pages') else ""
                jn = f" ({it['journal']})" if it.get('journal') else ""
                line = f"- {it['title'] or 'Untitled'} by {auth}{vol_str}{iss_str}{pg_str} [{issn_str}]{jn}"
                lines.append(line)

            note = models.Notification()
            note.who = owner
            note.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS
            note.long = notify_svc.long_notification(source_id).format(list_of_articles="\n".join(lines))
            note.short = notify_svc.short_notification(source_id)
            note.action = action_url

            notify_svc.notify(note)
            total_notes += 1
            job.add_audit_message(f"Sending notification for owner {owner} with {len(items)} deleted articles")

        job.add_audit_message(f"Sent {total_notes} publisher deletion notifications.")

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id)
        return job

    @classmethod
    def submit(cls, background_job):
        background_job.save()
        execute_article_deletion_notifications.schedule(args=(background_job.id,),
                                                        delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = ArticleDeletionNotificationsBackgroundTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_article_deletion_notifications():
    background_helper.submit_by_bg_task_type(ArticleDeletionNotificationsBackgroundTask)


@huey_helper.register_execute(is_load_config=False)
def execute_article_deletion_notifications(job_id):
    background_helper.execute_by_job_id(job_id, lambda j: ArticleDeletionNotificationsBackgroundTask(j))
