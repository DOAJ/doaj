from portality import models
from portality import article
from datetime import datetime
from portality.core import app

if app.config.get("READ_ONLY_MODE", False):
    print "System is in READ-ONLY mode, script cannot run"
    exit()

start = datetime.now()

xwalk = article.XWalk()
batch_size = 1000
total=0

article_iterator = models.Article.iterall(page_size=5000)
batch = []
for a in article_iterator:
    xwalk.add_journal_info(a)
    a.prep()
    batch.append(a.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print "writing", len(batch), "; total so far", total
        models.Article.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print "writing", len(batch), "; total so far", total
    models.Article.bulk(batch)

end = datetime.now()

print start, "-", end
