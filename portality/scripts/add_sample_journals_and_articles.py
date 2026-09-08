from datetime import datetime
from portality.models import Journal, Article
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory


def create_journals_and_articles():
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    now_iso = now.isoformat() + 'Z'
    journal_ids = []
    eissns = []
    print('Creating 5 new Journals...')
    for i in range(1, 6):
        overlay = {
            "bibjson": {
                "title": f"Test Journal {i} - {now_str}",
                "eissn": random_issn(),
                "pissn": random_issn()
            },
            "created_date": now_iso
        }
        source = JournalFixtureFactory.make_journal_source(in_doaj=True, overlay=overlay)
        journal = Journal(**source)
        journal.set_id(journal.makeid())
        journal.save()
        journal_ids.append(journal.id)
        eissns.append(source['bibjson']['eissn'])
        print(f"Journal {journal.id} created: {source['bibjson']['title']}")

    print('Creating 5 new Articles...')
    for i in range(1, 6):
        overlay = {
            "bibjson": {
                "title": f"Test Article {i} - {now_str}",
                "journal": {"title": f"Test Journal {i} - {now_str}"}
            },
            "created_date": now_iso
        }
        source = ArticleFixtureFactory.make_article_source(eissn=eissns[i-1], overlay=overlay)
        article = Article(**source)
        article.set_id(article.makeid())
        article.save()
        print(f"Article {article.id} created: {source['bibjson']['title']}")

def random_issn():
    import random
    first3 = ''.join(random.choices('0123456789', k=3))
    last4 = ''.join(random.choices('0123456789', k=4))
    return f"X{first3}-{last4}"

if __name__ == "__main__":
    create_journals_and_articles()
