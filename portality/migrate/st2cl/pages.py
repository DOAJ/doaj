import requests, os, sys, codecs

pages = {
    "home" : "http://www.doaj.org/doaj",
    "browse" : "http://www.doaj.org/doaj?func=browse",
    "search" : "http://www.doaj.org/doaj?func=search",
    "suggest" : "http://www.doaj.org/doaj?func=suggest",
    "suggest1" : "http://www.doaj.org/doaj?func=suggest&owner=1",
    "supportdoaj" : "http://www.doaj.org/doaj?func=loadTemplate&template=supportDoaj",
    "members" : "http://www.doaj.org/doaj?func=loadTemplate&template=members",
    "membership" : "http://www.doaj.org/doaj?func=membership",
    "support" : "http://www.doaj.org/doaj?func=support",
    "forpublishers" : "http://www.doaj.org/doaj?func=loadTemplate&template=forPublishers",
    "about" : "http://www.doaj.org/doaj?func=loadTemplate&template=about",
    "faq" : "http://www.doaj.org/doaj?func=loadTemplate&template=faq",
    "links" : "http://www.doaj.org/doaj?func=loadTempl&templ=links",
    "contact" : "http://www.doaj.org/doaj?func=contact"
}

languages = ["en", "fr", "es", "gr", "pt", "tr"]

OUT = "/home/richard/tmp/doaj/pages/"
if not os.path.exists(OUT):
    os.mkdir(OUT)
    
for lang in languages:
    for name, page in pages.items():
        url = None
        if "?" not in page:
            url = page + "?uiLanguage=" + lang
        else:
            url = page + "&uiLanguage=" + lang
        print url,
        sys.stdout.flush()
        resp = requests.get(url)
        if resp.status_code >= 400:
            print resp.status_code
            continue
        directory = os.path.join(OUT, lang)
        if not os.path.exists(directory):
            os.mkdir(directory)
        f = os.path.join(directory, name + ".html")
        with codecs.open(f, "wb", "utf8") as fh:
            fh.write(resp.text)
        print "done"
