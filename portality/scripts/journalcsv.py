import os
import codecs
from portality import models
from portality.core import app
from portality.journalcsv import make_journals_csv
from datetime import datetime
from operator import itemgetter
import sys

if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
    print "System is in READ-ONLY mode, script cannot run"
    exit()

cdir = app.config.get("CACHE_DIR")
if cdir is None:
    print "You must set CACHE_DIR in the config"
    exit()

csvdir = os.path.join(cdir, "csv")

# save it into the cache directory
attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '_utf8.csv'
out = os.path.join(csvdir, attachment_name)

# Avoid unicode issues by forcing the whole system to use unicode. fixme: is this a hack? :)
reload(sys)
sys.setdefaultencoding('utf8')

# write the csv file
with codecs.open(out, 'wb', encoding='utf8') as csvfile:
    make_journals_csv(csvfile)

# update the ES record to point to the new file
models.Cache.cache_csv(attachment_name)

# remove all but the two latest csvs
csvs = [(c, os.path.getmtime(os.path.join(csvdir, c)) ) for c in os.listdir(csvdir) if c.endswith(".csv")]
sorted_csvs = sorted(csvs, key=itemgetter(1), reverse=True)

if len(sorted_csvs) > 2:
    for c, lm in sorted_csvs[2:]:
        os.remove(os.path.join(csvdir, c))









