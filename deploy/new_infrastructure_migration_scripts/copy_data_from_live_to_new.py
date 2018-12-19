
# this file exports data using a scan scroll from one index and bulk loads it to another

import json, requests

save_to_file = True
index_name = 'doaj'
types = []
old_index = ''
new_index = 'http://localhost:9200'
scroll_minutes = '5m'
size = 5000
bulk_size = 50000 # this is rough, as the scan may not get exact sizes

# need to query across absolutely everything in the live index
# probably needs to be a scan scroll

# then upload them in batches to the new index

# worth copying them to disk as we get them?

processed = {}

for tp in types:
    processed[tp] = 0
    start = requests.post(old_index + '/' + index_name + '/' + tp + '/_search?search_type=scan&scroll=' + scroll_minutes, json={"query": { "match_all": {} }, "size": size })
    res = start.json()
    records = []
    first = True
    while (res.get('scroll_id',False) != False and (first == True or len(res.get('hits',{}).get('hits',[])) > 0)) or len(records) != 0:
        first = False # a scan scroll will start empty, unlike a normal scroll - so need to know when looking at the first result
        if len(records) > bulk_size:
            if save_to_file == True:
                out = open('records_' + tp + '_to_' + processed + '.json','w')
                out.write(json.dumps(records, indent=2))
                out.close()
            bn = ''
            for record in records:
                bn += json.dumps({'index':{'_index':index_name, '_type': tp, '_id': record['_id']}}) + '\n'
                bn += json.dumps(record) + '\n'
            s = requests.post(new_index + '/_bulk', data=bn)
            print tp
            print processed[tp]
            print s.status_code
            records = []
        processed[tp] += len(res['hits']['hits'])
        for r in res.get('hits',{}).get('hits',[]):
            records.append(r['_source'])
        if res.get('scroll_id',False) != False:
            nxt = requests.get(old_index + '/_search/scroll?scroll=' + scroll_minutes + '&scroll_id=' + res['_scroll_id'])
            res = nxt.json()

print json.dumps(processed, indent=2)
