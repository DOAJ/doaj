import os, sys, codecs, random, string
from lxml import etree
from datetime import datetime
from copy import deepcopy
from portality.models import Journal, JournalBibJSON, Suggestion, Article, ArticleBibJSON, Account

################################################################
## Preliminary data loading functions
################################################################

smap = {}
lccmap = {}
issnmap = {}

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
        code = subject.find("code")
        if parent is not None:
            parent = parent.text
        if code is not None:
            code = code.text
        lccmap[name] = {"p" : parent, "c" : code}
    
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

def load_issn_journal_map():
    # we need to go over every journal in the index
    for j in Journal.iterall():
        obj = {}
        jbib = j.bibjson()
        
        # store only the data we want for the article migration
        obj["subjects"] = jbib.subjects()
        obj["title"] = jbib.title
        obj["license"] = jbib.get_license()
        obj["language"] = jbib.language
        obj["country"] = jbib.country
        obj["in_doaj"] = j.is_in_doaj()
        
        # get the issns that map to this journal (or any previous version of it)
        issns = j.data.get("index", {}).get("issn", [])
        
        # register pointers to the object for each issn
        for issn in issns:
            issnmap[issn] = obj

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
    print("migrating", str(len(journals)), "journal records")
    
    clusters = _get_journal_clusters(journals)
    
    # make a journal object, and map the main and historic records to it
    for canon, rest in clusters:
        j = Journal()
        
        cb = _to_journal_bibjson(canon)
        j.set_bibjson(cb)
        
        j.set_in_doaj(_is_in_doaj(canon))
        j.set_created(_created_date(canon))
        
        for p in rest:
            replaces = _get_replaces(p)
            isreplacedby = _get_isreplacedby(p)
            j.add_history(_to_journal_bibjson(p), replaces=replaces, isreplacedby=isreplacedby)
            
        j.save()
    
def _normalise_issn(issn):
    issn = issn.upper()
    if len(issn) > 8: return issn
    if len(issn) == 8:
        if "-" in issn: return "0" + issn
        else: return issn[:4] + "-" + issn[4:]
    if len(issn) < 8:
        if "-" in issn: return ("0" * (9 - len(issn))) + issn
        else:
            issn = ("0" * (8 - len(issn))) + issn
            return issn[:4] + "-" + issn[4:]

def _get_replaces(element):
    pissn = element.find("previousIssn").text
    peissn = element.find("previousEissn").text
    replaces = []
    if pissn is not None:
        replaces.append(_normalise_issn(pissn))
    if peissn is not None:
        replaces.append(_normalise_issn(peissn))
    return replaces

def _get_isreplacedby(element):
    nissn = element.find("nextIssn").text
    neissn = element.find("nextEissn").text
    irb = []
    if nissn is not None:
        irb.append(_normalise_issn(nissn))
    if neissn is not None:
        irb.append(_normalise_issn(neissn))
    return irb

def _extract_issns(element):
    issn = element.find("issn").text
    nissn = element.find("nextIssn").text
    pissn = element.find("previousIssn").text
    
    eissn = element.find("eissn").text
    neissn = element.find("nextEissn").text
    peissn = element.find("previousEissn").text
    
    issns = []
    if issn is not None:
        issns.append(issn)
    if nissn is not None:
        issns.append(nissn)
    if pissn is not None:
        issns.append(pissn)
    if eissn is not None:
        issns.append(eissn)
    if neissn is not None:
        issns.append(neissn)
    if peissn is not None:
        issns.append(peissn)
    
    return issns

def _process_journal_id(id, register, idtable, reltable):
    if id in register:
        return
    register.append(id)
    queue = []
    issns = idtable.get(id, [])
    for issn in issns:
        ids = reltable.get(issn, [])
        for i in ids:
            if i in register: continue
            if i not in queue: queue.append(i)
    for q in queue:
        _process_journal_id(q, register, idtable, reltable)

def _get_journal_clusters(journals):
    journaltable = {}
    idtable = {}
    reltable = {}

    # first job is to separate the journals and the issns, joined by a common id
    # and to index each issn to the id in which it appears
    id = 0
    for j in journals:
        journaltable[id] = j
        idtable[id] = _extract_issns(j)
        for issn in idtable[id]:
            if issn in reltable:
                reltable[issn].append(id)
            else:
                reltable[issn] = [id]
        id += 1
    
    print(len(journals), "journal records; ", len(idtable.keys()), "join identifiers; ", len(reltable.keys()), "unique issns")
    
    # now calculate the equivalence table.  This groups all of the journals
    # which share issns of any kind into a single batch
    equiv_table = {}
    processed = []
    i = 0
    for id in idtable.keys():
        if id in processed:
            continue
        
        register = []
        _process_journal_id(id, register, idtable, reltable)
        processed += deepcopy(register)
        equiv_table[i] = deepcopy(register)
        i += 1
    
    # Next go through each equivalence, and build a table of the next/previous
    # links in each of the journals
    ordertables = {}
    for e, jids in equiv_table.items():
        ordertable = {}
        for jid in jids:
            ordertable[jid] = {"n" : [], "p": []}
            element = journaltable.get(jid)
            ne = element.find("nextEissn").text
            np = element.find("nextIssn").text
            pe = element.find("previousEissn").text
            pp = element.find("previousIssn").text
            if ne is not None: ne = ne.upper()
            if np is not None: np = np.upper()
            if pe is not None: pe = pe.upper()
            if pp is not None: pp = pp.upper()
            for jid2 in jids:
                if jid2 == jid: continue
                e2 = journaltable.get(jid2)
                eissn = e2.find("issn").text
                pissn = e2.find("eissn").text
                if eissn is not None: eissn = eissn.upper()
                if pissn is not None: pissn = pissn.upper()
                if (ne is not None and ne in [pissn, eissn]) or (np is not None and np in [pissn, eissn]):
                    ordertable[jid]["n"].append(jid2)
                if (pe is not None and pe in [pissn, eissn]) or (pp is not None and pp in [pissn, eissn]):
                    ordertable[jid]["p"].append(jid2)
        ordertables[e] = ordertable
    
    # Now analyse the previous/next status of each cluster, and organise
    # them in an array in descending order (head of the chain first)
    sorttable = {}
    for e, ot in ordertables.items():
        first = []
        last = []
        middle = []
        for k, r in ot.items():
            if len(r.get("n")) == 0:
                first.append(k)
            elif len(r.get("p")) == 0:
                last.append(k)
            else:
                middle.append(k)
        sorttable[e] = first + middle + last
    
    # finally (for the clustering algorithm), select the canonical record
    # and the older historical records
    canontable = {}
    for e, sort in sorttable.items():
        canon = None
        i = 0
        found = False
        for s in sort:
            element = journaltable.get(s)
            doaj = element.find("doaj").text
            if doaj is not None and doaj.upper() == "Y":
                canon = s
                found = True
                break
            i += 1
        if not found:
            i = 0
            canon = sort[0]
        rest = deepcopy(sort)
        del rest[i]
        canontable[e] = (canon, rest)
    
    # now, in preparation for returning to the caller, substitute everything in the canon table
    # for the xml elements they represent
    clusters = []
    for e, data in canontable.items():
        canon, rest = data
        celement = journaltable.get(canon)
        relements = [journaltable.get(r) for r in rest]
        clusters.append((celement, relements))
    
    return clusters

def _is_in_doaj(element):
    # an item is in the DOAJ if the following things hold true:
    # - doaj = True
    # - active = True
    # - for_free = True
    
    # lift the elements
    doaj = element.find("doaj")
    active = element.find("active")
    for_free = element.find("forFree")
    
    # work out whether each is True or False
    d = doaj is not None and doaj.text == "Y"
    a = active is not None and active.text == "Y"
    f = for_free is not None and for_free.text == "Y"
    
    # all 3 have to be true for the element to be in DOAJ
    return d and a and f

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
    
    subject_elements = element.findall("subject")
    for subject in subject_elements:
        if subject is not None and subject.text is not None and subject.text != "":
            subjects = _mine_subject(subject.text)
            for scheme, term, code in subjects:
                b.add_subject(scheme, term, code=code)
    
    return b

def _mine_subject(lcc_subject):
    # start a register of subjects and add this subject to it as the starting point
    register = []
    
    # get the LCC classification and its code
    s = lccmap.get(lcc_subject)
    register.append(("LCC", lcc_subject, s.get("c")))
    
    # recurse up the tree to get all of the parents of this subject in the LCC
    # classification
    _recurse_parents(lcc_subject, lccmap, register, "LCC")

    rels = lccmap.get(lcc_subject)
    doaj = rels.get("d")
    if doaj is not None:
        register.append(("DOAJ", doaj, None)) # DOAJ does not have codes
        _recurse_parents(doaj, smap, register, "DOAJ")
    
    return register

def _recurse_parents(subject, tree, register, scheme):
    rels = tree.get(subject)
    parent = rels.get("p")
    if parent is not None:
        s = tree.get(parent)
        register.append((scheme, parent, s.get("c")))
        _recurse_parents(parent, tree, register, scheme)

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
    print("migrating", str(len(suggestions)), "suggestion records")

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
        suggestion.description = desc.text
    
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
        suggestion.suggested_by_owner = bo.text == "1"
    
    so = element.find("addedOn")
    if so is not None and so.text is not None and so.text != "":
        suggestion.suggested_on = so.text
    

#################################################################

#################################################################
## Functions to migrate articles
#################################################################

def migrate_articles(source, batch_size=5000):
    # read in the content
    f = open(source)
    xml = etree.parse(f)
    f.close()
    articles = xml.getroot()
    print("migrating", str(len(articles)), "article records from", source)
    
    counter = 0
    omissions = 0
    batch = []
    for element in articles:
        a = Article()
        b = _to_article_bibjson(element)
        a.set_bibjson(b)
        hasjournal = _add_journal_info(a)
        
        if not hasjournal:
            print("INFO: omitting article")
            omissions += 1
            continue
        
        a.set_created(_created_date(element))
        a.set_id()
        a.prep() # prepare the thing to be saved, which is necessary since we're not actually going to save()
        batch.append(a.data)
        
        if len(batch) >= batch_size:
            counter += len(batch)
            print("Writing batch, size", len(batch))
            Article.bulk(batch, refresh=True)
            print("batch written, total so far", counter)
            del batch[:]
    
    if len(batch) > 0:
        counter += len(batch)
        print("Writing final batch, size", len(batch))
        Article.bulk(batch, refresh=True)
        print("batch written, total written", counter)
    
    print("wrote", counter, "articles, omitted", omissions)

def _created_date(element):
    cd = element.find("addedOn")
    if cd is not None and cd.text is not None and cd.text != "":
        fudge = "T".join(cd.text.split(" ")) + "Z" # fudge the date format
        # check that it parses
        try:
            datetime.strptime(fudge, "%Y-%m-%dT%H:%M:%SZ")
            return fudge
        except:
            # do nothing, we'll just fall back to "created now"
            print("failed on", cd.text)
            pass
        
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

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
        people = [p.strip() for p in authors.text.split("---") if p.strip() != ""]
        for person in people:
            b.add_author(person)
    
    publisher = element.find("publisher")
    if publisher is not None and publisher.text is not None and publisher.text != "":
        b.publisher = publisher.text
    
    keywords = element.find("keywords")
    if keywords is not None and keywords.text is not None and keywords.text != "":
        # this filters the string "keyword" and "keywords" at the same time
        words = [w.strip() for w in keywords.text.split("---") if w.strip().lower() not in ["keyword", "keywords", "no keywords", "</keyword><keyword>"]]
        b.set_keywords(words)
    
    return b

def _add_journal_info(article):
    bibjson = article.bibjson()
    
    # first, get the ISSNs associated with the record
    pissns = bibjson.get_identifiers(bibjson.P_ISSN)
    eissns = bibjson.get_identifiers(bibjson.E_ISSN)
    
    # find a matching journal record either from the registry cache
    # or directly from the index
    journal = None
    
    # first check the registry
    for issn in pissns:
        if issn in issnmap:
            journal = issnmap.get(issn)
    
    if journal is None:
        for issn in eissns:
            if issn in issnmap:
                journal = issnmap.get(issn)
    
    if journal is None:
        print("WARN: no journal for ", pissns, eissns)
        return False
    
    # if we get to here, we have a journal record we want to pull data from
    for s in journal.get("subjects", []):
        bibjson.add_subject(s.get("scheme"), s.get("term"), code=s.get("code"))
    
    if journal.get("title") is not None:
        bibjson.journal_title = journal.get("title")
    
    if journal.get("license") is not None:
        lic = journal.get("license")
        bibjson.set_journal_license(lic.get("title"), lic.get("type"), lic.get("url"), lic.get("version"), lic.get("open_access"))
    
    if journal.get("language") is not None:
        bibjson.journal_language = journal.get("language")
    
    if journal.get("country") is not None:
        bibjson.journal_country = journal.get("country")
    
    article.set_in_doaj(journal.get("in_doaj", False))
    return True

#################################################################

#################################################################
# Functions to migrate contacts
#################################################################

def migrate_contacts(source, batch_size=1000):
    # read in the content
    f = open(source)
    xml = etree.parse(f)
    f.close()
    contacts = xml.getroot()
    print("migrating", str(len(contacts)), "contact records from", source)
    
    # first thing to do is locate all the duplicates in the logins
    record = []
    duplicates = []
    for element in contacts:
        login = element.find("login")
        if login is not None and login.text is not None and login.text != "":
            if login.text in record:
                duplicates.append(login.text)
            record.append(login.text)
    
    # now go through and load all the user accounts
    batch = []
    for element in contacts:
        login = element.find("login")
        password = element.find("password")
        name = element.find("name")
        email = element.find("email")
        issns = element.findall("issn")
        
        if login is None or login.text is None or login.text == "":
            print("ERROR: contact without login - providing login")
            if len(issns) == 0:
                # make a random 8 character login name
                login = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(8))
            else:
                # select the first issn
                login = issns[0].text
        else:
            login = login.text
        
        if password is None or password.text is None or password.text == "":
            print("ERROR: contact without password", login, "- providing one")
            # make a random 8 character password
            password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(8))
        else:
            password = password.text
        
        # check to see if this is a duplicate
        if login in duplicates:
            if len(issns) == 0:
                print("INFO: duplicate detected, has no ISSNs, so skipping", login)
                continue
            else:
                print("INFO: duplicate detected, with ISSNs, so keeping", login)
                
        a = Account()
        a.set_id(login)
        a.set_password(password)
        
        if name is not None and name.text is not None and name.text != "":
            a.set_name(name.text)
        
        if email is not None and email.text is not None and email.text != "":
            a.set_email(email.text)
        
        for issn in issns:
            if issn is not None and issn.text is not None and issn.text != "":
                jid = _get_journal_id_from_issn(issn.text)
                a.add_journal(jid)
        
        a.prep() # prep for saving, since we're not actually going to call save()
        batch.append(a.data)
        
        if len(batch) >= batch_size:
            Account.bulk(batch, refresh=True)
            del batch[:]
    
    if len(batch) > 0:
        Account.bulk(batch)
        

def _get_journal_id_from_issn(issn):
    issn = _normalise_issn(issn)
    journals = Journal.find_by_issn(issn)
    if len(journals) > 1:
        print("WARN: issn", issn, "maps to multiple journals:", ", ".join([j.id for j in journals]))
    if len(journals) == 0:
        print("WARN: issn", issn, "does not map to any journals")
    if len(journals) > 0:
        return journals[0].id

#################################################################

if __name__ == "__main__":
    # get the data in directory
    IN_DIR = None
    if len(sys.argv) > 1:
        IN_DIR = sys.argv[1]
    else:
        print("you must specify a data directory to migrate from")
        exit()

    JOURNALS = os.path.join(IN_DIR, "journals")
    SUBJECTS = os.path.join(IN_DIR, "subjects")
    LCC = os.path.join(IN_DIR, "lccSubjects")
    SUGGESTIONS = os.path.join(IN_DIR, "suggestions")
    ARTICLES = [os.path.join(IN_DIR, f) for f in os.listdir(IN_DIR) if f.startswith("articles") and f != "articles.xsd" and not f.endswith(".errors")]
    CONTACTS = os.path.join(IN_DIR, "contacts")

    # load the subjects and then migrate suggestions and journals
    load_subjects(SUBJECTS, LCC)
    migrate_suggestions(SUGGESTIONS)
    migrate_journals(JOURNALS)
    
    # contacts have to come after journals, as they will search for matches
    migrate_contacts(CONTACTS)
    
    # load a map of issns to journals, which is used in article migration
    load_issn_journal_map()
    for a in ARTICLES:
        migrate_articles(a)
