from portality.models.article import NoJournalException

def add_admin_field(article):

    # Take this opportunity to delete any empty journal license field since it's not supported in the bibjson struct
    if article.data.get('bibjson', {}).get('journal', {}).get('license') is not None:
        del article.data['bibjson']['journal']['license']

    if "admin" not in article.data:
        try:
            article.add_journal_metadata()
        except NoJournalException:
            print("\n Article with no journal found: " + article.id)
    return article
