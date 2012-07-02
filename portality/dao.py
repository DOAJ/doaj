import json, UserDict, requests, uuid
from datetime import datetime
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from portality.core import app, current_user
import portality.util, portality.auth


def makeid():
    '''Create a new id for data object based on the idgen utility
    customise this if specific ID types are required'''
    return uuid.uuid4().hex
    
    
def initialise():
    # may need to PUT the indices first
    mappings = app.config['MAPPINGS']
    for mapping in mappings:
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/')
        t += '/' + app.config['ELASTIC_SEARCH_DB'] + '/' + mapping + '/_mapping'
        r = requests.get(t)
        if r.status_code == 404:
            r = requests.put(t, data=json.dumps(mappings[mapping]) )
            print r.text


class InvalidDAOIDException(Exception):
    pass
    
    
class DomainObject(UserDict.IterableUserDict):
    __type__ = None

    def __init__(self, **kwargs):
        if '_source' in kwargs:
            self.data = dict(kwargs['_source'])
            self.meta = dict(kwargs)
            del self.meta['_source']
        else:
            self.data = dict(kwargs)
            
    @classmethod
    def target(cls):
        t = 'http://' + str(app.config['ELASTIC_SEARCH_HOST']).lstrip('http://').rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/' + cls.__type__ + '/'
        return t
    
    @property
    def id(self):
        return self.data.get('id', None)
        
    @property
    def version(self):
        return self.meta.get('_version', None)

    @property
    def json(self):
        return json.dumps(self.data)

    def save(self):
        if 'id' in self.data:
            id_ = self.data['id'].strip()
        else:
            id_ = makeid()
            self.data['id'] = id_
        
        self.data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H%M")

        if 'created_date' not in self.data:
            self.data['created_date'] = datetime.now().strftime("%Y-%m-%d %H%M")

        if 'history' not in self.data:
            self.data['history'] = []
        previous = Record.pull(self.data['id'])
        if previous:
            for key,val in previous.items():
                if key not in ['history','access','last_updated']:
                    if val != data[key]:
                        data['history'].insert(0, {
                            'date': data['last_updated'],
                            'field': key,
                            'previous': val,
                            'current': data[key],
                            'user': get_user()
                        })
        
        r = requests.post(self.target() + self.data['id'], data=json.dumps(self.data))

    @classmethod
    def pull(cls, id_):
        '''Retrieve object by id.'''
        if id_ is None:
            return None
        try:
            out = requests.get(cls.target() + id_)
            if out.status_code == 404:
                return None
            else:
                return cls(**out.json)
        except:
            return None

    @classmethod
    def mapping(cls):
        r = requests.get(cls.target() + '_mapping')
        return r.json
        
    @classmethod
    def keys(cls,mapping=False,prefix=''):
        # return a sorted list of all the keys in the index
        if not mapping:
            mapping = cls.mapping()[cls.__type__]['properties']
        keys = []
        for item in mapping:
            if mapping[item].has_key('fields'):
                for item in mapping[item]['fields'].keys():
                    if item != 'exact' and not item.startswith('_'):
                        keys.append(prefix + item + app.config['FACET_FIELD'])
            else:
                keys = keys + cls.keys(mapping=mapping[item]['properties'],prefix=prefix+item+'.')
        keys.sort()
        return keys
        
    @classmethod
    def query(cls, qs='q=*'):
        if isinstance(qs,dict):
            r = requests.post(cls.target() + '_search', data=json.dumps(qs))
        else:
            r = requests.get(cls.target() + '_search?' + qs)
        return r.json

    def accessed(self):
        if 'access' not in self.data:
            self.data['access'] = []
        self.data['access'].insert(0, { 'user':get_user(), 'date':datetime.now().strftime("%Y-%m-%d %H%M") } )        
        r = requests.put(self.target() + self.data['id'], data=json.dumps(self.data))

    def delete(self):        
        r = requests.delete(self.target() + self.id)


class Record(DomainObject):
    __type__ = 'record'
    
    
class Account(DomainObject, UserMixin):
    __type__ = 'account'

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def is_super(self):
        return portality.auth.user.is_super(self)
    

