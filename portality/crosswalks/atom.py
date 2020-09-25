from flask import url_for
from portality.core import app


class AtomCrosswalk(object):
    def crosswalk(self, atom_record):
        entry = {}
        b = atom_record.bibjson()

        doaj_url = app.config['BASE_URL'] + url_for('doaj.toc', identifier=atom_record.toc_id) + "?rss"

        title = b.title
        issns = b.issns()
        if len(issns) > 0:
            title += " (" + ", ".join(issns) + ")"

        summary = ""
        if b.publisher:
            summary += "Published by " + b.publisher
        if b.institution:
            if not b.publisher:
                summary += "Published in " + b.institution
            else:
                summary += " in " + b.institution
        if summary != "":
            summary += "\n"
        summary += "Added to DOAJ on " + atom_record.created_timestamp.strftime("%e %b %Y") + "\n"
        lccs = b.lcc_paths()
        if len(lccs) > 0:
            summary += "LCC Subject Category: " + " | ".join(lccs)

        if b.publisher is not None:
            entry["author"] = b.publisher
        elif b.provider is not None:
            entry["author"] = b.provider
        else:
            entry["author"] = app.config.get("SERVICE_NAME")

        cats = []
        for subs in b.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            cats.append(scheme + ":" + term)
        entry["categories"] = cats

        entry["content_src"] = doaj_url
        entry["alternate"] = doaj_url

        entry["id"] = "urn:uuid:" + atom_record.id

        urls = b.get_urls(urltype="homepage")
        if len(urls) > 0:
            entry['related'] = urls[0]

        entry['rights'] = app.config['FEED_LICENCE']

        entry['summary'] = summary
        entry['title'] = title
        entry['updated'] = atom_record.last_updated

        return entry
