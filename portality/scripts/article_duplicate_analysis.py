import codecs
from copy import deepcopy
from datetime import datetime
from portality import clcsv

#duplicate_report = "/home/richard/tmp/doaj/article_duplicates_2019-03-29/duplicate_articles_global_2019-03-29.csv"
#noids_report = "/home/richard/tmp/doaj/article_duplicates_2019-03-29/noids_2019-03-29.csv"
#log =  "/home/richard/tmp/doaj/article_duplicates_2019-03-29/log.txt"
#out = "/home/richard/tmp/doaj/article_duplicates_2019-03-29/actions.csv"

duplicate_report = "/home/richard/tmp/doaj/article_duplicates_test_sheet.csv"
noids_report = "/home/richard/tmp/doaj/article_duplicates_2019-03-29/noids_2019-03-29.csv"
log =  "/home/richard/tmp/doaj/article_duplicates_test_sheet_log.txt"
out = "/home/richard/tmp/doaj/article_duplicates_test_sheet_actions.csv"

INVALID_DOIS = ["undefined", "-", "http://dx.doi.org/"]

class MatchSet(object):
    def __init__(self, typ=None):
        self._type = typ
        self._root = None
        self._matches = []

    def add_root(self, id, created, doi, fulltext, owner, issns, in_doaj, title_match):
        self._root = {
            "id" : id,
            "created": created,
            "doi" : doi,
            "fulltext" : fulltext,
            "owner" : owner,
            "issns" : issns,
            "in_doaj" : in_doaj,
            "title_match" : title_match
        }
        self._matches.append(self._root)

    def add_match(self, id, created, doi, fulltext, owner, issns, in_doaj, title_match):
        match = {
            "id" : id,
            "created": created,
            "doi" : doi,
            "fulltext" : fulltext,
            "owner" : owner,
            "issns" : issns,
            "in_doaj" : in_doaj,
            "title_match" : title_match
        }
        self._matches.append(match)

    def remove(self, ids):
        removes = []
        for i in range(len(self._matches)):
            if self._matches[i]["id"] in ids:
                removes.append(i)

        removes.sort(reverse=True)
        for r in removes:
            del self._matches[r]

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, typ):
        self._type = typ

    @property
    def matches(self):
        return self._matches

    @property
    def root(self):
        return self._root


class ActionRegister(object):
    def __init__(self):
        self._actions = {}

    def set_action(self, id, action, reason):
        if id not in self._actions:
            self._actions[id] = {action : [reason]}
            return

        act = self._actions[id]
        if action not in act:
            act[action] = [reason]
            return

        act[action].append(reason)

    def has_actions(self):
        return len(self._actions) > 0

    def report(self):
        return "\n".join(
            [k + " - " + "; ".join(
                [a + " (" + "|".join(b) + ")" for a, b in v.iteritems()]
            )
            for k, v in self._actions.iteritems()]
        )

    def export_to(self, final_instructions):
        resolved = self.resolve()
        for r in resolved:
            if r["id"] not in final_instructions:
                final_instructions[r["id"]] = {"action" : r["action"], "reason" : r["reason"]}
            else:
                if r["action"] == "delete":
                    final_instructions[r["id"]] = {"action" : "delete", "reason" : r["reason"]}

    def resolve(self):
        resolved_actions = []
        for k, v in self._actions.iteritems():
            resolved = {"id" : k, "action" : None, "reason" : None}
            if "delete" in v:
                resolved["action"] = "delete"
                resolved["reason"] = "; ".join(v["delete"])
            elif "remove_doi" in v and "remove_fulltext" in v:
                resolved["action"] = "delete"
                resolved["reason"] = "; ".join(v["remove_doi"]) + "|" + "; ".join("remove_fulltext")
            else:
                resolved["action"] = v.keys()[0]
                resolved["reason"] = "; ".join(v[resolved["action"]])
            resolved_actions.append(resolved)
        return resolved_actions


def analyse(duplicate_report, noids_report, out):

    with codecs.open(out, "wb", "utf-8") as o, \
            codecs.open(log, "wb", "utf-8") as l, \
            codecs.open(duplicate_report, "rb", "utf-8") as f:

        final_instructions = {}
        reader = clcsv.UnicodeReader(f)
        headers = reader.next()
        next_row = None
        while True:
            match_set, next_row = _read_match_set(reader, next_row)
            ids = [m["id"] for m in match_set.matches]
            l.write("--" + str(len(ids)) + "-- " + ",".join(ids) + "\n\n")

            # get rid of any articles from the match set that are not in doaj
            actions = ActionRegister()
            _eliminate_not_in_doaj(match_set, actions)

            cont = True
            if len(match_set.matches) == 1:
                _sanitise(match_set, actions)
                cont = False

            if cont:
                #_clean_doi_match_type(match_set, actions)
                #_clean_fulltext_match_type(match_set, actions)
                _clean_matching_dois(match_set, actions)
                _clean_matching_fulltexts(match_set, actions)
                _sanitise(match_set, actions)

            if len(match_set.matches) == 1:
                cont = False

            if cont:
                _remove_old(match_set, actions)

            """
            if cont:
                _remove_old_when_all_match(match_set, actions)

            if len(match_set.matches) == 1:
                cont = False

            if cont:
                _remove_old_when_no_ft_and_doi_title_match(match_set, actions)

            if len(match_set.matches) == 1:
                cont = False

            if cont:
                _remove_old_when_no_doi_and_ft_title_match(match_set, actions)
            """

            # report on the actions on this match set
            if actions.has_actions():
                l.write(actions.report())
                l.write("\n\n")

            actions.export_to(final_instructions)

            if next_row is None:
                break

        with codecs.open(noids_report, "rb", "utf-8") as n:
            nreader = clcsv.UnicodeReader(n)
            headers = nreader.next()
            for row in nreader:
                final_instructions[row[0]] = {"action" : "delete", "reason" : "no doi or fulltext"}

        writer = clcsv.UnicodeWriter(o)
        writer.writerow(["id", "action", "reason"])
        for k, v in final_instructions.iteritems():
            writer.writerow([k, v["action"], v["reason"]])


def _remove_old(match_set, actions):
    titles = [a["title_match"] for a in match_set.matches]
    if False in titles:
        return

    dois = [a["doi"] for a in match_set.matches]
    doiset = set(dois)
    doi_match = len(doiset) == 1 and "" not in dois
    no_doi = len(doiset) == 0

    fts = [a["fulltext"] for a in match_set.matches]
    ftset = set(fts)
    ft_match = len(ftset) == 1 and "" not in fts
    no_ft = len(ftset) == 0

    if (doi_match and ft_match) or (doi_match and no_ft) or (no_doi and ft_match):
        dateset = []
        for a in match_set.matches:
            created = datetime.strptime(a["created"], "%Y-%m-%dT%H:%M:%SZ")
            dateset.append({"created" : created, "id" : a["id"]})

        dateset.sort(key=lambda x : x["created"])
        dateset.pop()
        ids = [a["id"] for a in dateset]
        match_set.remove(ids)

        for id in ids:
            if no_doi:
                msg = "no doi; fulltext and title match, and newer article available"
            elif no_ft:
                msg = "no fulltext; doi and title match, and newer article available"
            else:
                msg = "doi, fulltext and title match, and newer article available"
            actions.set_action(id, "delete", msg)


def _remove_old_when_no_doi_and_ft_title_match(match_set, actions):
    if match_set.type != "fulltext":
        return

    dois = [a["doi"] for a in match_set.matches]
    dois = set(dois)
    if len(dois) > 1:
        return
    if "" not in dois:
        return

    titles = [a["title_match"] for a in match_set.matches]
    if False in titles:
        return

    # no doi and fulltext and titles all match, so we can throw away all the old stuff
    dateset = []
    for a in match_set.matches:
        created = datetime.strptime(a["created"], "%Y-%m-%dT%H:%M:%SZ")
        dateset.append({"created" : created, "id" : a["id"]})

    dateset.sort(key=lambda x : x["created"])
    dateset.pop()
    ids = [a["id"] for a in dateset]
    match_set.remove(ids)

    for id in ids:
        actions.set_action(id, "delete", "no doi; fulltext and title match, and newer article available")


def _remove_old_when_no_ft_and_doi_title_match(match_set, actions):
    if match_set.type != "doi":
        return

    fulltexts = [a["fulltext"] for a in match_set.matches]
    fulltexts = set(fulltexts)
    if len(fulltexts) > 1:
        return
    if "" not in fulltexts:
        return

    titles = [a["title_match"] for a in match_set.matches]
    if False in titles:
        return

    # no fulltext and doi and titles all match, so we can throw away all the old stuff
    dateset = []
    for a in match_set.matches:
        created = datetime.strptime(a["created"], "%Y-%m-%dT%H:%M:%SZ")
        dateset.append({"created" : created, "id" : a["id"]})

    dateset.sort(key=lambda x : x["created"])
    dateset.pop()
    ids = [a["id"] for a in dateset]
    match_set.remove(ids)

    for id in ids:
        actions.set_action(id, "delete", "no fulltext; doi and title match, and newer article available")

def _remove_old_when_all_match(match_set, actions):
    if match_set.type != "doi+fulltext":
        return

    titles = [a["title_match"] for a in match_set.matches]
    if False in titles:
        return

    # doi, fulltext and titles all match, so we can throw away all the old stuff
    dateset = []
    for a in match_set.matches:
        created = datetime.strptime(a["created"], "%Y-%m-%dT%H:%M:%SZ")
        dateset.append({"created" : created, "id" : a["id"]})

    dateset.sort(key=lambda x : x["created"])
    dateset.pop()
    ids = [a["id"] for a in dateset]
    match_set.remove(ids)

    for id in ids:
        actions.set_action(id, "delete", "doi, fulltext and title match, and newer article available")


def _clean_fulltext_match_type(match_set, actions):
    if match_set.type != "fulltext":
        return

    # this is a doi match
    dois = [a["doi"] for a in match_set.matches]
    if "" in dois:
        return

    doiset = set(dois)
    if len(dois) != len(doiset):
        return

    # all the dois are different
    for a in match_set.matches:
        actions.set_action(a["id"], "remove_fulltext", "duplicated fulltext, different dois")


def _clean_matching_fulltexts(match_set, actions):
    # first find out if the match set has a complete set of dois.  If not all the records
    # have dois we can't clean the Fulltexts out.
    dois = [a["doi"] for a in match_set.matches]
    if "" in dois:
        return

    # check that all the dois are unique.  If they are not, we can't remove the fulltexts
    doiset = set(dois)
    if len(dois) != len(doiset):
        return

    # get all the Fulltexts that exist, and remember which IDs have Fulltextss
    fts = []
    has_ft = []
    for a in match_set.matches:
        if a["fulltext"] != "":
            fts.append(a["fulltext"])
            has_ft.append(a["id"])

    # check that all the fulltexts we found are the same.  If they are not, we can't remove them
    ftset = set(fts)
    if len(ftset) != 1:
        return

    # all the fulltext are different, and the records all have the same doi, or do not have a DOI
    for id in has_ft:
        actions.set_action(id, "remove_fulltext", "duplicated fulltext, different doi")


def _clean_doi_match_type(match_set, actions):
    if match_set.type != "doi":
        return

    # this is a doi match
    fts = [a["fulltext"] for a in match_set.matches]
    if "" in fts:
        return

    ftset = set(fts)
    if len(fts) != len(ftset):
        return

    # all the fulltext are different
    for a in match_set.matches:
        actions.set_action(a["id"], "remove_doi", "duplicated doi, different fulltexts")

def _clean_matching_dois(match_set, actions):
    # first find out if the match set has a complete set of fulltexts.  If not all the records
    # have fulltexts we can't clean the DOIs out.
    fts = [a["fulltext"] for a in match_set.matches]
    if "" in fts:
        return

    # check that all the fulltexts are unique.  If they are not, we can't remove the DOIs
    ftset = set(fts)
    if len(fts) != len(ftset):
        return

    # get all the DOIs that exist, and remember which IDs have DOIs
    dois = []
    has_doi = []
    for a in match_set.matches:
        if a["doi"] != "":
            dois.append(a["doi"])
            has_doi.append(a["id"])

    # check that all the dois we found are the same.  If they are not, we can't remove them
    doiset = set(dois)
    if len(doiset) != 1:
        return

    # all the fulltext are different, and the records all have the same doi, or do not have a DOI
    for id in has_doi:
        actions.set_action(id, "remove_doi", "duplicated doi, different fulltexts")

def _sanitise(match_set, actions):
    for article in match_set.matches:
        if article["doi"] in INVALID_DOIS:
            if article["fulltext"] == "":
                actions.set_action(article["id"], "delete", "invalid doi, and no fulltext")
            else:
                actions.set_action(article["id"], "remove_doi", "invalid doi")


def _eliminate_not_in_doaj(match_set, actions):
    removes = []
    for i in range(len(match_set.matches)):
        article = match_set.matches[i]
        if not article["in_doaj"]:
            removes.append(article["id"])

    match_set.remove(removes)
    for r in removes:
        actions.set_action(r, "delete", "not in doaj")


def _read_match_set(reader, next_row):
    n_matches = -1
    match_set = MatchSet()
    while True:
        if next_row is not None:
            row = deepcopy(next_row)
            next_row = None
        else:
            try:
                row = reader.next()
            except StopIteration:
                return match_set, None

        if row is None:
            return match_set, None

        a_id = row[0]
        root = match_set.root
        if root is not None and a_id != root["id"]:
            return match_set, row

        a_created = row[1]
        a_doi = row[2]
        a_ft = row[3]
        a_owner = row[4]
        a_issns = row[5]
        a_in_doaj = row[6] == "True"

        if n_matches != -1:
            n_matches = int(row[7])

        match_type = row[8]

        b_id = row[9]
        b_created = row[10]
        b_doi = row[11]
        b_ft = row[12]
        b_owner = row[13]
        b_issns = row[14]
        b_in_doaj = row[15] == "True"

        title_match = row[17] == "True"

        if match_set.type is None:
            match_set.type = match_type

        if root is None:
            match_set.add_root(a_id, a_created, a_doi, a_ft, a_owner, a_issns, a_in_doaj, title_match)

        match_set.add_match(b_id, b_created, b_doi, b_ft, b_owner, b_issns, b_in_doaj, title_match)

    # a catch to make sure that everything is ok with the match set detection
    assert n_matches + 1 == len(match_set.matches)

analyse(duplicate_report, noids_report, out)
