from lxml import etree
import os, json
from portality import models

source = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lccSubjects.xml")

doc = etree.parse(open(source))
root = doc.getroot()

nodes = {}
tree = {"name" : "LCC", "children" : []}
cpmap = {}

for element in root.findall("subject"):
    nel = element.find("name")
    cel = element.find("code")
    pel = element.find("parent")
    
    if nel is None:
        continue
        
    name = nel.text
    code = None
    parent = None
    if cel is not None:
        code = cel.text
    if pel is not None:
        parent = pel.text
    
    node = {"name" : name}
    if code is not None:
        node["code"] = code
    
    nodes[name] = node
    
    if parent is None:
        tree["children"].append(node)
    else:
        cpmap[name] = parent

for child, parent in cpmap.items():
    cn = nodes.get(child)
    pn = nodes.get(parent)
    if cn is None or pn is None:
        continue
    if "children" not in pn:
        pn["children"] = []
    pn["children"].append(cn)

lcc = models.LCC(**tree)
lcc.save()
