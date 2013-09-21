
from datetime import datetime

from portality.core import app

from portality.dao import DomainObject as DomainObject

'''
Define models in here. They should all inherit from the DomainObject.
Look in the dao.py to learn more about the default methods available to the Domain Object.
When using portality in your own flask app, perhaps better to make your own models file somewhere and copy these examples
'''


# an example account object, which requires the further additional imports
# There is a more complex example below that also requires these imports
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls,email):
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return not self.is_anonymous() and self.id in app.config['SUPER_USER']
    

# a typical record object, with no special abilities
class Record(DomainObject):
    __type__ = 'record'

    
# a special object that allows a search onto all index types - FAILS TO CREATE INSTANCES
class Everything(DomainObject):
    __type__ = 'everything'

    @classmethod
    def target(cls):
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/'
        return t


# a page manager object, with a couple of extra methods
class Pages(DomainObject):
    __type__ = 'pages'

    @classmethod
    def pull_by_url(cls,url):
        res = cls.query(q={"query":{"term":{'url.exact':url}}})
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    def update_from_form(self, request):
        newdata = request.json if request.json else request.values
        for k, v in newdata.items():
            if k == 'tags':
                tags = []
                for tag in v.split(','):
                    if len(tag) > 0: tags.append(tag)
                self.data[k] = tags
            elif k in ['editable','accessible','visible','comments']:
                if v == "on":
                    self.data[k] = True
                else:
                    self.data[k] = False
            elif k not in ['submit']:
                self.data[k] = v
        if not self.data['url'].startswith('/'):
            self.data['url'] = '/' + self.data['url']
        if 'title' not in self.data or self.data['title'] == "":
            self.data['title'] = 'untitled'

    def save_from_form(self, request):
        self.update_from_form(request)
        self.save()
    

# You can make simple models that just reside in their own index type.
# Then other model types may rely on them, or they may be used on your frontend. Whatever.
class SearchHistory(DomainObject):
    __type__ = 'searchhistory'


# You could write a record model that stores versions of itself in an archive.
# In which case, here is an example of an Archive model.
class Archive(DomainObject):
    __type__ = 'archive'
    
    @classmethod
    def store(cls, data, action='update'):
        archive = Archive.get(data.get('_id',None))
        if not archive:
            archive = Archive(_id=data.get('_id',None))
        if archive:
            if 'store' not in archive.data: archive.data['store'] = []
            try:
                who = current_user.id
            except:
                who = data.get('_created_by','anonymous')
            archive.data['store'].insert(0, {
                'date':data.get('_last_modified', datetime.now().strftime("%Y-%m-%d %H%M")), 
                'user': who,
                'state': data, 
                'action':action
            })
            archive.save()
        

# Here is a much more complex Record object that defines its own ID generator, merges and deduplicates itself,
# tracks its own history, and knows what collections it belongs to and some other things
# (taken from http://github.com/okfn/bibserver
'''class Record(DomainObject):
    __type__ = 'record'

    @classmethod
    def get(cls, id_):
        if id_ is None:
            return None
        try:
            out = requests.get(cls.target() + id_)
            if out.status_code == 404:
                return None
            else:
                rec = cls(**out.json())
                rec.data['_views'] = int(rec.data.get('_views',0)) + 1
                rec.data['_last_viewed'] = datetime.now().strftime("%Y-%m-%d %H%M")
                r = requests.post(rec.target() + rec.id, data=json.dumps(rec.data))
                return rec
        except:
            return None

    @property
    def views(self):
        return self.data.get('_views',0)

    @classmethod
    def make_rid(cls,data):
        id_data = {
            'author': [i.get('name','') for i in data.get('author',[])].sort(),
            'title': data.get('title','')
        }
        buf = util.slugify(json.dumps(id_data, sort_keys=True).decode('unicode-escape'),delim=u'')
        new_id = hashlib.md5(buf).hexdigest()
        return new_id

    @classmethod
    def sameas(cls,rid):
        res = cls.query(terms={'_sameas':rid})
        if res['hits']['total'] == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    @classmethod
    def merge(cls, a, b) :
        for k, v in a.items():
            if k.startswith('_') and k not in ['_collection']:
                del a[k]
            elif isinstance(v, dict) and k in b:
                cls.merge(v, b[k])
            elif isinstance(v, list) and k in b:
                if not isinstance(b[k], list):
                    b[k] = [b[k]]
                for idx, item in enumerate(v):
                    if isinstance(item,dict) and idx < len(b[k]):
                        cls.merge(v[idx],b[k][idx])
                    elif k in ['_collection'] and item not in b[k]:
                        b[k].append(item)
        a.update(b)
        return a

    @property
    def history(self):
        archive = Archive.get(self.data.get('_id',None))
        if archive:
            return archive.data.get('store',[])
        else:
            return []
    
    # remove a record from a collection - bypasses the main save which always tries to greedily retain info    
    def removefromcollection(self,collid):
        collid = collid.replace('/','_____')
        if collid in self.data.get('_collection',[]):
            self.data['_collection'].remove(collid)
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        Archive.store(self.data)

    def addtocollection(self,collid):
        collid = collid.replace('/','_____')
        if '_collection' not in self.data:
            self.data['_collection'] = []
        if collid not in self.data['_collection']:
            self.data['_collection'].append(collid)
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        Archive.store(self.data)

    # add or remove a tag to a record
    def removetag(self,tagid):
        if tagid in self.data.get('_tag',[]):
            self.data['_tag'].remove(tagid)
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        Archive.store(self.data)

    def addtag(self,tagid):
        if '_tag' not in self.data:
            self.data['_tag'] = []
        if tagid not in self.data['_tag']:
            self.data['_tag'].append(tagid)
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        Archive.store(self.data)

    # returns a list of current users collections that this record is in
    @property
    def isinmy(self):
        colls = []
        if current_user is not None and not current_user.is_anonymous():
            for item in self.data['_collection']:
                if item.startswith(current_user.id):
                    colls.append(item)
        return colls
            
    def save(self):
        # archive the old version
        if app.config['ARCHIVING']:
            Archive.store(self.data)

        # make an ID based on current content - builds from authors and title
        derivedID = self.make_rid(self.data)

        # look for any stored record with the derived ID
        exists = requests.get(self.target() + derivedID)
        if exists.status_code == 200:
            # where found, merge with current data and this record will be overwritten on save
            self.data = self.merge(self.data, exists.json()['_source'])

        # if this record has a new ID, need to merge the old record and delete it
        if self.id is not None and self.id != derivedID:
            old = requests.get(self.target() + self.id)
            if old.status_code == 200:
                self.data = self.merge(self.data, old.json()['_source'])
                if '_sameas' not in self.data: self.data['_sameas'] = []
                self.data['_sameas'].append(self.id)
                Archive.store(self.data, action='delete')
                r = requests.delete( self.target() + self.id )

        # ensure the latest ID is used by this record now                
        self.data['_id'] = derivedID
        
        # make sure all collection refs are lower-cased
        self.data['_collection'] = [i.lower() for i in self.data.get('_collection',[])]
        
        # update site url, created date, last modified date
        if 'SITE_URL' in app.config:
            self.data['url'] = app.config['SITE_URL'].rstrip('/') + '/record/' +  self.id
            if 'identifier' not in self.data: self.data['identifier'] = []
            if 'bibsoup' not in [i['type'] for i in self.data['identifier']]:
                self.data['identifier'].append({'type':'bibsoup','url':self.data['url'],'id':self.id})
        if '_created' not in self.data:
            self.data['_created'] = datetime.now().strftime("%Y-%m-%d %H%M")
        self.data['_last_modified'] = datetime.now().strftime("%Y-%m-%d %H%M")
            
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        return r.status_code


    @classmethod
    def bulk(cls, records):
        # TODO: change this to a bulk es save
        for item in records:
            new = Record(**item)
            success = 0
            attempts = 0
            while success != 200 and attempts < 10:
                time.sleep(attempts * 0.1)
                success = new.save()
                attempts += 1

    def delete(self):
        Archive.store(self.data, action='delete')
        r = requests.delete( self.target() + self.id )

    def similar(self,field="title"):
        res = Record.query(recid=self.id, endpoint='_mlt', q='mlt_fields=' + field + '&min_term_freq=1&percent_terms_to_match=1&min_word_len=3')
        return [Record(**i['_source']) for i in res['hits']['hits']]
    
    @property
    def valuelist(self):
        # a list of all the values in the record
        vals = []
        def valloop(obj):
            if isinstance(obj,dict):
                for item in obj:
                    valloop(obj[item])
            elif isinstance(obj,list):
                for thing in obj:
                    valloop(thing)
            else:
                vals.append(obj)
        valloop(self.data)
        return vals
        
    @property
    def valuelist_string(self):
        return json.dumps(self.valuelist)

    @property
    def remote(self):
        # check any listed external APIs for relevant data to return
        # TODO: just does service core for now - implement for others
        info = {}
        apis = app.config['EXTERNAL_APIS']
        if apis['servicecore']['key']:
            try:
                servicecore = "not found in any UK repository"
                addr = apis['servicecore']['url'] + self.data['title'].replace(' ','%20') + "?format=json&api_key=" + apis['servicecore']['key']
                r = requests.get(addr)
                data = r.json()
                if 'ListRecords' in data and len(data['ListRecords']) != 0:
                    info['servicecore'] = data['ListRecords'][0]['record']['metadata']['oai_dc:dc']
            except:
                pass
        return info

    # build how it should look on the page
    @property
    def pretty(self):
        result = '<p>'
        img = False
        if img:
            result += '<img class="thumbnail" style="float:left; width:100px; margin:0 5px 10px 0; max-height:150px;" src="' + img[0] + '" />'

        record = self.data
        lines = ''
        if 'title' in record:
            lines += '<h2>' + record['title'] + '</h2>'
        if 'author' in record:
            lines += '<p>'
            authors = False
            for obj in record.get('author',[]):
                if authors: lines += ', '
                lines += obj.get('name','')
                authors = True
            lines += '</p>'
        if 'journal' in record:
            lines += '<p><i>' + record['journal'].get('name','') + '</i>'
            if 'year' in record:
                lines += ' (' + record['year'] + ')'
            lines += '</p>'
        elif 'year' in record:
            lines += '<p>(' + record['year'] + ')</p>'
        if 'link' in record:
            for obj in record['link']:
                lines += '<small><a target="_blank" href="' + obj['url'] + '">'
                if 'anchor' in obj:
                    lines += obj['anchor']
                else:
                    lines += obj['url']
                lines += '</a></small>'    
        
        if lines:
            result += lines
        else:
            result += json.dumps(record,sort_keys=True,indent=4)
        result += '</p>'
        return result
'''


# And a more complex Collection example to go with the above Record, also from bibserver
'''class Collection(DomainObject):
    __type__ = 'collection'

    @classmethod
    def get(cls, id_):
        if id_ is None:
            return None
        try:
            id_ = id_.replace('/','_____')
            out = requests.get(cls.target() + id_)
            if out.status_code == 404:
                return None
            else:
                rec = cls(**out.json())
                rec.data['_views'] = int(rec.data.get('_views',0)) + 1
                rec.data['_last_viewed'] = datetime.now().strftime("%Y-%m-%d %H%M")
                r = requests.post(rec.target() + rec.id, data=json.dumps(rec.data))
                return rec
        except:
            return None

    @property
    def views(self):
        return self.data.get('_views',0)
        
    def records(self, **kwargs):
        return [Record.get(**i['_source']['_id']) for i in Record.query(terms={'_collection':self.id}, **kwargs).get('hits',{}).get('hits',[])]

    def save(self):
        if not self.owner and not current_user.is_anonymous() and not self.data.get('public',False):
            self.data['owner'] = current_user.id
        if not self.data.get('slug',False):
            self.data['slug'] = util.slugify(self.data.get('name',uuid.uuid4().hex))
        if not self.id:
            self.data['_id'] = self.owner + '_____' + self.data['slug']
        if not self.data.get('url',False):
            url = app.config.get('SITE_URL','').rstrip('/') + '/'
            if self.owner:
                url += self.owner + '/'
            self.data['url'] = url + self.data['slug']
        if '_created' not in self.data:
            self.data['_created'] = datetime.now().strftime("%Y-%m-%d %H%M")
        self.data['_last_modified'] = datetime.now().strftime("%Y-%m-%d %H%M")
        r = requests.post(self.target() + self.id, data=json.dumps(self.data))
        print r.text

    def delete(self):
        r = requests.delete( self.target() + self.id )
        count = 0
        while count < len(self):
            for record in self.records(_from=count,size=100):
                record.removefromcollection(self.id)
            count += 100
    
    def __len__(self):
        return Record.query(terms={'_collection':self.id}).get('hits',{}).get('total',0)

    @property
    def owner(self):
        return self.data.get('owner','')
'''


# Here is a more complex Account model example, with calls back out to SearchHistory models
# Also expects a Collection model to exist, and defines how removal of a user account would include 
# removal of registration of collections to that user too.
'''class Account(DomainObject, UserMixin):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls,email):
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits',{}).get('total',0) == 1:
            return cls(**res['hits']['hits'][0]['_source'])
        else:
            return None

    @property
    def recentsearches(self):
        if app.config.get('QUERY_TRACKING', False):
            res = SearchHistory.query(terms={'user':current_user.id}, sort={"_created" + app.config.get('FACET_FIELD','.exact'):{"order":"desc"}}, size=100)
            print res
            return [i.get('_source',{}) for i in res.get('hits',{}).get('hits',[])]
        else:
            return []

    @property
    def recentviews(self):
        return self.data.get('recentviews',[])

    def addrecentview(self, ridtuple):
        if 'recentviews' not in self.data:
            self.data['recentviews'] = []
        if ridtuple[0] not in [t[0] for t in self.data['recentviews']]:
            self.data['recentviews'].insert(0, ridtuple)
        if len(self.data['recentviews']) > 100:
            del self.data['recentviews'][100]
        self.save()

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return auth.user.is_super(self)

    @property
    def email(self):
        return self.data['email']

    def collections(self, sort={"slug.exact":{"order":"asc"}}, **kwargs):
        return [Collection.get(i['_source']['_id']) for i in Collection.query(terms={'owner':self.id},**kwargs).get('hits',{}).get('hits',[])]
    
    def __len__(self):
        return Collection.query(terms={'owner':self.id}).get('hits',{}).get('total',0)

    def delete(self):
        r = requests.delete( self.target() + self.id )
        count = 0
        while count < len(self):
            for coll in self.collections(_from=count,size=100):
                coll.delete()
            count += 100
'''

# This could be used with account signup approval processes to store accounts that have been 
# created but not yet approved via email confirmation.
'''class UnapprovedAccount(Account):
    __type__ = 'unapprovedaccount'
    
    def requestvalidation(self):
        # send an email to account email address and await response, unless in debug mode
        # validate link is like http://siteaddr.net/username?validate=key
        msg = "Hello " + self.id + "\n\n"
        msg += "Thanks for signing up with " + app.config['SERVICE_NAME'] + "\n\n"
        msg += "In order to validate and enable your account, please follow the link below:\n\n"
        msg += app.config['SITE_URL'] + "/" + self.id + "?validate=" + self.data['validate_key'] + "\n\n"
        msg += "Thanks! We hope you enjoy using " + app.config['SERVICE_NAME']
        if not app.config['DEBUG']:
            util.send_mail([self.data['email']], app.config['EMAIL_FROM'], 'validate your account', msg)
        
    def validate(self,key):
        # accept validation and create new account
        if key == self.data['validate_key']:
            del self.data['validate_key']
            account = Account(**self.data)
            account.save()
            self.delete()
            return account
        else:
            return None
'''
            
            

