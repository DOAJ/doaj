# ~~ AccountCreatedEmail:Consumer ~~
from portality.bll import DOAJ
from portality.events.consumer import EventConsumer
from portality import constants


class ArticleRISGenerator(EventConsumer):
    ID = "article:ris_generator"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_ARTICLE_SAVE and event.context.get("article_id") is not None

    @classmethod
    def consume(cls, event):
        context = event.context
        exportSvc = DOAJ.exportService()
        exportSvc.ris(context.get("article_id"), save=True)
