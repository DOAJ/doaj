from portality.dao import DomainObject
from portality.models import GenericBibJSON
from copy import deepcopy
from datetime import datetime
from portality import xwalk

class Article(DomainObject):
    __type__ = "article"

    @classmethod
    def duplicates(cls, issns=None, publisher_record_id=None, doi=None, fulltexts=None, title=None, volume=None, number=None, start=None, should_match=None):
        # some input sanitisation
        issns = issns if isinstance(issns, list) else []
        urls = fulltexts if isinstance(fulltexts, list) else [fulltexts] if isinstance(fulltexts, str) or isinstance(fulltexts, unicode) else []

        q = DuplicateArticleQuery(issns=issns,
                                    publisher_record_id=publisher_record_id,
                                    doi=doi,
                                    urls=urls,
                                    title=title,
                                    volume=volume,
                                    number=number,
                                    start=start,
                                    should_match=should_match)
        # print json.dumps(q.query())

        res = cls.query(q=q.query())
        articles = [cls(**hit.get("_source")) for hit in res.get("hits", {}).get("hits", [])]
        return articles

    @classmethod
    def list_volumes(cls, issns):
        q = ArticleVolumesQuery(issns)
        result = cls.query(q=q.query())
        return [t.get("term") for t in result.get("facets", {}).get("vols", {}).get("terms", [])]

    @classmethod
    def list_volume_issues(cls, issns, volume):
        q = ArticleVolumesIssuesQuery(issns, volume)
        result = cls.query(q=q.query())
        return [t.get("term") for t in result.get("facets", {}).get("issues", {}).get("terms", [])]

    @classmethod
    def get_by_volume(cls, issns, volume):
        q = ArticleQuery(issns=issns, volume=volume)
        articles = cls.iterate(q.query(), page_size=1000)
        return articles

    @classmethod
    def get_by_volume_issue(cls, issns, volume, issue):
        q = ArticleIssueQuery(issns=issns, volume=volume, issue=issue)
        articles = cls.query(q=q.query())
        return [i['fields'] for i in articles.get('hits',{}).get('hits',[])]

    @classmethod
    def find_by_issns(cls, issns):
        q = ArticleQuery(issns=issns)
        articles = cls.iterate(q.query(), page_size=1000)
        return articles

    @classmethod
    def delete_selected(cls, query=None, owner=None, snapshot=True):
        if owner is not None:
            from portality.models import Journal
            issns = Journal.issns_by_owner(owner)
            q = ArticleQuery(issns=issns)
            query = q.query()

        if snapshot:
            articles = cls.iterate(query, page_size=1000)
            for article in articles:
                article.snapshot()

        cls.delete_by_query(query)

    def bibjson(self):
        if "bibjson" not in self.data:
            self.data["bibjson"] = {}
        return ArticleBibJSON(self.data.get("bibjson"))

    def set_bibjson(self, bibjson):
        bibjson = bibjson.bibjson if isinstance(bibjson, ArticleBibJSON) else bibjson
        self.data["bibjson"] = bibjson

    def history(self):
        hs = self.data.get("history", [])
        tuples = []
        for h in hs:
            tuples.append((h.get("date"), ArticleBibJSON(h.get("bibjson"))))
        return tuples

    def snapshot(self):
        from portality.models import ArticleHistory

        snap = deepcopy(self.data)
        if "id" in snap:
            snap["about"] = snap["id"]
            del snap["id"]
        if "index" in snap:
            del snap["index"]
        if "last_updated" in snap:
            del snap["last_updated"]
        if "created_date" in snap:
            del snap["created_date"]

        hist = ArticleHistory(**snap)
        hist.save()

        # FIXME: make this use the article history class
        #snap = deepcopy(self.data.get("bibjson"))
        #self.add_history(snap)

    def add_history(self, bibjson, date=None):
        """Deprecated"""
        bibjson = bibjson.bibjson if isinstance(bibjson, ArticleBibJSON) else bibjson
        if date is None:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        snobj = {"date" : date, "bibjson" : bibjson}
        if "history" not in self.data:
            self.data["history"] = []
        self.data["history"].append(snobj)

    def is_in_doaj(self):
        return self.data.get("admin", {}).get("in_doaj", False)

    def set_in_doaj(self, value):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["in_doaj"] = value

    def publisher_record_id(self):
        return self.data.get("admin", {}).get("publisher_record_id")

    def set_publisher_record_id(self, pri):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["publisher_record_id"] = pri

    def upload_id(self):
        return self.data.get("admin", {}).get("upload_id")

    def set_upload_id(self, uid):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["upload_id"] = uid

    def merge(self, old, take_id=True):
        # this takes an old version of the article and brings
        # forward any useful information that is needed.  The rules of merge are:
        # - ignore "index" (it gets regenerated on save)
        # - always take the "created_date"
        # - any top level field that does not exist in the current item (esp "id" and "history")
        # - in "admin", copy any field that does not already exist

        # first thing to do is create a snapshot of the old record
        old.snapshot()

        # now go on and do the merge

        # always take the created date
        self.set_created(old.created_date)

        # take the id
        if self.id is None or take_id:
            self.set_id(old.id)

        # take the history (deprecated)
        if len(self.data.get("history", [])) == 0:
            self.data["history"] = deepcopy(old.data.get("history", []))

        # take the bibjson
        if "bibjson" not in self.data:
            self.set_bibjson(deepcopy(old.bibjson()))

        # take the admin if there isn't one
        if "admin" not in self.data:
            self.data["admin"] = deepcopy(old.data.get("admin", {}))
        else:
            # otherwise, copy any admin keys that don't exist on the current item
            oa = old.data.get("admin", {})
            for key in oa:
                if key not in self.data["admin"]:
                    self.data["admin"][key] = deepcopy(oa[key])

    def _generate_index(self):
        # the index fields we are going to generate
        issns = []
        subjects = []
        schema_subjects = []
        schema_codes = []
        classification = []
        langs = []
        country = None
        license = []
        publisher = []

        # the places we're going to get those fields from
        cbib = self.bibjson()
        jindex = self.data.get('index', {})
        hist = self.history()

        # get the issns out of the current bibjson
        issns += cbib.get_identifiers(cbib.P_ISSN)
        issns += cbib.get_identifiers(cbib.E_ISSN)

        # now get the issns out of the historic records
        for date, hbib in hist:
            issns += hbib.get_identifiers(hbib.P_ISSN)
            issns += hbib.get_identifiers(hbib.E_ISSN)

        # get the subjects and concatenate them with their schemes from the current bibjson
        for subs in cbib.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            subjects.append(term)
            schema_subjects.append(scheme + ":" + term)
            classification.append(term)
            if "code" in subs:
                schema_codes.append(scheme + ":" + subs.get("code"))

        # copy the languages
        if cbib.journal_language is not None:
            langs = cbib.journal_language

        # copy the country
        if jindex.get('country'):
            country = jindex.get('country')
        elif cbib.journal_country:
            country = xwalk.get_country_name(cbib.journal_country)

        # get the title of the license
        lic = cbib.get_journal_license()
        if lic is not None:
            license.append(lic.get("title"))

        # copy the publisher/provider
        if cbib.publisher:
            publisher.append(cbib.publisher)

        # deduplicate the list
        issns = list(set(issns))
        subjects = list(set(subjects))
        schema_subjects = list(set(schema_subjects))
        classification = list(set(classification))
        license = list(set(license))
        publisher = list(set(publisher))
        langs = list(set(langs))
        schema_codes = list(set(schema_codes))

        # work out what the date of publication is
        date = cbib.get_publication_date()

        # build the index part of the object
        self.data["index"] = {}
        if len(issns) > 0:
            self.data["index"]["issn"] = issns
        if date != "":
            self.data["index"]["date"] = date
        if len(subjects) > 0:
            self.data["index"]["subject"] = subjects
        if len(schema_subjects) > 0:
            self.data["index"]["schema_subject"] = schema_subjects
        if len(classification) > 0:
            self.data["index"]["classification"] = classification
        if len(publisher) > 0:
            self.data["index"]["publisher"] = publisher
        if len(license) > 0:
            self.data["index"]["license"] = license
        if len(langs) > 0:
            self.data["index"]["language"] = langs
        if country is not None:
            self.data["index"]["country"] = country
        if schema_codes > 0:
            self.data["index"]["schema_code"] = schema_codes

    def prep(self):
        self._generate_index()
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def save(self):
        self._generate_index()
        super(Article, self).save()

class ArticleBibJSON(GenericBibJSON):

    # article-specific simple getters and setters
    @property
    def year(self): return self.bibjson.get("year")
    @year.setter
    def year(self, val) : self.bibjson["year"] = str(val)
    @year.deleter
    def year(self):
        if "year" in self.bibjson:
            del self.bibjson["year"]

    @property
    def month(self): return self.bibjson.get("month")
    @month.setter
    def month(self, val) : self.bibjson["month"] = str(val)
    @month.deleter
    def month(self):
        if "month" in self.bibjson:
            del self.bibjson["month"]

    @property
    def start_page(self): return self.bibjson.get("start_page")
    @start_page.setter
    def start_page(self, val) : self.bibjson["start_page"] = val

    @property
    def end_page(self): return self.bibjson.get("end_page")
    @end_page.setter
    def end_page(self, val) : self.bibjson["end_page"] = val

    @property
    def abstract(self): return self.bibjson.get("abstract")
    @abstract.setter
    def abstract(self, val) : self.bibjson["abstract"] = val

    # article-specific complex part getters and setters

    def _set_journal_property(self, prop, value):
        if "journal" not in self.bibjson:
            self.bibjson["journal"] = {}
        self.bibjson["journal"][prop] = value

    @property
    def volume(self):
        return self.bibjson.get("journal", {}).get("volume")

    @volume.setter
    def volume(self, value):
        self._set_journal_property("volume", value)

    @property
    def number(self):
        return self.bibjson.get("journal", {}).get("number")

    @number.setter
    def number(self, value):
        self._set_journal_property("number", value)

    @property
    def journal_title(self):
        return self.bibjson.get("journal", {}).get("title")

    @journal_title.setter
    def journal_title(self, title):
        self._set_journal_property("title", title)

    @property
    def journal_language(self):
        return self.bibjson.get("journal", {}).get("language")

    @journal_language.setter
    def journal_language(self, lang):
        self._set_journal_property("language", lang)

    # beware, the index part of an article will contain the same as the
    # index part of a journal, not the same as the bibjson part of a
    # journal!
    # the method below is referring to the bibjson part of a journal
    @property
    def journal_country(self):
        return self.bibjson.get("journal", {}).get("country")

    @journal_country.setter
    def journal_country(self, country):
        self._set_journal_property("country", country)

    @property
    def publisher(self):
        return self.bibjson.get("journal", {}).get("publisher")

    @publisher.setter
    def publisher(self, value):
        self._set_journal_property("publisher", value)

    def add_author(self, name, email=None, affiliation=None):
        if "author" not in self.bibjson:
            self.bibjson["author"] = []
        aobj = {"name" : name}
        if email is not None:
            aobj["email"] = email
        if affiliation is not None:
            aobj["affiliation"] = affiliation
        self.bibjson["author"].append(aobj)

    @property
    def author(self):
        return self.bibjson.get("author", [])

    def set_journal_license(self, licence_title, licence_type, url=None, version=None, open_access=None):
        lobj = {"title" : licence_title, "type" : licence_type}
        if url is not None:
            lobj["url"] = url
        if version is not None:
            lobj["version"] = version
        if open_access is not None:
            lobj["open_access"] = open_access

        self._set_journal_property("license", [lobj])

    def get_journal_license(self):
        return self.bibjson.get("journal", {}).get("license", [None])[0]

    def get_publication_date(self):
        # work out what the date of publication is
        date = ""
        if self.year is not None:
            # fix 2 digit years
            if len(self.year) == 2:
                if int(self.year) <=13:
                    self.year = "20" + self.year
                else:
                    self.year = "19" + self.year

            # if we still don't have a 4 digit year, forget it
            if len(self.year) != 4:
                return date

            # build up our proposed datestamp
            date += str(self.year)
            if self.month is not None:
                try:
                    if len(self.month) == 1:
                        date += "-0" + str(self.month)
                    else:
                        date += "-" + str(self.month)
                except:
                    # FIXME: months are in all sorts of forms, we can only handle
                    # numeric ones right now
                    date += "-01"
            else:
                date += "-01"
            date += "-01T00:00:00Z"

            # attempt to confirm the format of our datestamp
            try:
                datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            except:
                return ""
        return date

    def remove_journal_metadata(self):
        if "journal" in self.bibjson:
            del self.bibjson["journal"]

class ArticleQuery(object):
    base_query = {
        "query" : {
            "filtered": {
                "filter": {
                    "bool" : {
                        "must" : []
                    }
                }
            }
        }
    }

    _issn_terms = { "terms" : {"index.issn.exact" : ["<list of issns here>"]} }
    _volume_term = { "term" : {"bibjson.journal.volume.exact" : "<volume here>"} }

    def __init__(self, issns=None, volume=None):
        self.issns = issns
        self.volume = volume

    def query(self):
        q = deepcopy(self.base_query)

        if self.issns is not None:
            iq = deepcopy(self._issn_terms)
            iq["terms"]["index.issn.exact"] = self.issns
            q["query"]["filtered"]["filter"]["bool"]["must"].append(iq)

        if self.volume is not None:
            vq = deepcopy(self._volume_term)
            vq["term"]["bibjson.journal.volume.exact"] = self.volume
            q["query"]["filtered"]["filter"]["bool"]["must"].append(vq)

        return q

class ArticleIssueQuery(object):
    base_query = {
        "query" : {
            "filtered": {
                "filter": {
                    "bool" : {
                        "must" : []
                    }
                }
            }
        },
        "sort": "bibjson.start_page",
        "size": 100000,
        "fields": [
            "id",
            "bibjson.journal.volume",
            "bibjson.journal.number",
            "bibjson.title",
            "bibjson.author.name",
            "bibjson.link.url",
            "bibjson.start_page",
            "bibjson.end_page",
            "bibjson.abstract",
            "bibjson.month",
            "bibjson.year"
        ]
    }

    _issn_terms = { "terms" : {"index.issn.exact" : ["<list of issns here>"]} }
    _volume_term = { "term" : {"bibjson.journal.volume.exact" : "<volume here>"} }
    _issue_term = { "term" : {"bibjson.journal.number.exact" : "<issue here>"} }
    _noissue_term = { "missing" : {"field": "bibjson.journal.number.exact"} }

    def __init__(self, issns=None, volume=None, issue=None):
        self.issns = issns
        self.volume = volume
        self.issue = issue

    def query(self):
        q = deepcopy(self.base_query)

        if self.issns is not None:
            iq = deepcopy(self._issn_terms)
            iq["terms"]["index.issn.exact"] = self.issns
            q["query"]["filtered"]["filter"]["bool"]["must"].append(iq)

        if self.volume is not None:
            vq = deepcopy(self._volume_term)
            vq["term"]["bibjson.journal.volume.exact"] = self.volume
            q["query"]["filtered"]["filter"]["bool"]["must"].append(vq)

        if self.issue is not None:
            if self.issue == "unknown":
                isq = deepcopy(self._noissue_term)
            else:
                isq = deepcopy(self._issue_term)
                isq["term"]["bibjson.journal.number.exact"] = self.issue
            q["query"]["filtered"]["filter"]["bool"]["must"].append(isq)

        return q

    
class ArticleVolumesQuery(object):
    base_query = {
        "query" : {
            "filtered": {
                "filter": {
                    "terms" : {"index.issn.exact" : ["<list of issns here>"]}
                }
            }
        },
        "size" : 0,
        "facets" : {
            "vols" : {
                "terms" : {
                    "field" : "bibjson.journal.volume.exact",
                    "order": "reverse_term",
                    "size" : 1000
                }
            }
        }
    }

    def __init__(self, issns=None):
        self.issns = issns

    def query(self):
        q = deepcopy(self.base_query)
        q["query"]["filtered"]["filter"]["terms"]["index.issn.exact"] = self.issns
        return q

class ArticleVolumesIssuesQuery(object):
    base_query = {
        "query" : {
            "filtered": {
                "filter": {
                    "bool": {
                        "must": [
                            {"terms" : {"index.issn.exact" : ["<list of issns here>"]}},
                            {"term" : {"bibjson.journal.volume.exact" : "<volume here>"}}
                        ]
                    }
                }
            }
        },
        "size" : 0,
        "facets" : {
            "issues" : {
                "terms" : {
                    "field" : "bibjson.journal.number.exact",
                    "order": "reverse_term",
                    "size" : 1000
                }
            }
        }
    }

    def __init__(self, issns=None, volume=None):
        self.issns = issns
        self.volume = volume

    def query(self):
        q = deepcopy(self.base_query)
        q["query"]["filtered"]["filter"]["bool"]["must"][0]["terms"]["index.issn.exact"] = self.issns
        q["query"]["filtered"]["filter"]["bool"]["must"][1]["term"]["bibjson.journal.volume.exact"] = self.volume
        return q

class DuplicateArticleQuery(object):
    base_query = {
        "query" : {
            "bool" : {
                "must" : []
            }
        }
    }

    _should = {
        "should" : [],
        "minimum_should_match" : 2
    }

    _volume_term = {"term" : {"bibjson.journal.volume.exact" : "<volume>"}}
    _number_term = {"term" : {"bibjson.journal.number.exact" : "<issue number>"}}
    _start_term = {"term" : {"bibjson.start_page.exact" : "<start page>"}}
    _issn_terms = {"terms" : { "index.issn.exact" : ["<list of issns>"] }}
    _pubrec_term = {"term" : {"admin.publisher_record_id.exact" : "<publisher record id>"}}
    _identifier_term = {"term" : {"bibjson.identifier.id.exact" : "<doi or issn here>"}}
    _url_terms = {"terms" : {"bibjson.link.url.exact" : ["<urls here>"]}}
    _fuzzy_title = {"fuzzy" : {"bibjson.title.exact" : "<title here>"}}

    def __init__(self, issns=None, publisher_record_id=None, doi=None, urls=None, title=None, volume=None, number=None, start=None, should_match=None):
        self.issns = issns if isinstance(issns, list) else []
        self.publisher_record_id = publisher_record_id
        self.doi = doi
        self.urls = urls if isinstance(urls, list) else [urls] if isinstance(urls, str) or isinstance(urls, unicode) else []
        self.title = title
        self.volume = volume
        self.number = number
        self.start = start
        self.should_match = should_match

    def query(self):
        # - MUST be from at least one of the ISSNs
        # - MUST have the publisher record id
        # - MUST have the doi unless should_match is set
        # - MUST have the one of the fulltext urls unless should_match is set
        # - MUST fuzzy match the title
        # - SHOULD have <should_match> of: volume, issue, start page, fulltext url, doi

        q = deepcopy(self.base_query)
        if len(self.issns) > 0:
            it = deepcopy(self._issn_terms)
            it["terms"]["index.issn.exact"] = self.issns
            q["query"]["bool"]["must"].append(it)

        if self.publisher_record_id is not None:
            pr = deepcopy(self._pubrec_term)
            pr["term"]["admin.publisher_record_id.exact"] = self.publisher_record_id
            q["query"]["bool"]["must"].append(pr)

        if self.doi is not None and self.should_match is None:
            idt = deepcopy(self._identifier_term)
            idt["term"]["bibjson.identifier.id.exact"] = self.doi
            q["query"]["bool"]["must"].append(idt)

        if len(self.urls) > 0 and self.should_match is None:
            uq = deepcopy(self._url_terms)
            uq["terms"]["bibjson.link.url.exact"] = self.urls
            q["query"]["bool"]["must"].append(uq)

        if self.title is not None:
            ft = deepcopy(self._fuzzy_title)
            ft["fuzzy"]["bibjson.title.exact"] = self.title
            q["query"]["bool"]["must"].append(ft)

        if self.should_match is not None:
            term_count = 0
            s = deepcopy(self._should)

            if self.volume is not None:
                term_count += 1
                vt = deepcopy(self._volume_term)
                vt["term"]["bibjson.journal.volume.exact"] = self.volume
                s["should"].append(vt)

            if self.number is not None:
                term_count += 1
                nt = deepcopy(self._number_term)
                nt["term"]["bibjson.journal.number.exact"] = self.number
                s["should"].append(nt)

            if self.start is not None:
                term_count += 1
                st = deepcopy(self._start_term)
                st["term"]["bibjson.start_page.exact"] = self.start
                s["should"].append(st)

            if len(self.urls) > 0:
                term_count += 1
                uq = deepcopy(self._url_terms)
                uq["terms"]["bibjson.link.url.exact"] = self.urls
                s["should"].append(uq)

            if self.doi is not None:
                term_count += 1
                idt = deepcopy(self._identifier_term)
                idt["term"]["bibjson.identifier.id.exact"] = self.doi
                s["should"].append(idt)

            msm = self.should_match
            if msm > term_count:
                msm = term_count
            s["minimum_should_match"] = msm

            q["query"]["bool"].update(s)

        return q
