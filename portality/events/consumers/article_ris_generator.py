# ~~ AccountCreatedEmail:Consumer ~~
from portality.bll import DOAJ
from portality.events.consumer import EventConsumer
from portality import constants, models


class ArticleRISGenerator(EventConsumer):
    ID = "article:ris_generator"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_ARTICLE_SAVE and event.context.get("article") is not None

    @classmethod
    def consume(cls, event):
        context = event.context

        if "article" not in context:
            raise Exception("No article found in event context")

        # this could raise an exception, which will cause the event not be be consumed, and will be
        # caught and logged at the level above
        article = models.Article(**context.get("article"))

        exportSvc = DOAJ.exportService()
        exportSvc.ris(article, save=True)
