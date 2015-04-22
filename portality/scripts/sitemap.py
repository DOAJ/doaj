from portality import models
from portality.core import app
from lxml import etree
import os
from datetime import datetime
from operator import itemgetter

if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
    print "System is in READ-ONLY mode, script cannot run"
    exit()

base_url = app.config.get("BASE_URL")
if base_url is None:
    print "BASE_URL must be set in configuration before we can generate a sitemap"
    exit(0)
if not base_url.endswith("/"):
    base_url += "/"

cdir = app.config.get("CACHE_DIR")
if cdir is None:
    print "You must set CACHE_DIR in the config"
    exit()
smdir = os.path.join(cdir, "sitemap")

toc_changefreq = app.config.get("TOC_CHANGEFREQ", "monthly")

NSMAP = {None : "http://www.sitemaps.org/schemas/sitemap/0.9"}
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
urlset = etree.Element(NS + "urlset", nsmap=NSMAP)

counter = 0

# do the static pages
statics = app.config.get("STATIC_PAGES", [])
for path, change in statics:
    if path.startswith("/"):
        path = path[1:]
    stat_loc = base_url + path
    url = etree.SubElement(urlset, NS + "url")
    loc = etree.SubElement(url, NS + "loc")
    loc.text = stat_loc
    cf = etree.SubElement(url, NS + "changefreq")
    cf.text = change
    counter += 1

# do all the journal ToCs
for j in models.Journal.all_in_doaj(page_size=12000):
    
    # first create an entry purely for the journal
    toc_loc = base_url + "toc/" + j.toc_id
    lastmod = j.last_updated
    
    url = etree.SubElement(urlset, NS + "url")
    loc = etree.SubElement(url, NS + "loc")
    loc.text = toc_loc
    if lastmod is not None:
        lm = etree.SubElement(url, NS + "lastmod")
        lm.text = lastmod
    cf = etree.SubElement(url, NS + "changefreq")
    cf.text = toc_changefreq
    counter += 1
    
    # now create an entry for each volume in the journal
    volumes = models.JournalVolumeToC.list_volumes(j.id)
    for v in volumes:
        vol_loc = base_url + "toc/" + j.toc_id + "/" + v
        vurl = etree.SubElement(urlset, NS + "url")
        vloc = etree.SubElement(vurl, NS + "loc")
        vloc.text = vol_loc
        cf = etree.SubElement(vurl, NS + "changefreq")
        cf.text = toc_changefreq
        counter += 1
        
# log to the screen
print counter, "urls written to sitemap"

# save it into the cache directory
attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '.xml'
out = os.path.join(smdir, attachment_name)
tree = etree.ElementTree(urlset)
with open(out, "wb") as f:
    tree.write(f, encoding="UTF-8", xml_declaration=True, pretty_print=True)

# update the ES record to point to the new file
models.Cache.cache_sitemap(attachment_name)

# remove all but the two latest sitemaps
sms = [(c, os.path.getmtime(os.path.join(smdir, c)) ) for c in os.listdir(smdir) if c.endswith(".xml")]
sorted_sms = sorted(sms, key=itemgetter(1), reverse=True)

if len(sorted_sms) > 2:
    for c, lm in sorted_sms[2:]:
        os.remove(os.path.join(smdir, c))
