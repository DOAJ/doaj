from portality.dao import DomainObject
from portality.models import Article
from copy import deepcopy

class JournalVolumeToC(DomainObject):
    __type__ = "toc"

    @classmethod
    def get_id(cls, journal_id, volume):
        q = ToCQuery(journal_id=journal_id, volume=volume, idonly=True)
        result = cls.query(q=q.query())
        ids = [hit.get("fields", {}).get("id") for hit in result.get("hits", {}).get("hits", [])]
        if len(ids) == 1:
            return ids[0]
        return None

    @classmethod
    def get_toc(cls, journal_id, volume):
        q = ToCQuery(journal_id=journal_id, volume=volume)
        result = cls.query(q=q.query())
        vols = [hit.get("_source") for hit in result.get("hits", {}).get("hits", [])]
        if len(vols) == 1:
            return cls(**vols[0])
        return None

    @classmethod
    def list_volumes(cls, journal_id):
        q = VolumesToCQuery(journal_id)
        res = cls.query(q=q.query())
        volumes = [term.get("term") for term in res.get("facets", {}).get("vols", {}).get("terms", [])]
        return volumes

    @classmethod
    def delete_by_volume(cls, journal_id, volume):
        q = ToCQuery(journal_id=journal_id, volume=volume)
        cls.delete_by_query(q.query())

    @property
    def about(self):
        return self.data.get("about")

    def set_about(self, journal_id):
        self.data["about"] = journal_id

    @property
    def issn(self):
        return self.data.get("issn", [])

    def set_issn(self, issns):
        if not isinstance(issns, list):
            issns = [issns]
        self.data["issn"] = issns

    def add_issn(self, issn):
        if "issn" not in self.data:
            self.data["issn"] = []
        self.data["issn"].append(issn)

    @property
    def volume(self):
        return self.data.get("volume")

    def set_volume(self, vol):
        self.data["volume"] = vol

    @property
    def issues(self):
        return [JournalIssueToC(i) for i in self.data.get("issues", [])]

    def set_issues(self, issues):
        if "issues" in self.data:
            del self.data["issues"]
        if not isinstance(issues, list):
            issues = [issues]
        for i in issues:
            self.add_issue(i)

    def add_issue(self, issue):
        if "issues" not in self.data:
            self.data["issues"] = []
        if isinstance(issue, JournalIssueToC):
            issue = issue.data
        self.data["issues"].append(issue)
        self._sort_issues()

    def get_issue(self, number):
        for issue in self.issues:
            if issue.number == number:
                return issue
        return None

    def _sort_issues(self):
        # first extract the array we want to sort on
        # and make a map of that value to the issue itself
        numbers = []
        imap = {}
        for iss in self.issues:
            numbers.append(iss.number)
            imap[iss.number] = iss

        # now do the combined numeric and non-numeric sorting
        numeric = []
        non_numeric = []
        nmap = {}
        for n in numbers:
            try:
                # try to convert n to an int
                nint = int(n)
                numeric.append(nint)

                # remember the original string (it may have leading 0s)
                nmap[nint] = n
            except:
                non_numeric.append(n)

        numeric.sort(reverse=True)
        non_numeric.sort(reverse=True)

        sorted_keys = [nmap[n] for n in numeric] + non_numeric # convert the numbers back to their original representations
        sorted_issues = [imap[n].data for n in sorted_keys]

        self.data["issues"] = sorted_issues

class JournalIssueToC(object):

    def __init__(self, raw=None):
        self.data = raw if raw is not None else {}

    @property
    def number(self):
        return self.data.get("number")

    @number.setter
    def number(self, num):
        self.data["number"] = num

    @property
    def year(self):
        return self.data.get("year")

    @year.setter
    def year(self, y):
        self.data["year"] = y

    @property
    def month(self):
        return self.data.get("month")

    @month.setter
    def month(self, m):
        self.data["month"] = m

    @property
    def articles(self):
        return [Article(**a) for a in self.data.get("articles", [])]

    @articles.setter
    def articles(self, arts):
        if "articles" in self.data:
            del self.data["articles"]
        if not isinstance(arts, list):
            arts = [arts]
        for a in arts:
            self.add_article(a)

    def add_article(self, article):
        if "articles" not in self.data:
            self.data["articles"] = []
        if isinstance(article, Article):
            article = article.data
        self.data["articles"].append(article)
        self._sort_articles()

    def _sort_articles(self):
        # first extract the array we want to sort on
        # and make a map of that value to the issue itself
        unsorted = []
        numbers = []
        imap = {}
        for art in self.articles:
            sp = art.bibjson().start_page

            # can't sort anything that doesn't have a start page
            if sp is None:
                unsorted.append(art)
                continue

            # deal with start page clashes and record the start pages
            # to sort by
            if sp not in numbers:
                numbers.append(sp)
            if sp in imap:
                imap[sp].append(art)
            else:
                imap[sp] = [art]

        # now do the combined numeric and non-numeric sorting
        numeric = []
        non_numeric = []
        nmap = {}
        for n in numbers:
            try:
                # try to convert n to an int
                nint = int(n)
                numeric.append(nint)

                # remember the original string
                nmap[nint] = n
            except:
                non_numeric.append(n)

        numeric.sort()
        non_numeric.sort()

        sorted_keys = [nmap[n] for n in numeric] + non_numeric # convert the numbers back to their original representations
        s = []
        for n in sorted_keys:
            s += [x.data for x in imap[n]]
        s += [x.data for x in unsorted]

        self.data["articles"] = s

class VolumesToCQuery(object):
    base_query = {
        "query" : {
            "term" : {"about.exact" : "<journal id>"}
        },
        "size" : 0,
        "facets" : {
            "vols" : {
                "terms" : {
                    "field" : "volume.exact",
                    "size" : 100
                }
            }
        }
    }

    def __init__(self, journal_id):
        self.journal_id = journal_id

    def query(self):
        q = deepcopy(self.base_query)
        q["query"]["term"]["about.exact"] = self.journal_id
        return q

class ToCQuery(object):
    base_query = {
        "query" : {
            "bool" : {
                "must" : []
            }
        }
    }

    _journal_term = { "term" : {"about.exact" : "<journal id>"} }
    _volume_term = { "term" : {"volume.exact" : "<volume id>"}}

    def __init__(self, journal_id=None, volume=None, idonly=False):
        self.journal_id = journal_id
        self.volume = volume
        self.idonly = idonly

    def query(self):
        q = deepcopy(self.base_query)

        if self.journal_id is not None:
            jt = deepcopy(self._journal_term)
            jt["term"]["about.exact"] = self.journal_id
            q["query"]["bool"]["must"].append(jt)

        if self.volume is not None:
            vt = deepcopy(self._volume_term)
            vt["term"]["volume.exact"] = self.volume
            q["query"]["bool"]["must"].append(vt)

        if self.idonly:
            q["fields"] = ["id"]

        return q