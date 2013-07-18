'''
An endpoint for exposing a sitemap generated from records in the index.
Needs work - functional but not great.
Needs updating to expose XML too.
'''


import json
from copy import deepcopy

from flask import Blueprint, request, redirect, abort, make_response, render_template
from flask.ext.login import current_user

from portality.core import app
import portality.util as util
import portality.models as models


blueprint = Blueprint('sitemap', __name__)


@blueprint.route('.xml')
def xml():
    resp = render_template('sitemap/sitemap.xml')
    resp.mimetype = "application/xml"
    return resp


@blueprint.route('/')
def index():
    jsitemap = deepcopy(app.config['JSITE_OPTIONS'])
    jsitemap['facetview']['initialsearch'] = False
    jsitemap['editable'] = False

    if util.request_wants_json() and not current_user.is_anonymous():
        resp = render_template( 'sitemap/sitemap.json')
        resp.mimetype = "application/json"
        return resp
    elif current_user.is_anonymous():
        return render_template('sitemap/sitemap.html', public=True, jsite_options=json.dumps(jsitemap), nosettings=True)
    else:
        return render_template('sitemap/sitemap.html', public=False, jsite_options=json.dumps(jsitemap), nosettings=True)


@blueprint.route('/<path:path>', methods=['GET','POST','DELETE'])
def update(path=''):
    sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))

    if request.method == 'DELETE':
        if current_user.is_anonymous():
            abort(401)
        else:
            # TODO: delete the details of the current sent record from the sitenav
            # unless it has children. Then just leave it in.
            pass

    else:
        if current_user.is_anonymous():
            abort(401)
        
        parts = path.lstrip('/').rstrip('/').split('/')
        payload = request.json
        newmenuobj = {
            'url': payload['url'],
            'section': payload.get('title',parts[-1]),
            'access': payload.get('accessible',True),
            'listed': payload.get('visible',False)
        }
        pos = sitemap
        url = ''
        for key,part in enumerate(parts):
            if part:
                url += '/' + part
                if part in pos.keys():
                    if len(parts) == key+1:
                        pos[part]['__META__'] = newmenuobj
                    else:
                        pos[part]['__META__'] = {'url':url,'section':part,'access':True,'listed':True}
                else:
                    pos[part] = {'__META__':newmenuobj}
                pos = pos[part]
                    
        out = open('portality/templates/sitemap/sitemap.json','w')
        out.write(json.dumps(sitemap, indent=4))
        out.close()

        update_sitemaps()

        resp = make_response( json.dumps(sitemap, indent=4) )
        resp.mimetype = "application/json"
        return resp
        

@blueprint.route('/refresh')
def refresh():
    if current_user.is_anonymous():
        abort(401)
    out = open('portality/templates/sitemap/sitemap.json','w')
    out.write('{}')
    out.close()
    records = models.Record.query(size=1000000)
    for record in [rec['_source'] for rec in records['hits']['hits']]:
        request.json = record
        update(path=record['url'])
    return redirect('/sitemap')


def update_sitemaps():
    sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))
    generate_sitemap_xml(sitemap=sitemap)
    generate_sitemap_html(sitemap=sitemap)
    generate_sitemap_public_html(sitemap=sitemap)
    generate_sitenav(sitemap=sitemap)

def generate_sitemap_xml(sitemap=False):
    if not sitemap:
        sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))
     # TODO: finish this, have it meet google sitemap / resourcesync reqs
     # add anything necessary to handle versioning for resourcesync above too
    pass
    
def generate_sitemap_html(sitemap=False):
    if not sitemap:
        sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))
    sn = '<ul style="list-style-type:none;margin-left:10px;">\n'
    for key,menu in sitemap.items():
        if len(menu.keys()) > 1:
            sn += '<li><h2><a href="' + menu['__META__']['url'] + '">' + menu['__META__']['section'] + '</a></h2>\n'
            sn += '<ul style="list-style-type:none;margin-left:20px;">\n'
            for key,child in menu.items():
                if key != '__META__':
                    sn += '<li><h3><a href="' + child['__META__']['url'] + '">' + child['__META__']['section'] + '</a></h3>\n'
                    if len(child.keys()) > 1:
                        sn += '<ul style="list-style-type:none;margin-left:20px;">\n'
                        for k,kid in child.items():
                            if k != '__META__':
                                sn += '<h4><li><a href="' + kid['__META__']['url'] + '">' + kid['__META__']['section'] + '</a></h4></li>\n'
                        sn += '</ul>\n'
                    sn += '</li>\n'
            sn += '</ul>\n'
            sn += '</li>\n'
        elif menu['__META__'].get('listed',False) and menu['__META__'].get('access',True):
            sn += '<li><h2><a href="' + menu['__META__']['url'] + '">' + menu['__META__']['section'] + '</a></h2></li>\n'
    sn += '</ul>'
    
    out = open('portality/templates/sitemap/sitemap_private.html','w')
    out.write(sn)
    out.close()

def generate_sitemap_public_html(sitemap=False):
    if not sitemap:
        sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))
    sn = '<ul style="list-style-type:none;margin-left:10px;">\n'
    for key,menu in sitemap.items():
        if len(menu.keys()) > 1:
            sn += '<li><h2><a href="' + menu['__META__']['url'] + '">' + menu['__META__']['section'] + '</a></h2>\n'
            sn += '<ul style="list-style-type:none;margin-left:20px;">\n'
            for key,child in menu.items():
                if key != '__META__':
                    if child['__META__']['listed'] and child['__META__']['access'] or len(child.keys()) > 1:
                        sn += '<li><h3><a href="' + child['__META__']['url'] + '">' + child['__META__']['section'] + '</a></h3>\n'
                    if len(child.keys()) > 1:
                        sn += '<ul style="list-style-type:none;margin-left:20px;">\n'
                        for k,kid in child.items():
                            if k != '__META__':
                                if kid['__META__']['listed'] and kid['__META__']['access']:
                                    sn += '<li><h4><a href="' + kid['__META__']['url'] + '">' + kid['__META__']['section'] + '</a></h4></li>\n'
                        sn += '</ul>\n'
                    if child['__META__']['listed'] and child['__META__']['access'] or len(child.keys()) > 1:
                        sn += '</li>\n'
            sn += '</ul>\n'
            sn += '</li>\n'
        elif menu['__META__'].get('listed',False) and menu['__META__'].get('access',True):
            sn += '<li><h2><a href="' + menu['__META__']['url'] + '">' + menu['__META__']['section'] + '</a></h2></li>\n'
    sn += '</ul>'

    out = open('portality/templates/sitemap/sitemap_public.html','w')
    out.write(sn)
    out.close()

def generate_sitenav(sitemap=False):
    if not sitemap:
        sitemap = json.load(open('portality/templates/sitemap/sitemap.json'))
    sn = ''
    for key,menu in sitemap.items():
        if menu['__META__'].get('listed',False) and menu['__META__'].get('access',True) and menu['__META__']['url'] not in ['/admin','/sitemap','/tagging','/stream']:
            sn += '<li><a href="' + menu['__META__']['url'] + '">' + menu['__META__']['section'] + '</a></li>\n'

    out = open('portality/templates/sitemap/sitenav.html','w')
    out.write(sn)
    out.close()

