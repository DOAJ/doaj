import os
from lxml import etree
from datetime import datetime
from portality.models import Journal, JournalBibJSON, Suggestion, Article, ArticleBibJSON

IN_DIR = "/home/richard/Dropbox/Documents/DOAJ/data/"

JOURNALS = IN_DIR + "journals"
SUBJECTS = IN_DIR + "subjects"
LCC = IN_DIR + "lccSubjects"
SUGGESTIONS = IN_DIR + "suggestions"

ARTICLES = [os.path.join(IN_DIR, f) for f in os.listdir(IN_DIR) if f.startswith("articles") and f != "articles.xsd"]

################################################################
## Preliminary data loading functions
################################################################

smap = {}
lccmap = {}

def load_subjects(subject_path, lcc_path):
    f = open(subject_path)
    subxml = etree.parse(f)
    f.close()
    
    f = open(lcc_path)
    lccxml = etree.parse(f)
    f.close()
    
    subjects = subxml.getroot()
    lccs = lccxml.getroot()
    
    # load the LCC subjects first - this is straightforward
    for subject in lccs:
        name = subject.find("name").text
        parent = subject.find("parent")
        if parent is not None:
            parent = parent.text
        lccmap[name] = {"p" : parent}
    
    for subject in subjects:
        name = subject.find("name").text
        parent = subject.find("parent")
        if parent is not None:
            parent = parent.text
        # NOTE: this is because there is one instance of a name having the same name as a parent,
        # so we need to catch that.  This kind of changes the subject structure, but in a way which
        # doesn't have any effect
        if name == parent: 
            parent = None
        lccmappings = subject.findall("lccMapping")
        for m in lccmappings:
            lccmap[m.text]["d"] = name
        smap[name] = {"p" : parent}

################################################################

################################################################
## Functions to migrate the journals
################################################################

def migrate_journals(source):
    # read in the content
    f = open(source)
    xml = etree.parse(f)
    f.close()
    journals = xml.getroot()
    print "migrating", str(len(journals)), "journal records"
    
    # registries for the various issns
    all_map = {}
    all_cluster = {}
    all_clusters = []
    pissn_counter = 0
    eissn_counter = 0

    # populate the registries - a map of issns to xml records
    # and a map of issns to next and previous issns
    for j in journals:
        issn = j.find("issn").text
        nissn = j.find("nextIssn").text
        pissn = j.find("previousIssn").text
        
        eissn = j.find("eissn").text
        neissn = j.find("nextEissn").text
        peissn = j.find("previousEissn").text
        
        if issn is not None:
            pissn_counter += 1
            all_map[issn] = j
            all_cluster[issn] = {"p" : pissn, "n" : nissn}
            if eissn is not None:
                all_cluster[issn]["s"] = eissn
        if eissn is not None:
            eissn_counter += 1
            all_map[eissn] = j
            all_cluster[eissn] = {"p" : peissn, "n" : neissn}
            if pissn is not None:
                all_cluster[eissn]["s"] = pissn
    
    print pissn_counter, "issns, and", eissn_counter, "e-issns (some may be duplicated, or in the wrong fields)"
    print len(all_map.keys()), "unique issn and pissn values in source dataset"
    
    # now do the clusters of issns - so we should wind up with a list of 
    # groups of issns that all represent the same journal
    checkbox = []
    for issn, rels in all_cluster.iteritems():
        if issn in checkbox:
            continue
        register = []
        _do_issn_cluster(issn, rels, register, all_cluster)
        all_clusters.append(register)
        checkbox += register
    
    print (len(all_clusters)), "groups of issns detected"
    print (len(checkbox)), "issns checked off"
    print (len(list(set(checkbox)))), "deduplicated checkbox"
    
    size = 0
    size_register = {}
    for cs in all_clusters:
        length = len(cs)
        if length in size_register:
            size_register[length] += 1
        else:
            size_register[length] = 1
        size += length
        
    print size, "total unduplicated issns in cluster map"
    print "counts of cluster sizes", size_register
    
    for cs in all_clusters:
        # work out which is the main record, and which are historic
        current, previous = _get_current_previous(cs, all_cluster)
        
        # make a journal object, and map the main and historic records to it
        j = Journal()
        element = all_map.get(current)
        if element is None:
            print "No entry for ", current
        cb = _to_journal_bibjson(element)
        issn_units = _get_other_issn_units(element)
        j.set_bibjson(cb)
        j.set_in_doaj(_is_in_doaj(element))
        for p in previous:
            j.add_history(_to_journal_bibjson(all_map.get(p)))
            issn_units += _get_other_issn_units(all_map.get(p))
        
        # pick over any old or next ISSNs which are asserted but which don't appear
        # in the overall dataset, and record them as stripped down historic records
        issn_units = list(set(issn_units))
        hbib = [h for d, r, irb, h in j.history()]
        for unit in issn_units:
            found = False
            if _issn_unit_in_bibjson(unit, cb):
                found = True
            for hb in hbib:
                if _issn_unit_in_bibjson(unit, hb):
                    found = True
            if not found:
                j.add_history(_issn_unit_to_bibjson(unit))
        
        j.set_created(_created_date(element))
        # save the result
        j.save() # FIXME: we may want to bulk this
        # print j.data

def _issn_unit_in_bibjson(unit, bibjson):
    pissn, eissn = unit
    thisp = bibjson.get_identifiers(bibjson.P_ISSN)
    thise = bibjson.get_identifiers(bibjson.E_ISSN)
    
    success = True
    if pissn is not None and pissn != thisp:
        success = False
    if eissn is not None and eissn != thise:
        success = False
    
    return success

def _issn_unit_to_bibjson(unit):
    pissn, eissn = unit
    if pissn is None and eissn is None:
        return
    b = JournalBibJSON()
    if pissn is not None:
        b.add_identifier(b.P_ISSN, pissn)
    if eissn is not None:
        b.add_identifier(b.E_ISSN, eissn)
    return b

def _get_other_issn_units(element):
    ppissn = element.find("previousIssn")
    npissn = element.find("nextIssn")
    peissn = element.find("previousEissn")
    neissn = element.find("nextEissn")
    
    pp = ppissn.text if ppissn is not None and ppissn.text is not None and ppissn.text != "" else None
    np = npissn.text if npissn is not None and npissn.text is not None and npissn.text != "" else None
    pe = peissn.text if peissn is not None and peissn.text is not None and peissn.text != "" else None
    ne = neissn.text if neissn is not None and neissn.text is not None and neissn.text != "" else None
    
    return [(pp, pe), (np, ne)]

def _do_issn_cluster(issn, rels, cluster_register, cluster_data):
    cluster_register.append(issn)
    prev = rels["p"]
    next = rels["n"]
    sibling = rels.get("s")
    if prev is not None and prev not in cluster_register:
        prevrels = cluster_data.get(prev)
        if prevrels is not None:
            _do_issn_cluster(prev, prevrels, cluster_register, cluster_data)
    if next is not None and next not in cluster_register:
        nextrels = cluster_data.get(next)
        if nextrels is not None:
            _do_issn_cluster(next, nextrels, cluster_register, cluster_data)
    if sibling is not None and sibling not in cluster_register:
        sibrels = cluster_data.get(sibling)
        if sibrels is not None:
            _do_issn_cluster(sibling, sibrels, cluster_register, cluster_data)

def _is_in_doaj(element):
    doaj = element.find("doaj")
    if doaj is not None:
        return doaj.text == "Y"
    return False

def _to_journal_bibjson(element):
    b = JournalBibJSON()
    
    title = element.find("title")
    if title is not None and title.text is not None and title.text != "":
        b.title = title.text
    
    alt = element.find("alternativeTitle")
    if alt is not None and alt.text is not None and alt.text != "":
        b.alternative_title = alt.text
    
    issn = element.find("issn")
    if issn is not None and issn.text is not None and issn.text != "":
        b.add_identifier(b.P_ISSN, issn.text)
    
    eissn = element.find("eissn")
    if eissn is not None and eissn.text is not None and issn.text != "":
        b.add_identifier(b.E_ISSN, eissn.text)
    
    keywords = element.find("keywords")
    if keywords is not None and keywords.text is not None and keywords.text != "":
        ks = [k.strip() for k in keywords.text.split(",")]
        b.set_keywords(ks)
    
    language = element.find("language")
    if language is not None and language.text is not None and language.text != "":
        languages = [l.strip() for l in language.text.split(",")]
        b.set_language(languages)
    
    chargingLink = element.find("chargingLink")
    if chargingLink is not None and chargingLink.text is not None and chargingLink != "":
        b.author_pays_url = chargingLink.text
    
    charging = element.find("charging")
    if charging is not None and charging.text is not None and charging.text != "":
        b.author_pays = charging.text
    
    country = element.find("country")
    if country is not None and country.text is not None and country.text != "":
        b.country = country.text
    
    license = element.find("license")
    if license is not None and license.text is not None and license.text != "":
        b.set_license(license.text, license.text)
    
    publisher = element.find("publisher")
    if publisher is not None and publisher.text is not None and publisher.text != "":
        b.publisher = publisher.text
    
    url = element.find("url")
    if url is not None and url.text is not None and url.text != "":
        b.add_url(url.text, "homepage")
    
    oa_start_year = element.find("startYear")
    oa_start_volume = element.find("startVolume")
    oa_start_issue = element.find("startIssue")
    if oa_start_year is not None:
        oa_start_year = oa_start_year.text
    if oa_start_volume is not None:
        oa_start_volume = oa_start_volume.text
    if oa_start_issue is not None:
        oa_start_issue = oa_start_issue.text
    b.set_oa_start(year=oa_start_year, volume=oa_start_volume, number=oa_start_issue)
    
    oa_end_year = element.find("endYear")
    oa_end_volume = element.find("endVolume")
    oa_end_issue = element.find("endIssue")
    if oa_end_year is not None:
        oa_end_year = oa_end_year.text
    if oa_end_volume is not None:
        oa_end_volume = oa_end_volume.text
    if oa_end_issue is not None:
        oa_end_issue = oa_end_issue.text
    b.set_oa_end(year=oa_end_year, volume=oa_end_volume, number=oa_end_issue)
    
    provider = element.find("provider")
    if provider is not None and provider.text is not None and provider.text != "":
        b.provider = provider.text
    
    active = element.find("active")
    if active is not None and active.text is not None and active.text != "":
        b.active = active.text == "Y"
    
    for_free = element.find("forFree")
    if for_free is not None and for_free.text is not None and for_free.text != "":
        b.for_free = for_free.text == "Y"
    
    subject_elements = element.findall("subject")
    for subject in subject_elements:
        if subject is not None and subject.text is not None and subject.text != "":
            subjects = _mine_subject(subject.text)
            for scheme, term in subjects:
                b.add_subject(scheme, term)
    
    return b

def _mine_subject(lcc_subject):
    # start a register of subjects and add this subject to it as the starting point
    register = []
    register.append(("LCC", lcc_subject))
    
    # recurse up the tree to get all of the parents of this subject in the LCC
    # classification
    _recurse_parents(lcc_subject, lccmap, register, "LCC")

    rels = lccmap.get(lcc_subject)
    doaj = rels.get("d")
    if doaj is not None:
        register.append(("DOAJ", doaj))
        _recurse_parents(doaj, smap, register, "DOAJ")
    
    return register

def _recurse_parents(subject, tree, register, scheme):
    rels = tree.get(subject)
    parent = rels.get("p")
    if parent is not None:
        register.append((scheme, parent))
        _recurse_parents(parent, tree, register, scheme)

def _get_current_previous(cluster, all_cluster):
    # trivial case of a single-element cluster
    if len(cluster) == 1:
        return cluster[0], []
    
    # else, workout which one is at the head of the chain
    current = None
    previous = []
    for c in cluster:
        rels = all_cluster.get(c)
        if rels.get("n") is None:
            current = c
        else:
            previous.append(c)
    # print current, previous, cluster
    return current, previous

#################################################################

#################################################################
## Functions to migrate suggestions
#################################################################

def migrate_suggestions(source):
    # read in the content
    f = open(source)
    xml = etree.parse(f)
    f.close()
    suggestions = xml.getroot()
    print "migrating", str(len(suggestions)), "suggestion records"

    for element in suggestions:
        s = Suggestion()
        
        # re-use the journal bibjson crosswalk
        cb = _to_journal_bibjson(element)
        s.set_bibjson(cb)
        
        # explicitly set the open-access-ness
        cb.set_open_access(_is_open_access(element))
        
        # suggestion info
        _to_suggestion(element, s)
        
        s.save()

def _is_open_access(element):
    oa = element.find("openAccess")
    if oa is not None:
        return oa.text == "Y"
    return False

def _to_suggestion(element, suggestion):
    
    desc = element.find("description")
    if desc is not None and desc.text is not None and desc.text != "":
        suggestion.set_description(desc.text)
    
    sn = element.find("userName")
    se = element.find("userEmail")
    if sn is not None and sn.text is not None and sn.text != "":
        sn = sn.text
    else:
        sn = None
    if se is not None and se.text is not None and se.text != "":
        se = se.text
    else:
        se = None
    if sn is not None or se is not None:
        suggestion.set_suggester(sn, se)
    
    status = element.find("status")
    if status is not None and status.text is not None and status.text != "":
        suggestion.set_application_status(status.text)
    
    note = element.find("note")
    if note is not None and note.text is not None and note.text != "":
        suggestion.add_note(note.text)
    
    oc = element.find("ownerComment")
    if oc is not None and oc.text is not None and oc.text != "":
        suggestion.add_correspondence(oc.text)
    
    note2 = element.find("note2")
    if note2 is not None and note2.text is not None and note2.text != "":
        suggestion.add_note(note2.text)
    
    ce = element.find("contactEmail")
    cn = element.find("contactName")
    if ce is not None and ce.text is not None and ce.text != "":
        ce = ce.text
    else:
        ce = None
    if cn is not None and cn.text is not None and cn.text != "":
        cn = cn.text
    else:
        cn = None
    if cn is not None or ce is not None:
        suggestion.add_contact(cn, ce)
    
    bo = element.find("byOwner")
    if bo is not None:
        suggestion.set_suggested_by_owner(bo.text == "1")
    
    so = element.find("addedOn")
    if so is not None and so.text is not None and so.text != "":
        suggestion.set_suggested_on(so.text)
    

#################################################################

#################################################################
## Functions to migrate articles
#################################################################

def migrate_articles(source):
    # read in the content
    f = open(source)
    xml = etree.parse(f)
    f.close()
    articles = xml.getroot()
    print "migrating", str(len(articles)), "article records from", source
    
    for element in articles:
        a = Article()
        b = _to_article_bibjson(element)
        a.set_bibjson(b)
        a.set_created(_created_date(element))
        a.save()

def _created_date(element):
    cd = element.find("addedOn")
    if cd is not None and cd.text is not None and cd.text != "":
        return cd.text
    return datetime.now().isoformat()

def _to_article_bibjson(element):
    b = ArticleBibJSON()
    
    title = element.find("title")
    if title is not None and title.text is not None and title.text != "":
        b.title = title.text
    
    doi = element.find("doi")
    if doi is not None and doi.text is not None and doi.text != "":
        b.add_identifier(b.DOI, doi.text)
    
    issn = element.find("issn")
    if issn is not None and issn.text is not None and issn.text != "":
        b.add_identifier(b.P_ISSN, issn.text)
    
    eissn = element.find("eissn")
    if eissn is not None and eissn.text is not None and eissn.text != "":
        b.add_identifier(b.E_ISSN, eissn.text)
    
    volume = element.find("volume")
    if volume is not None and volume.text is not None and volume.text != "":
        b.volume = volume.text
    
    issue = element.find("issue")
    if issue is not None and issue.text is not None and issue.text != "":
        b.number = issue.text
    
    year = element.find("year")
    if year is not None and year.text is not None and year.text != "":
        b.year = year.text
    
    month = element.find("month")
    if month is not None and month.text is not None and month.text != "":
        b.month = month.text
    
    pages = element.find("pages")
    if pages is not None and pages.text is not None and pages.text != "":
        bits = [bit.strip() for bit in pages.text.split("-")]
        if len(bits) > 0:
            b.start_page = bits[0]
        if len(bits) > 1:
            b.end_page = bits[1]
    
    ftxt = element.find("ftxt")
    if ftxt is not None and ftxt.text is not None and ftxt.text != "":
        b.add_url(ftxt.text, "fulltext")
    
    abstract = element.find("abstract")
    if abstract is not None and abstract.text is not None and abstract.text != "":
        b.abstract = abstract.text
    
    authors = element.find("authors")
    if authors is not None and authors.text is not None and authors.text != "":
        people = [p.strip() for p in authors.text.split("---")]
        for person in people:
            b.add_author(person)
    
    publisher = element.find("publisher")
    if publisher is not None and publisher.text is not None and publisher.text != "":
        b.publisher = publisher.text
    
    keywords = element.find("keywords")
    if keywords is not None and keywords.text is not None and keywords.text != "":
        words = [w.strip() for w in keywords.text.split("---")]
        b.set_keywords(words)
        
    return b

#################################################################

if __name__ == "__main__":
    load_subjects(SUBJECTS, LCC)
    # migrate_suggestions(SUGGESTIONS)
    migrate_journals(JOURNALS)
    #for a in ARTICLES:
    #    migrate_articles(a)

















