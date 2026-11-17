import hmac
import json
import math
import os
import time
from functools import wraps

import requests
from elasticsearch.exceptions import ElasticsearchException
from flask import Blueprint, make_response, url_for, request

from portality import util
from portality.bll import DOAJ
from portality.core import app, es_connection

blueprint = Blueprint('status', __name__)


def _status_credentials():
    """ (username, password) for the protected status endpoints, or None if they aren't configured """
    username = app.config.get("STATUS_BASIC_AUTH_USERNAME")
    password = app.config.get("STATUS_BASIC_AUTH_PASSWORD")
    if not username or not password:
        return None
    return username, password


def status_auth_required(fn):
    """ Require HTTP basic auth matching STATUS_BASIC_AUTH_*. Refuses everything if those aren't configured. """
    @wraps(fn)
    def decorated(*args, **kwargs):
        creds = _status_credentials()
        auth = request.authorization
        if (creds is not None and auth is not None and auth.type == "basic"
                and hmac.compare_digest((auth.username or "").encode(), creds[0].encode())
                and hmac.compare_digest((auth.password or "").encode(), creds[1].encode())):
            return fn(*args, **kwargs)
        resp = make_response("Authentication required", 401)
        resp.headers["WWW-Authenticate"] = 'Basic realm="DOAJ status"'
        return resp
    return decorated


@blueprint.route('/ping')
def ping():
    """ Cheap, unauthenticated check for uptime monitors: this app worker is responding, and the search cluster
    answers a ping (which reads no index data). 503 if the search cluster can't be reached. """
    try:
        # ping() already returns False on connection errors and timeouts (TransportError)
        es_ok = es_connection.ping(request_timeout=2)
    except ElasticsearchException:
        es_ok = False
    resp = make_response("OK" if es_ok else "Search unavailable", 200 if es_ok else 503)
    resp.mimetype = "text/plain"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@blueprint.route('/stats')
@status_auth_required
@util.jsonp
def stats():
    res = {}

    # Get inode use
    try:
        st = os.statvfs('/')
        res['inode_used_pc'] = int((float(st.f_files-st.f_ffree)/st.f_files)*100)
        # could complete this by installing and using psutil but as disk and memory can currently 
        # be monitored directly by DO, no current need - can change if we move from DO
        #res['disk_used_pc'] = int((float(st.f_blocks-st.f_bavail)/st.f_blocks)*100)
        #res['memory_used_pc'] = 0
    except (OSError, ZeroDivisionError):
        pass

    # Test writing to filesystem
    ts = int(time.time())
    fn = '/tmp/status_test_write_' + str(ts) + '.txt'
    try:
        f = open(fn, "w")
        f.write("I am a test at " + str(ts))
        f.close()
        res['writable'] = True
    except OSError:
        res['writable'] = False
    try:
        os.remove(fn)
    except OSError:
        pass

    # Retrieve the hostname
    try:
        hn = os.uname()[1]
        res['host'] = hn
    except (AttributeError, OSError):   # os.uname is POSIX-only
        pass

    # Return a JSON response
    resp = make_response(json.dumps(res))
    resp.mimetype = "application/json"
    return resp


@blueprint.route('/')
@status_auth_required
@util.jsonp
def status():
    res = {'stable': True, 'ping': {'apps': {}, 'indices': {}}, 'background': {'status': 'Background jobs are stable', 'info': []}, 'notes': []}

    # to get monitoring on this, use uptime robot or similar to check that the status page 
    # contains the 'stable': True string and the following note strings

    app_note = 'apps reachable'
    app_unreachable = 0
    inodes_note = 'inode use on app machines below 95%'
    inodes_high = 0
    writable_note = 'app machines can write to disk'
    not_writable = 0
    #disk_note = 'disk use on app machines below 95%'
    #disk_high = 0
    #memory_note = 'memory use on app machines below 95%'
    #memory_high = 0
    es_note = 'indexes stable'
    es_unreachable = 0
    indexable_note = 'index accepts index/delete operations'
    cluster_note = 'cluster stable'

    for addr in app.config.get('APP_MACHINES_INTERNAL_IPS', []):
        if not addr.startswith('http'): addr = 'http://' + addr
        addr += url_for('.stats')
        try:
            r = requests.get(addr, auth=_status_credentials(), timeout=10)
        except requests.exceptions.RequestException:
            res['ping']['apps'][addr] = 'unreachable'
            res['stable'] = False
            app_unreachable += 1
            app_note = str(app_unreachable) + ' APPS UNREACHABLE'
            continue
        res['ping']['apps'][addr] = r.status_code if r.status_code != 200 else r.json()
        try:
            if res['ping']['apps'][addr].get('inode_used_pc',0) >= 95:
                inodes_high += 1
                inodes_note = 'INODE GREATER THAN 95% ON ' + str(inodes_high) + ' APP MACHINES'
            if res['ping']['apps'][addr].get('writable',False) != True:
                not_writable += 1
                writable_note = 'WRITE FAILURE ON ' + str(not_writable) + ' APP MACHINES'
            #if res['ping']['apps'][addr].get('disk_used_pc',0) >= 95:
            #    disk_high += 1
            #    disk_note = 'DISK USE GREATER THAN 95% ON ' + disk_high + ' APP MACHINES'
            #if res['ping']['apps'][addr].get('memory_used_pc',0) >= 95:
            #    memory_high += 1
            #    memory_note = 'MEMORY USE GREATER THAN 95% ON ' + memory_high + ' APP MACHINES'
        except AttributeError:   # a non-200 response was recorded as its status code, not a dict of stats
            pass
        if r.status_code != 200:
            res['stable'] = False
            app_unreachable += 1
            app_note = str(app_unreachable) + ' APPS UNREACHABLE'
    res['notes'].append(app_note)
    res['notes'].append(inodes_note)
    res['notes'].append(writable_note)
    #res['notes'].append(disk_note)
    #res['notes'].append(memory_note)

    # check that all necessary ES nodes can actually be pinged from this machine
    for eddr in app.config['ELASTICSEARCH_HOSTS']:
        es_addr = eddr if isinstance(eddr, str) else f'http://{eddr["host"]}:{eddr["port"]}'
        try:
            r = requests.get(es_addr, timeout=3)
            res['ping']['indices'][es_addr] = r.status_code
            es_ok = r.status_code == 200
        except requests.exceptions.RequestException:
            res['ping']['indices'][es_addr] = 'unreachable'
            es_ok = False
        if not es_ok:
            res['stable'] = False
            es_unreachable += 1
            es_note = str(es_unreachable) + ' INDEXES UNREACHABLE'
    res['notes'].append(es_note)

    # query ES for cluster health and nodes up (uses second ES host in config)
    # a failed request, a non-JSON body or an unexpected response shape all mean we can't vouch for the cluster
    es_errors = (requests.exceptions.RequestException, ValueError, KeyError)
    try:
        es = requests.get(es_addr + '/_stats', timeout=10).json()
        res['index'] = { 'cluster': {}, 'shards': { 'total': es['_shards']['total'], 'successful': es['_shards']['successful'] }, 'indices': {} }
        for k, v in es['indices'].items():
            res['index']['indices'][k] = { 'docs': v['primaries']['docs']['count'], 'size': int(math.ceil(v['primaries']['store']['size_in_bytes']) / 1024 / 1024) }
        try:
            ces = requests.get(es_addr + '/_cluster/health', timeout=10)
            res['index']['cluster'] = ces.json()
            if res['index']['cluster']['status'] != 'green':
                res['stable'] = False
                cluster_note = 'CLUSTER UNSTABLE'
        except es_errors:
            res['stable'] = False
            cluster_note = 'CLUSTER UNSTABLE'
    except es_errors:
        res['stable'] = False
        cluster_note = 'CLUSTER UNSTABLE'
    res['notes'].append(cluster_note)

    # check background jobs
    # ~~BackgroundTask:Monitoring~~
    bgtask_status_service = DOAJ.backgroundTaskStatusService()
    res['background'] = bgtask_status_service.create_background_status()
    if not bgtask_status_service.is_stable(res['background'].get('status')):
        res['stable'] = False

    resp = make_response(json.dumps(res))
    resp.mimetype = "application/json"
    return resp
