from portality import models

class Choices(object):

    ##
    @classmethod
    def choices_for_article_issns(cls, user, article_id=None):
        if "admin" in user.role and article_id is not None:
            a = models.Article.pull(article_id)
            issns = models.Journal.issns_by_owner(a.get_owner())
        else:
            issns = models.Journal.issns_by_owner(user.id)
        ic = [("", "Select an ISSN")] + [(i, i) for i in issns]
        return ic
