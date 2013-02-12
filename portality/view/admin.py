import json
from copy import deepcopy

from flask import Blueprint, request, flash, abort, make_response, render_template
from flask.ext.login import current_user

from portality.core import app
import portality.models as models


blueprint = Blueprint('admin', __name__)


# restrict everything in admin to logged in users
@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        abort(401)

'''
projected "we expect this cost to arise during the course of the project"},
ordered "we have received a purchase order requesting us to deliver goods or services at an agreed price"},
invoiced "we have received an invoice for goods or services delivered to us, which we should pay when project funds are available"},
claimed": "an expense claimed with documentary evidence by a team member"},
reminded": "we have not been paid for an invoice we sent, so we have sent a reminder"},
paid "the money to pay this cost has left our bank account"}
'''
            
# define the dropdowns to be used in the admin pages
def dropdowns():
    dropdowns = {
        "vat": ['UK','EU','Other'],
        "projects": [i['_source']['id'] for i in dao.Project.query(q="*",size=1000000).get('hits',{}).get('hits',[])],
        "internals": [i['_source']['id'] for i in dao.Project.query(terms={"internal":"yes"},size=1000000).get('hits',{}).get('hits',[])],
        "clpeople": [str(i['_source']['id']) for i in dao.Account.query(q="*",size=1000000).get('hits',{}).get('hits',[])],
        "partners": [i['_source']['id'] for i in dao.Account.query(terms={"partner":"yes"},size=1000000).get('hits',{}).get('hits',[])],
        "seniors": [i['_source']['id'] for i in dao.Account.query(terms={"senior":"yes"},size=1000000).get('hits',{}).get('hits',[])],
        "contacts": [(i['_source']['id'],i['_source']['name'],i['_source']['companyname']) for i in dao.Contact.query(q="*",size=1000000).get('hits',{}).get('hits',[])],
        "billables": [(i['_source']['id'],i['_source']['name'],i['_source']['companyname']) for i in dao.Contact.query(terms={"billable":"yes"},size=1000000).get('hits',{}).get('hits',[])],
        "contractors": [(i['_source']['id'],i['_source']['name'],i['_source']['companyname']) for i in dao.Contractor.query(q="*",size=1000000).get('hits',{}).get('hits',[])]
    }
    return dropdowns
    

# this returns an object with basically everything in it, plus some extras, but can be query filtered
# it also provides a list of all the links between the objects, cos this is for the vis
def geteverything(q=False,person=False,project=False,contact=False,contractor=False,ignore=[],ignoreisolated=False,datefrom=False,dateto=False):

    qryobj = {'query':{'match_all':{}}}

    everything = {
        "nodes": [],
        "links": []
    }


    if 'contacts' not in ignore:
        if contact or q:
            qryobj = {'query':{'bool':{'must':[]}}}
        if contact: qryobj['query']['bool']['must'].append({'term':{'id': contact}})
        if q: qryobj['query']['bool']['must'].append({'query_string':{'query':'*' + q.lstrip('*').rstrip('*') + '*'}})
        contacts = [i['_source'] for i in dao.Contact.query(q=qryobj,size=10000).get('hits',{}).get('hits',[])]
        qryobj = {'query':{'match_all':{}}}
        for item in contacts:
            item['id'] = item['name']
            if item['companyname']:
                item['id'] += '_' + item['companyname']
            item['id'] = item['id'].replace(' ','_').lower()
            item["rtype"] = "contacts"
            item['budget'] = 1000
            everything["nodes"].append(item)

    if 'contractors' not in ignore:
        if contractor or q:
            qryobj = {'query':{'bool':{'must':[]}}}
        if contractor: qryobj['query']['bool']['must'].append({'term':{'id': contractor}})
        if q: qryobj['query']['bool']['must'].append({'query_string':{'query':'*' + q.lstrip('*').rstrip('*') + '*'}})
        contractors = [i['_source'] for i in dao.Contractor.query(q=qryobj,size=10000).get('hits',{}).get('hits',[])]
        qryobj = {'query':{'match_all':{}}}
        for item in contractors:
            item['id'] = item['name']
            if item['companyname']:
                item['id'] += '_' + item['companyname']
            item['id'] = item['id'].replace(' ','_').lower()
            item["rtype"] = "contractors"
            item['budget'] = 1000
            everything["nodes"].append(item)

    if 'people' not in ignore:
        if person or q:
            qryobj = {'query':{'bool':{'must':[]}}}
        if person: qryobj['query']['bool']['must'].append({'term':{'id': person}})
        if q: qryobj['query']['bool']['must'].append({'query_string':{'query':'*' + q.lstrip('*').rstrip('*') + '*'}})
        people = [i['_source'] for i in dao.Account.query(q=qryobj,size=10000).get('hits',{}).get('hits',[])]
        qryobj = {'query':{'match_all':{}}}
        for item in people:
            item["name"] = item["id"]
            item["rtype"] = "people"
            item['budget'] = 1000
            everything["nodes"].append(item)

    projqryobj = deepcopy(qryobj)
    commqryobj = deepcopy(qryobj)
    finqryobj = deepcopy(qryobj)

    if project:
        projqryobj = {'query':{'bool':{'must':[{'term':{'id': project}}]}}}
        commqryobj = {'query':{'bool':{'must':[{'term':{'project': project}}]}}}
        finqryobj = {'query':{'bool':{'must':[{'term':{'project': project}}]}}}
    if person:
        if 'bool' not in commqryobj['query']: commqryobj = {'query':{'bool':{'must':[]}}}
        commqryobj['query']['bool']['must'].append({'term':{'name': person}})
        if 'bool' not in finqryobj['query']: finqryobj = {'query':{'bool':{'must':[]}}}
        finqryobj['query']['bool']['must'].append({'term':{'recipient': person}})
        if 'bool' not in projqryobj['query']: projqryobj = {'query':{'bool':{}}}
        projqryobj['query']['bool']['should'] = [
            {'term':{'seniorplusone': person}},
            {'term':{'plusone': person}},
            {'term':{'proposer': person}},
            {'term':{'lead': person}},
            {'term':{'qc': person}},
        ]

    # if provided a minimum date from, then only return objects that are still running after that date
    # e.g. objects whose end date (dateto) is after the provided datefrom
    # or objects that have only one date stamp, and that is after the datefrom
    if datefrom or dateto or q:
        if 'bool' not in projqryobj['query']: projqryobj = {'query':{'bool':{}}}
        if 'must' not in projqryobj['query']['bool']: projqryobj['query']['bool']['must'] = []
        if 'bool' not in commqryobj['query']: commqryobj = {'query':{'bool':{}}}
        if 'must' not in commqryobj['query']['bool']: commqryobj['query']['bool']['must'] = []
        if 'bool' not in finqryobj['query']: finqryobj = {'query':{'bool':{}}}
        if 'must' not in finqryobj['query']['bool']: finqryobj['query']['bool']['must'] = []

    if q:
        qqry = {'query_string':{'query':'*' + q.lstrip('*').rstrip('*') + '*'}}
        projqryobj['query']['bool']['must'].append(qqry)
        commqryobj['query']['bool']['must'].append(qqry)
        finqryobj['query']['bool']['must'].append(qqry)
    
    if datefrom:
        fromqry = {"range" : {"dateto" : {"from" : datefrom}}}
        projqryobj['query']['bool']['must'].append(fromqry)
        commqryobj['query']['bool']['must'].append(fromqry)
        if not dateto:
            fromqry = {"range" : {"duedate" : {"from" : datefrom}}}
            finqryobj['query']['bool']['must'].append(fromqry)

    # if provided a maximum date to, then only return objects that have started before that date
    if dateto:
        toqry = {"range" : {"datefrom" : {"to" : dateto}}}
        projqryobj['query']['bool']['must'].append(toqry)
        commqryobj['query']['bool']['must'].append(toqry)
        if not datefrom:
            toqry = {"range" : {"duedate" : {"to" : dateto}}}
            finqryobj['query']['bool']['must'].append(toqry)
        
    # because financial events only have one date on which they occurred, when datefrom and dateto are both set,
    # simplify down to just one query on "date" with from and to params
    if datefrom and dateto:
        qry = {"range" : {"duedate" : {"from": datefrom, "to" : dateto}}}
        finqryobj['query']['bool']['must'].append(qry)
    
    linkables = {
        "projects": [i['_source'] for i in dao.Project.query(q=projqryobj,size=10000).get('hits',{}).get('hits',[])],
        "commitments": [i['_source'] for i in dao.Commitment.query(q=commqryobj,size=10000).get('hits',{}).get('hits',[])],
        "financials": [i['_source'] for i in dao.Financial.query(q=finqryobj,size=10000).get('hits',{}).get('hits',[])]
    }
    for each in linkables:
        if each not in ignore:
            for item in linkables[each]:
                item['rtype'] = each
                item['id'] = item['id'].replace(' ','_').lower()
                tid = item['id']
                if 'recipient' in item:
                    item['name'] = item['recipient']
                if 'budget' not in item:
                    if 'cost' in item:
                        item['budget'] = item['cost']
                        if not item['budget']: item['budget'] = 1000
                    if 'share' in item:
                        project = dao.Project.pull(item['project'])
                        pb = project.data.get('budget',0)
                        if not pb: pb = 0
                        sh = item.get('share',0)
                        if not sh: sh = 0
                        item['budget'] = int(pb) * ( int(sh) / 100 )
                    else:
                        item['budget'] = 1000
                if 'who' in item: # this one should be removed once used on clean data (keep the ones above tho)
                    item['name'] = item['who']
                if 'name' not in item:
                    if 'recipient' in item and item['recipient']:
                        item['name'] = item['recipient']
                    else:
                        item['name'] = item['id']
                if each == "commitments":
                    item['commitment'] = item['name']
                linktypes = ['proposer','seniorplusone','plusone','qc','lead','related','customer','funder','billing','project','commitment']
                for l in linktypes:
                    lnk = item.get(l,False)
                    if lnk:
                        obj = {"source":lnk.replace(' ','_').lower(),"target":tid.replace(' ','_').lower(), "rtype":l}
                        inlist = False
                        for tng in everything['links']:
                            check1 = tng['source'] + '_' + tng['target']
                            check2 = tng['target'] + '_' + tng['source']
                            thisone = obj['source'] + '_' + obj['target']
                            if thisone == check1 or thisone == check2:
                                inlist = True
                        if not inlist: 
                            everything['links'].append(obj)
                everything["nodes"].append(item)

    checklist = [i['id'] for i in everything['nodes']]
    tidylinks = []
    for val in everything["links"]:
        if val['source'] in checklist and val['target'] in checklist:
            tidylinks.append(val)
    everything["links"] = tidylinks

    if ignoreisolated:
        checklist = []
        for i in everything['links']:
            checklist.append(i['source'])
            checklist.append(i['target'])
        tidynodes = []
        for rec in everything["nodes"]:
            if rec['id'] in checklist:
                tidynodes.append(rec)
        everything['nodes'] = tidynodes

    return everything                        


# this is a JSON endpoint onto everything
@blueprint.route('/everything', methods=['GET','POST'])
def everything():
    e = geteverything(
        q=request.values.get('q',False),
        person=request.values.get('person',False), 
        project=request.values.get('project',False), 
        contact=request.values.get('contact',False), 
        contractor=request.values.get('contractor',False), 
        ignore=request.values.get('ignore','').split(','),
        ignoreisolated=request.values.get('ignoreisolated',False),
        datefrom=request.values.get('datefrom',False),
        dateto=request.values.get('dateto',False)
    )
    resp = make_response( json.dumps(e) )
    resp.mimetype = "application/json"
    return resp
    

# build an admin page where things can be done
@blueprint.route('/')
def index():
    opts = deepcopy(app.config['JSITE_OPTIONS'])
    opts['data'] = {"editable":False}
    return render_template('admin/index.html', jsite_options=json.dumps(opts), dropdowns=dropdowns(), everything=json.dumps(geteverything()), nosettings=True)


# show/save a particular admin item or else redirect back up to default page behaviour
@blueprint.route('/<itype>', methods=['GET','POST'])
@blueprint.route('/<itype>/<iid>', methods=['GET','POST'])
def adminitem(itype,iid=False):
    if itype in ['project','financial','commitment','contact','contractor']:
        klass = getattr(dao, itype[0].capitalize() + itype[1:] )
        if not iid and request.json:
            iid = request.json.get("id",False)
            if not iid:
                iid = request.json.get("name",'')
                if iid and 'companyname' in request.json:
                    iid += '_' + request.json["companyname"]
            if not iid:
                iid = request.json.get("reference",'')
                if iid:
                    exists = klass.pull(iid)
                    if exists:
                        iid = False
            if not iid:
                iid = dao.makeid()

        if iid:
            rec = klass.pull(iid)
            if request.method == 'GET':
                if rec is None:
                    abort(404)
                else:
                    resp = make_response( rec.json )
                    resp.mimetype = "application/json"
                    return resp
            elif request.method == 'POST':
                if rec is None:
                    rec = klass(**request.json)
                rec.data = request.json
                print rec.data
                rec.save()
                return ""
        else:
            abort(404)
    else:
        abort(404)


# return a status report for a given project
'''@blueprint.route('/project/<projectid>/report')
def report(projectid):
    project = dao.Project.pull(projectid)
    resp = make_response( json.dumps(project.report) )
    resp.mimetype = "application/json"
    return resp'''


'''
# show/save a particular project
@blueprint.route('/project', methods=['GET','POST'])
@blueprint.route('/project/<project>', methods=['GET','POST'])
def project(project=''):
    opts = deepcopy(app.config['JSITE_OPTIONS'])
    opts['data'] = {"editable":False}
        
    if request.method == 'GET':
        p = dao.Project.pull(project)
        if p is not None:
            return render_template('admin/project/index.html', jsite_options=json.dumps(opts), nosettings=True)
        else:
            return render_template('admin/project/index.html', jsite_options=json.dumps(opts), dropdowns=dropdowns(), nosettings=True)
    elif request.method == 'POST':
        proj = request.json
        commits = proj['commitments']
        finance = proj['finance']
        del proj['commitments']
        del proj['finance']
        p = dao.Project(**proj)
        p.save()
        for item in commits:
            t = dao.Commitment(**item)
            t.save()
        for item in finance:
            f = dao.Finance(**item)
            f.save()
        return ""
'''


'''
# save a particular type of object
@blueprint.route('/<itype>', methods=['GET','POST'])
def save(itype):
    klass = getattr(dao, itype[0].capitalize() + subpath[1:] )
    new = klass(**request.json)
    new.save()
    return ""
   
'''     




