from StringIO import StringIO
from portality import models
from portality.core import app
import os, csv
from datetime import datetime
from operator import itemgetter

cdir = app.config.get("CACHE_DIR")
if cdir is None:
    print "You must set CACHE_DIR in the config"
    exit()

csvdir = os.path.join(cdir, "csv")

# FIXME: this was all fine when it happened synchronously to the user request, but
# now we're doing this offline, we should just have the writer write to the file
def get_csv_string(csv_row):
    '''
    csv.writer only writes to files - it'd be a lot easier if it
    could give us the string it generates, but it can't. This
    function uses StringIO to capture every CSV row that csv.writer
    produces and returns it.

    :param csv_row: A list of strings, each representing a CSV cell.
        This is the format required by csv.writer .
    '''
    csvstream = StringIO()
    csvwriter = csv.writer(csvstream, quoting=csv.QUOTE_ALL)
    # normalise the row - None -> "", and unicode > 128 to ascii
    csvwriter.writerow([unicode(c).encode("utf8", "replace") if c is not None else "" for c in csv_row])
    csvstring = csvstream.getvalue()
    csvstream.close()
    return csvstring

# generate the new csv
thecsv = ''
thecsv += get_csv_string(models.Journal.CSV_HEADER)

journal_iterator = models.Journal.all_in_doaj(page_size=10000)
for j in journal_iterator:
    thecsv += get_csv_string(j.csv())

# save it into the cache directory
attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '_utf8.csv'
out = os.path.join(csvdir, attachment_name)
with open(out, "wb") as f:
    f.write(thecsv)

# update the ES record to point to the new file
models.Cache.cache_csv(attachment_name)

# remove all but the two latest csvs
csvs = [(c, os.path.getmtime(os.path.join(csvdir, c)) ) for c in os.listdir(csvdir) if c.endswith(".csv")]
sorted_csvs = sorted(csvs, key=itemgetter(1), reverse=True)

if len(sorted_csvs) > 2:
    for c, lm in sorted_csvs[2:]:
        os.remove(os.path.join(csvdir, c))









