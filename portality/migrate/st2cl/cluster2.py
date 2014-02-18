from lxml import etree
from copy import deepcopy
import csv

IN = "/home/richard/Dropbox/Documents/DOAJ/data/journals"
OUT = "/home/richard/tmp/doaj/equiv.csv"

def extract_issns(element):
    issn = j.find("issn").text
    nissn = j.find("nextIssn").text
    pissn = j.find("previousIssn").text
    
    eissn = j.find("eissn").text
    neissn = j.find("nextEissn").text
    peissn = j.find("previousEissn").text
    
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

f = open(IN)
xml = etree.parse(f)
f.close()
journals = xml.getroot()

journaltable = {}
idtable = {}
reltable = {}

# first job is to separate the journals and the issns, joined by a common id
# and to index each issn to the id in which it appears
id = 0
for j in journals:
    journaltable[id] = j
    idtable[id] = extract_issns(j)
    
    for issn in idtable[id]:
        if issn in reltable:
            reltable[issn].append(id)
        else:
            reltable[issn] = [id]
    
    id += 1

print len(journals), "journal records; ", len(idtable.keys()), "join identifiers; ", len(reltable.keys()), "unique issns"

count_register = {}
for id, issns in idtable.iteritems():
    size = len(issns)
    if size in count_register:
        count_register[size] += 1
    else:
        count_register[size] = 1

print "journal record to issn count statistics: ", count_register

mapregister = {}
for issn, ids in reltable.iteritems():
    size = len(ids)
    if size in mapregister:
        mapregister[size] += 1
    else:
        mapregister[size] = 1

print "issn to journal record count statistics: ", mapregister

def process(id, register):
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
        process(q, register)

equiv_table = {}
processed = []
i = 0
for id in idtable.keys():
    if id in processed:
        continue
    
    register = []
    process(id, register)
    processed += deepcopy(register)
    equiv_table[i] = deepcopy(register)
    i += 1

print len(processed), "join ids considered"

process_register = {}
for p in processed:
    if p in process_register:
        process_register[p] += 1
    else:
        process_register[p] = 1
multiples = [(k, v) for k, v in process_register.items() if v > 1]
print "join ids considered more than once:", multiples

if len(multiples) > 0:
    print "issns associated with join ids considered more than once:"
for k, v in multiples:
    issns = idtable.get(k)
    print k, "->", issns
    for issn in issns:
        print "    ", issn, "->", reltable.get(issn, [])
        for rel in reltable.get(issn, []):
            print "        ", rel, "->", idtable.get(rel)

print len(equiv_table.keys()), "equivalences identified"

equivregister = {}
idregister = {}
multiequiv = {}
counter = 0
for i, ids in equiv_table.iteritems():
    # count the size of the equivalences
    size = len(ids)
    if size in equivregister:
        equivregister[size] += 1
    else:
        equivregister[size] = 1
    
    # determine the count of ids in the equivalence table
    for jid in ids:
        if jid in idregister:
            idregister[jid] += 1
        else:
            idregister[jid] = 1
    
    # build a list of all those equivalences which have more than one journal record
    if size > 1:
        multiequiv[i] = ids
    
    counter += size
    
multiids = [(k, v) for k, v in idregister.items() if v > 1] 

print "equivalence register statistics: ", equivregister
print "join ids which appear in more than one equivalence", multiids
print counter, "total issns in equivalence table"

for k, v in multiequiv.iteritems():
    print k, "->", v
    for jid in v:
        print "    ", jid, "->", idtable.get(jid)

ordertables = {}
for e, jids in multiequiv.iteritems():
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

"""
print "equivalences and their ordered relations of join identifiers"
for e, o in ordertables.iteritems():
    print e, "->", o
"""

sorttable = {}
for e, ot in ordertables.iteritems():
    first = []
    last = []
    middle = []
    for k, r in ot.iteritems():
        if len(r.get("n")) == 0:
            first.append(k)
        elif len(r.get("p")) == 0:
            last.append(k)
        else:
            middle.append(k)
    sorttable[e] = first + middle + last

canontable = {}
for e, sort in sorttable.iteritems():
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

print "canonicalised, ordered equivalences and the relations they are derived from"
for k in ordertables.keys():
    print k, "->", ordertables.get(k)
    print "    ->", sorttable.get(k)
    print "    ->", canontable.get(k)


def get_issn_cell(jid):
    element = journaltable.get(jid)
    issn = element.find("issn").text
    eissn = element.find("eissn").text
    issns = []
    if issn is not None: issns.append(issn)
    if eissn is not None: issns.append(eissn)
    cell = ", ".join(issns)
    return cell

def get_title_cell(jid):
    element = journaltable.get(jid)
    title = element.find("title").text.encode("ascii", "ignore")
    return title

f = open(OUT, "wb")    
writer = csv.writer(f)
writer.writerow(["Equivalence Number", "Proposed Current Title", "Proposed Current ISSNs", "Proposed History: Title/ISSNs"])
for e, data in canontable.iteritems():
    canon, rest = data
    cells = [e]
    canon_issn_cell = get_issn_cell(canon)
    cells.append(get_title_cell(canon))
    cells.append(canon_issn_cell)
    for r in rest:
        r_issn_cell = get_issn_cell(r)
        cells.append(get_title_cell(r))
        cells.append(r_issn_cell)
    writer.writerow(cells)



























