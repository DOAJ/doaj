'''
This endpoint takes elasticsearch queries and returns the result object along with additional
"nodes" list and "links" list for use in force-directed network graphs
'''

import json, urllib2, requests

from flask import Blueprint, request, make_response

from portality.core import app
import portality.models as models
import portality.util as util


blueprint = Blueprint('graph', __name__)


# this is a JSON endpoint onto everything
@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def everything():
    if request.method == "POST":
        if request.json:
            qs = request.json
        else:
            qs = dict(request.form).keys()[-1]
    elif 'q' in request.values:
        qs = {'query': {'query_string': { 'query': request.values['q'] }}}
    elif 'source' in request.values:
        qs = json.loads(urllib2.unquote(request.values['source']))
    else: 
        qs = {'query':{'match_all':{}}}

    if 'graph' in qs:
        graphsettings = qs['graph']
        del qs['graph']
    else:
        graphsettings = {}

    e = get(
        q=qs,
        ignore=graphsettings.get('ignore',[]),
        only=graphsettings.get('only',[]),
        promote=graphsettings.get('promote',{}),
        links=graphsettings.get('links',{}),
        ignoreisolated=graphsettings.get('ignoreisolated',request.values.get('ignoreisolated',False)),
        dropfacets = graphsettings.get('dropfacets',request.values.get('dropfacets',False)),
        drophits = graphsettings.get('drophits',request.values.get('drophits',False)),
        dropnodes = graphsettings.get('dropnodes',request.values.get('dropnodes',False)),
        droplinks = graphsettings.get('droplinks',request.values.get('droplinks',False)),
        remote_source = graphsettings.get('remote_source',request.values.get('remote_source',False))
    )

    resp = make_response( json.dumps(e) )
    resp.mimetype = "application/json"
    return resp


# method to translate dot notation object location into a value if existend
# e.g. finds author.name in an object like {"author":[{"name":"me"}]}
# expects lists to have the same sorts of thing in them - e.g. if first thing in a list is a string, so should the rest be
def _findthis(dotnoted,obj):
    fkp = dotnoted.split('.')
    fkpl = len(fkp)
    matched = False
    x = 0
    while x < fkpl:
        if x == 0 and not matched: matched = obj
        if matched:
            if isinstance(matched,dict):
                matched = matched.get(fkp[x],False)
            elif isinstance(matched,list) and isinstance(matched[0],dict):
                matched = [j for j in [i.get(fkp[x],False) for i in matched] if j]
                if len(matched) and isinstance(matched[0],list): matched = [s for sublist in matched for s in sublist]
            elif x != fkpl-1:
                matched = False
        x += 1
    return matched


# look through a list of objects and find which one has the val (or one of list of vals) in the relevant key
# this is needed in case the key points to a list rather than just a string, in which case a list comprehension would do
# like pos = [i['id'] for i in everything['nodes']].index(item['id'])
# or in case of wanting a list of occurrences in a list of lists/tuples/objs:
# poses = [k for k,v in enumerate(everything['nodes']) if item['id'] in v.get('id',[])]
def _whichhasid(objlist,key,val):
    for k, v in enumerate(objlist):
        if isinstance(key,int):
            if key < len(v):
                vl = v[key]
            else:
                vl = []
        else:
            vl = v.get(key,[])
        if not isinstance(vl,list): vl = [vl]
        if not isinstance(val,list): val = [val]
        for vt in val:
            if vt in vl:
                return k
    return None


# get everything from the index for display in a network graph
# pass in a typical elasticsearch query object
# list any object types to ignore in the ignore list, or set the ones to use in the only list
# if there are particular keys in a given object type that should be treated also as object types, use the 
# object type as a key in the promote object, pointing to a list of the keys to promote
# in the links object provide a list of the links between items that should be mapped, for each item type
# set ignoreisolated to true to remove items that have no links from the result set
# dropfacets and drophits can be set to reduce the size of the return dataset
def get(
        q={
            'query':{'match_all':{}},
            'size': 100000
        },
        ignore=[], 
        only=[],
        #promote={'record':['keywords','tags']}, 
        #promote={'record':['citation']}, 
        #promote={'record':['citation','author','journal']},
        promote={},
        #links={'wikipedia':['topic'],'reference':['_parents'],'record':['children']},
        links={},
        identifiers=['identifier.id'],
        ignoreisolated=False,
        dropfacets=False,
        drophits=False,
        dropnodes=False,
        droplinks=False,
        remote_source=False
    ):

    # ensure that nothing set to be hidden via the settings gets exposed
    for item in app.config.get('NO_QUERY',[]):
        if item not in ignore: ignore.append(item)
        if item in only: only = [ x for x in only if x != item ]

    if remote_source:
        # get the result from remote index
        r = requests.post(remote_source,data=json.dumps(q))
        everything = r.json()
    else:
        # get a list of search result objects, across all types rather than just one, from local index via models
        everything = models.Everything.query(q=q)
    
    if not dropnodes:
        everything['nodes'] = []
        everything['links'] = []

        records = []
        for i in everything.get('hits',{}).get('hits',[]):
            o = i['_source']
            o['itype'] = i['_type']
            if 'id' not in o: o['id'] = o.get('_id','')
            if not isinstance(o['id'],list): o['id'] = [o['id']]
            for it in identifiers:
                hasone = _findthis(it,o)
                if hasone:
                    if not isinstance(hasone,list): hasone = [hasone]
                    for h in hasone:
                        if h not in o['id']: o['id'].append(h)
            records.append(o)

        # get any terms facets returned with the query and put them in the records list
        for key,fcts in everything.get('facets',{}).items():
            if 'terms' in fcts:
                terms = fcts['terms']
                for term in terms:
                    records.append({
                        "group": key,
                        "itype": key,
                        "id": [term['term']],
                        "className": term['term'],
                        "value": term["count"]
                    })

        for item in records:
            if 'className' not in item:
                item['className'] = item.get('title',item.get('url',item['id']))
            if 'value' not in item: item['value'] = 1
            if 'group' not in item: item['group'] = item['itype']

            if (item['itype'] not in ignore and not only) or (item['itype'] in only):
                # promote some keys of particular objects to being first class objects themselves
                if item['itype'] in promote.keys():
                    for key in promote[item['itype']]:
                        # TODO: need a check here for subpath keys like journal.name.exact
                        if key in item:
                            probj = item[key]
                            if not isinstance(probj,list): probj = [probj]
                            for p in probj:
                                if isinstance(p,basestring): p = {'id':[p]}
                                p['className'] = p['id'][0]
                                p['itype'] = item['itype'] + '_' + key
                                if p['itype'] not in links.keys(): links[p['itype']] = []
                                links[p['itype']].append('_pparent')
                                p['_pparent'] = item['id'][0]
                                records.append(p)

                
                # TODO: need to add sameas / join functionality, so things that are the same on different fields can be matched
                # for example citation.identifier.id.exact would match identifier.id.exact between citations and records
                # also what if an item has two citation identifiers? should really be one object

                
                # make a simple version of the item for use on the graphic (does not need full data after processing)
                simpleitem = {
                    "className":item["className"],
                    "itype":item["itype"],
                    "id":item["id"],
                    "value":item["value"],
                    "group":item["group"]
                }
                if simpleitem['className'] is None: simpleitem['className'] = ','.join(simpleitem['id'])
                                        
                if not droplinks:
                    # check any item properties for links to generated facets
                    for facetkey in everything.get('facets',{}).keys():
                        mitem = _findthis(facetkey.replace(app.config['FACET_FIELD'],''),item)
                        if mitem:
                            if not isinstance(mitem,list): mitem = [mitem]
                            for link in mitem:
                                source = _whichhasid(everything['nodes'],'id',item['id'])
                                target = _whichhasid(everything['nodes'],'id',link)
                                if target is None:
                                    try:
                                        #everything['nodes'].append(records[[i['id'] for i in records].index(link)])
                                        everything['nodes'].append(records[_whichhasid(records,'id',link)])
                                        target = len(everything['nodes'])-1
                                    except:
                                        everything['nodes'].append({'id':[link],'value':1,'className':link,'group':facetkey,'itype':facetkey})
                                        target = len(everything['nodes'])-1
                                        # NOTE this adds all found values in the records, not just those in the top facet list
                                        # to make only those found in the facet count shown, set target=None and do not append to nodes 
                                        # should perhaps also then have to remove any appended source above
                                        #target=None
                                if source is None and target is not None:
                                    everything['nodes'].append(simpleitem)
                                    source = len(everything['nodes'])-1

                                if source is not None and target is not None:
                                    obj = {"source":source,"target":target, "itype":item['itype']+'_'+link}
                                    everything['links'].append(obj)

                    # generate a links list between every object in every type to any other related object in any type
                    if item['itype'] in links.keys():
                        linkon = links[item['itype']]
                        for l in linkon:
                            ls = item.get(l,[])
                            if not isinstance(ls,list): ls = [ls]
                            for link in ls:
                                try:
                                    source = [i['id'] for i in everything['nodes']].index(item['id'])
                                except:
                                    everything['nodes'].append(simpleitem)
                                    source = len(everything['nodes'])-1
                                try:
                                    target = [i['id'] for i in everything['nodes']].index(link)
                                except:
                                    try:
                                        everything['nodes'].append(records[[i['id'] for i in records].index(link)])
                                    except:
                                        everything['nodes'].append({'id':[link],'value':1,'className':link})
                                    target = len(everything['nodes'])-1
                                obj = {"source":source,"target":target, "itype":item['itype']+'_'+l}
                                everything['links'].append(obj)

                if _whichhasid(everything["nodes"],'id',item['id']) is None and not ignoreisolated:
                    everything['nodes'].append(simpleitem)
                '''loc = _whichhasid(everything["nodes"],'id',item['id'])
                if loc is not None:
                    if isinstance(simpleitem['id'],list) and len(simpleitem['id']) > 1:
                        o = everything['nodes'][loc]['className']
                        for i in simpleitem['id']:
                            if i != o: o += ', ' + i
                elif not ignoreisolated:
                    everything['nodes'].append(simpleitem)'''

    if dropfacets and 'facets' in everything: del everything['facets']
    if drophits and 'hits' in everything and 'hits' in everything['hits']: del everything['hits']['hits']
    return everything








'''
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
    everything = models.Everything.query(q=q)
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
'''

