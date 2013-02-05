'''
This endpoint takes elasticsearch queries and returns the result object along with additional
"nodes" list and "links" list for use in force-directed network graphs
'''

import json

from flask import Blueprint, request, make_response

from portality.core import app
import portality.dao as dao


blueprint = Blueprint('graph', __name__)


# this is a JSON endpoint onto everything
@blueprint.route('/', methods=['GET','POST'])
def graph():
    e = get(
        ignoreisolated=request.values.get('ignoreisolated',False)
    )
    resp = make_response( json.dumps(e) )
    resp.mimetype = "application/json"
    return resp


# get everything from the database for display in a network graph
# pass in a typical elasticsearch query object
# list any object types to ignore in the ignore list, or set the ones to use in the only list
# if there are particular keys in a given object type that should be treated also as object types, use the 
# object type as a key in the promote object, pointing to a list of the keys to promote
# in the links object provide a list of the links between items that should be mapped, for each item type
# set ignoreisolated to true to remove items that have no links from the result set
def get(
        q={
            'query':{'match_all':{}},
            'size': 100000
        },
        ignore=[], 
        only=[], 
        promote={'record':['keywords','tags']}, 
        links={'wikipedia':['topic'],'reference':['_parents'],'record':['children']},
        ignoreisolated=False,
        datefrom=False,
        dateto=False
    ):

    # ensure that nothing set to be hidden via the settings gets exposed
    for item in app.config['NO_QUERY_VIA_API']:
        if item not in ignore: ignore.append(item)
        if item in only: only = [ x for x in only if x != item ]

    # get a list of search result objects, across all types rather than just one
    everything = dao.Everything.query(q=q)
    everything['nodes'] = []
    everything['links'] = []
    results = []
    for i in everything.get('hits',{}).get('hits',[]):
        obj = i['_source']
        obj['rtype'] = i['_type']
        results.append(obj)

    # a wee function to prep items for use here
    def prep(item):
        if 'rtype' not in item: item['rtype'] = 'record'
        if 'name' not in item:
            item['name'] = item.get('title',item.get('url',item['id']))
        #if 'budget' not in item:
        item['budget'] = 10
        if item['rtype'] == 'record': 
            item['budget'] = item['budget'] * (len(item.get('children',[])) + 2)
        return item
        
    # a wee function to look for links
    def linkify(item):
        linked = False
        if item['rtype'] in links.keys():
            linkon = links[item['rtype']]
            for l in linkon:
                ls = item.get(l,[])
                if not isinstance(ls,list): ls = [ls]
                for link in ls:
                    if link in notlinkedyet.keys():
                        print "hi"
                        everything['nodes'].append( notlinkedyet[link] )
                        del notlinkedyet[link]
                    obj = {"source":item['id'],"target":link, "rtype":item['rtype']+'_'+l}
                    inlist = False
                    for tng in everything['links']:
                        check1 = tng['source'] + '_' + tng['target']
                        check2 = tng['target'] + '_' + tng['source']
                        thisone = obj['source'] + '_' + obj['target']
                        if thisone == check1 or thisone == check2:
                            inlist = True
                    if not inlist:
                        everything['links'].append(obj)
                        linked = True
        return linked
        
    notlinkedyet = {}
    for item in results:
        item = prep(item) # tidy up the item

        if (item['rtype'] not in ignore and not only) or (item['rtype'] in only):
            # promote some keys of particular objects to being first class objects themselves
            if item['rtype'] in promote.keys():
                for key in promote[item['rtype']]:
                    if key in item:
                        probj = item[key]
                        if not isinstance(probj,list): probj = [probj]
                        for p in probj:
                            if isinstance(p,basestring): p = {'id':p}
                            p['rtype'] = item['rtype'] + '_' + key
                            if p['rtype'] not in links.keys(): links[p['rtype']] = ['_pparent']
                            p['_pparent'] = item['id']
                            results.append(p)
                                    
            # generate a links list between every object in every type to any other related object in any type
            linked = linkify(item)

            # add this item to the nodes list unless ignoring isolated and this one is isolated
            if not (ignoreisolated and not linked):
                everything['nodes'].append(item)
            else:
                notlinkedyet[item['id']] = item

    return everything


