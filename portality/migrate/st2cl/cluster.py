# Script which mines the journal metadata and groups records which pertain to the same Journal throughout
# time and across ISSN changes

############################################
# DO NOT USE AS-IS
############################################
# This is just a bunch of lines of code to help with exploring the data, it is not an executable
# script in its current form.


from lxml import etree

IN = "/home/richard/Dropbox/Documents/DOAJ/data/journals"
OUT = "/home/richard/tmp/doaj/clusters.xml"

f = open(IN)
xml = etree.parse(f)
f.close()
journals = xml.getroot()

all_map = {}
issn_map = {}
eissn_map = {}

all_cluster = {}
issn_cluster = {}
eissn_cluster = {}

# first, read all the useful information into memory
for j in journals:
    issn = j.find("issn").text
    nissn = j.find("nextIssn").text
    pissn = j.find("previousIssn").text
    
    eissn = j.find("eissn").text
    neissn = j.find("nextEissn").text
    peissn = j.find("previousEissn").text
    
    if issn is not None:
        issn_map[issn] = j
        all_map[issn] = j
        issn_cluster[issn] = {"p" : pissn, "n" : nissn}
        all_cluster[issn] = {"p" : pissn, "n" : nissn}
    if eissn is not None:
        eissn_map[eissn] = j
        all_map[issn] = j
        eissn_cluster[eissn] = {"p" : peissn, "n" : neissn}
        all_cluster[eissn] = {"p" : peissn, "n" : neissn}

# now build lists of all the issns that are linked together

def do_issn_cluster(issn, rels, cluster_register, success_register, cluster_data):
    cluster_register.append(issn)
    prev = rels["p"]
    next = rels["n"]
    if prev is not None and prev not in cluster_register:
        prevrels = cluster_data.get(prev)
        if prevrels is None:
            success_register["prevfail"].append(prev)
        else:
            success_register["prevfound"].append(prev)
            do_issn_cluster(prev, prevrels, cluster_register, success_register, cluster_data)
    if next is not None and next not in cluster_register:
        nextrels = cluster_data.get(next)
        if nextrels is None:
            success_register["nextfail"].append(next)
        else:
            success_register["nextfound"].append(next)
            do_issn_cluster(next, nextrels, cluster_register, success_register, cluster_data)

issn_clusters = []
issn_success_register = {"prevfound" : [], "prevfail" : [], "nextfound" : [], "nextfail" : []}
for issn, rels in issn_cluster.iteritems():
    register = []
    do_issn_cluster(issn, rels, register, issn_success_register, issn_cluster)
    issn_clusters.append(register)

eissn_clusters = []
eissn_success_register = {"prevfound" : [], "prevfail" : [], "nextfound" : [], "nextfail" : []}
for issn, rels in eissn_cluster.iteritems():
    register = []
    do_issn_cluster(issn, rels, register, eissn_success_register, eissn_cluster)
    eissn_clusters.append(register)

all_clusters = []
all_success_register = {"prevfound" : [], "prevfail" : [], "nextfound" : [], "nextfail" : []}
for issn, rels in all_cluster.iteritems():
    register = []
    do_issn_cluster(issn, rels, register, all_success_register, all_cluster)
    all_clusters.append(register)
    
    
# now we have a list of groups of issns which are all the same journal, let's find all of those
# which have more than one record
nonunity = []
for cs in all_clusters:
    if len(cs) > 1:
        nonunity.append(cs)

resolved = []
for cs in nonunity:
    resolution = []
    for c in cs:
        resolution.append(all_map.get(c))
    resolved.append(resolution)

out = open(OUT, "wb")
for rs in resolved:
    for r in rs:
        s = etree.tostring(r, pretty_print=True)
        out.write(s)
        out.write("\n")
    out.write("\n\n==================================\n\n")
out.close()

"""
multis = etree.Element("multis")
for cs in all_clusters:
    if len(cs) > 1:
        element = etree.SubElement(multis, "cluster")
        for c in cs:
            element.append(all_map.get(c))
"""





