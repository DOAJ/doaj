from flask import Blueprint, make_response
from portality import util
from portality.core import app
from portality import models
from portality.lib import dates
import json, requests, math, os, time
from datetime import datetime

blueprint = Blueprint('status', __name__)


@blueprint.route('/stats')
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
    except:
        pass

    # Test writing to filesystem
    ts = int(time.time())
    fn = '/tmp/status_test_write_' + str(ts) + '.txt'
    try:
        f = open(fn, "w")
        f.write("I am a test at " + str(ts))
        f.close()
        res['writable'] = True
    except:
        res['writable'] = False
    try:
        os.remove(fn)
    except:
        pass

    # Retrieve the hostname
    try:
        hn = os.uname()[1]
        res['host'] = hn
    except:
        pass
    
    # Return a JSON response
    resp = make_response(json.dumps(res))
    resp.mimetype = "application/json"
    return resp


@blueprint.route('/')
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

    for addr in app.config.get('APP_MACHINES_INTERNAL_IPS',[]):
        if not addr.startswith('http'): addr = 'http://' + addr
        addr += '/status/stats'
        r = requests.get(addr)
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
        except:
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
    for eddr in [app.config['ELASTIC_SEARCH_HOST']] if isinstance(app.config['ELASTIC_SEARCH_HOST'], str) else app.config['ELASTIC_SEARCH_HOST']:
        if not eddr.startswith('http'): eddr = 'http://' + eddr
        if not eddr.endswith(':9200'): eddr += ':9200'
        r = requests.get(eddr)
        res['ping']['indices'][eddr] = r.status_code
        res['stable'] = r.status_code == 200
        if r.status_code != 200:
            res['stable'] = False
            es_unreachable += 1
            es_note = str(es_unreachable) + ' INDEXES UNREACHABLE'
    res['notes'].append(es_note)
        
    # query ES for cluster health and nodes up
    es_addr = str(app.config['ELASTIC_SEARCH_HOST'][0] if not isinstance(app.config['ELASTIC_SEARCH_HOST'], str) else app.config['ELASTIC_SEARCH_HOST']).rstrip('/')
    if not es_addr.startswith('http'): es_addr = 'http://' + es_addr
    if not es_addr.endswith(':9200'): es_addr += ':9200'
    try:
        es = requests.get(es_addr + '/_status').json()
        res['index'] = { 'cluster': {}, 'shards': { 'total': es['_shards']['total'], 'successful': es['_shards']['successful'] }, 'indices': {} }
        for k, v in es['indices'].items():
            res['index']['indices'][k] = { 'docs': v['docs']['num_docs'], 'size': int(math.ceil(v['index']['primary_size_in_bytes']) / 1024 / 1024) }
        try:
            ces = requests.get(es_addr + '/_cluster/health')
            res['index']['cluster'] = ces.json()
            res['stable'] = res['index']['cluster']['status'] == 'green'
            if res['index']['cluster']['status'] != 'green': cluster_note = 'CLUSTER UNSTABLE'
        except:
            res['stable'] = False
            cluster_note = 'CLUSTER UNSTABLE'
    except:
        res['stable'] = False
        cluster_note = 'CLUSTER UNSTABLE'
    res['notes'].append(cluster_note)

    if False: # remove this False if happy to test write to the index (could be a setting)
        if res['stable'] and False:
            try:
                ts = str(int(time.time()))
                test_index = 'status_test_writable_' + ts
                test_type = 'test_' + ts
                test_id = ts
                rp = requests.put(es_addr + '/' + test_index + '/' + test_type + '/' + test_id, json={'hello': 'world'})
                if rp.status_code != 201:
                    indexable_note = 'NEW INDEX WRITE OPERATION FAILED TO WRITE, RETURNED ' + str(rp.status_code)
                else:
                    try:
                        rr = requests.get(es_addr + '/' + test_index + '/' + test_type + '/' + test_id).json()
                        if rr['hello'] != 'world':
                            indexable_note = 'INDEX READ DID NOT FIND EXPECTED VALUE IN NEW WRITTEN RECORD'
                        try:
                            rd = requests.delete(es_addr + '/' + test_index)
                            if rd.status_code != 200:
                                indexable_note = 'INDEX DELETE OF TEST INDEX DID NOT RETURNED UNEXPECTED STATUS CODE OF ' + str(rd.status_code)
                            try:
                                rg = requests.get(es_addr + '/' + test_index)
                                if rg.status_code != 404:
                                    indexable_note = 'INDEX READ AFTER DELETE TEST RETURNED UNEXPECTED STATUS CODE OF ' + str(rg.status_code)
                            except:
                                pass
                        except:
                            indexable_note = 'INDEX DELETE OF TEST INDEX FAILED'
                    except:
                        indexable_note = 'INDEX READ OF NEW WRITTEN RECORD DID NOT SUCCEED'
            except:
                indexable_note = 'INDEX/DELETE OPERATIONS CAUSED EXCEPTION'
        else:
            indexable_note = 'INDEX/DELETE OPERATIONS NOT TESTED DUE TO SYSTEM ALREADY UNSTABLE'
        res['notes'].append(indexable_note)

    # check background jobs
    try:
        # check if journal_csv, which should run at half past every hour on the main queue, has completed in the last 2 hours (which confirms main queue)
        qcsv = {"query": {"bool": {"must": [
            {"term":{"status":"complete"}},
            {"term":{"action":"journal_csv"}},
            {"range": {"created_date": {"gte": dates.format(dates.before(datetime.utcnow(), 7200))}}}
        ]}}, "size": 1, "sort": {"created_date": {"order": "desc"}}}
        rcsv = models.BackgroundJob.send_query(qcsv)['hits']['hits'][0]['_source']
        res['background']['info'].append('journal_csv has run in the last 2 hours, confirming main queue is running')
    except:
        res['background']['status'] = 'Unstable'
        res['background']['info'].append('Error when trying to check background job journal_csv in the last 2 hours - could be a problem with this job or with main queue')
        res['stable'] = False
    try:
        # check if prune_es_backups, which should run at 9.30am every day, has completed in the last 24 hours (which confirms long running queue)
        qprune = {"query": {"bool": {"must": [
            {"term":{"status":"complete"}},
            {"term":{"action":"prune_es_backups"}},
            {"range": {"created_date": {"gte": dates.format(dates.before(datetime.utcnow(), 86400))}}}
        ]}}, "size": 1, "sort": {"created_date": {"order": "desc"}}}
        rprune = models.BackgroundJob.send_query(qprune)['hits']['hits'][0]['_source']
        res['background']['info'].append('prune_es_backups has run in the last 24 hours, confirming long running queue is running')
    except:
        res['background']['status'] = 'Unstable'
        res['background']['info'].append('Error when trying to check background job prune_es_backups in the last 24 hours - could be a problem with this job or with long running queue')
        res['stable'] = False
    try:
        # remove old jobs if there are too many - remove anything over six months and complete
        qbg = {"query": {"bool": {"must": [
            {"term":{"status":"complete"}},
            {"range": {"created_date": {"lte": dates.format(dates.before(datetime.utcnow(), 15552000))}}}
        ]}}, "size": 10000, "sort": {"created_date": {"order": "desc"}}, "fields": "id"}
        rbg = models.BackgroundJob.send_query(qbg)
        for job in rbg.get('hits',{}).get('hits',[]):
            models.BackgroundJob.remove_by_id(job['fields']['id'][0])
        res['background']['info'].append('Removed ' + rbg['hits']['total'] + ' old complete background jobs')
    except:
        res['background']['status'] = 'Unstable'
        res['background']['info'].append('Error when trying to remove old background jobs')
        res['stable'] = False


    resp = make_response(json.dumps(res))
    resp.mimetype = "application/json"
    return resp


{"query": {"bool": {"must": [{"term":{"status":"complete"}}]}}, "size": 10000, "sort": {"created_date": {"order": "desc"}}, "fields": "id"}

