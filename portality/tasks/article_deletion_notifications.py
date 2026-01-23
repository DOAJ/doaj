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
from portality.tasks.redis_huey import scheduled_long_queue as queue


class ArticleDeletionNotificationsBackgroundTask(BackgroundTask):
    __action__ = "article_deletion_notifications"

    def run(self):
        job = self.background_job

        # Determine date range: last 7 days
        since = dates.before_now(7 * 24 * 60 * 60)
        since_str = dates.format(since)

        # Query tombstones created in the last week
        q = {
            "query": {
                "range": {
                    "created_date": {"gte": since_str}
                }
            }
        }

        owner_to_items: Dict[str, List[dict]] = {}

        for stone in models.ArticleTombstone.iterate(q, page_size=1000):
            admin = getattr(stone, 'data', {}).get('admin', {}) if hasattr(stone, 'data') else {}
            owner = admin.get('owner')
            if not owner:
                continue

            bj = stone.bibjson()
            title = bj.title if hasattr(bj, 'title') else stone.data.get('bibjson', {}).get('title')
            authors = []
            try:
                for a in bj.author or []:
                    n = a.get('name') if isinstance(a, dict) else None
                    if n:
                        authors.append(n)
            except Exception:
                pass

            volume = bj.volume if hasattr(bj, 'volume') else None
            issue = bj.number if hasattr(bj, 'number') else None
            start_page = bj.start_page if hasattr(bj, 'start_page') else None
            end_page = bj.end_page if hasattr(bj, 'end_page') else None
            pages = None
            if start_page and end_page:
                pages = f"{start_page}-{end_page}"
            elif start_page:
                pages = str(start_page)

            issns = []
            try:
                issns = bj.issns()
            except Exception:
                pass

            journal_name = None
            try:
                journal_name = bj.journal_title
            except Exception:
                # fall back to raw
                journal_name = stone.data.get('bibjson', {}).get('journal', {}).get('title')

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

            # Build notification content
            short = "Deleted articles in your journal(s) this week"

            lines = [
                "The following articles have been deleted from DOAJ in the last week:",
                "",
            ]
            for it in items:
                auth = (", ".join(it['authors'])) if it['authors'] else "Unknown author"
                issn_str = ", ".join([i for i in (it.get('issns') or []) if i])
                vol_str = f", vol {it['volume']}" if it.get('volume') else ""
                iss_str = f", issue {it['issue']}" if it.get('issue') else ""
                pg_str = f", pages {it['pages']}" if it.get('pages') else ""
                jn = f" ({it['journal']})" if it.get('journal') else ""
                line = f"- {it['title'] or 'Untitled'} by {auth}{vol_str}{iss_str}{pg_str} [{issn_str}]{jn}"
                lines.append(line)
            lines.append("")
            lines.append("Please upload replacement records if appropriate.")

            note = models.Notification()
            note.who = owner
            note.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS
            note.short = short
            note.long = "\n".join(lines)

            notify_svc.notify(note)
            total_notes += 1

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
