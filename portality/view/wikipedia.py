# based on Etiennes work for bibserver

import sys, re, json
import urllib, urllib2, httplib
import traceback

def repl(matchobj):
    return matchobj.group(0)

def wikitext_to_dict(txt):
    buf = []
    for c in re.findall('{{Citation |cite journal(.*?)}}', txt):
        if c.strip().startswith('needed'): continue
        c = re.sub('{{.*?|.*?|(.*?)}}', repl, c)
        tmp = {}
        for cc in c.split('|'):
            ccc = cc.strip().split('=')
            if len(ccc) == 2:
                tmp[ccc[0].strip()] = ccc[1].strip()
        if tmp:
            if 'author' in tmp:
                auth_string = tmp['author'].split(',')
                tmp['author'] = []
                for au in auth_string:
                    au = au.strip()
                    if au.startswith('and '):
                        au = au[4:]
                    tmp.setdefault('author', []).append({'name':au})
            name = '%s %s' % (tmp.get('first',''), tmp.get('last', ''))
            if name.strip():
                tmp.setdefault('author', []).append({'name':name})
            if 'journal' in tmp:
                tmp['journal'] = {'name':tmp['journal']}
            buf.append(tmp)
    return buf
    
def wikiparse(q):
    URL = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit=10&srprop=wordcount&format=json&srsearch='
    URLraw = 'http://en.wikipedia.org/w/index.php?action=raw&title='
    data = urllib2.urlopen(URL+urllib.quote_plus(q)).read()
    data_json = json.loads(data)
    records = []
    
    #try:
    search_result = data_json.get("query")
    if not search_result: search_result = data_json.get("query-continue", {"search":[]})
    for x in search_result["search"]:
        if x['wordcount'] > 20:
            quoted_title = urllib.quote_plus(x['title'].replace(' ','_').encode('utf8'))
            #try:
            title_data = urllib2.urlopen(URLraw+quoted_title).read()
            #except httplib.BadStatusLine:
            #    sys.stderr.write('Problem reading %s\n' % (URLraw+quoted_title))
            #    continue
            records.append({'name':x['title'], 'url':'http://en.wikipedia.org/wiki/'+x['title'].replace(' ','_')})
            '''citations = wikitext_to_dict(title_data)
            if citations:
                links = []
                for c in citations:
                    link = 'http://en.wikipedia.org/wiki/'+quoted_title
                    c['link'] = [{'url':link}]
                    if link not in links:
                        records.append(c)
                        links.append(link)'''
    #except:
    #    sys.stderr.write(traceback.format_exc())
        
    return records
    

