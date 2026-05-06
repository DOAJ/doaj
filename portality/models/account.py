import uuid
from flask_login import UserMixin
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from portality import constants
from portality.dao import DomainObject as DomainObject
from portality.core import app
from portality.authorise import Authorise
from portality.lib import dates
from portality.lib.dates import FMT_DATETIME_STD

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    def __init__(self, **kwargs):
        from portality.forms.validate import ReservedUsernames
        ReservedUsernames().validate(kwargs.get('id', ''))
        super(Account, self).__init__(**kwargs)

    @classmethod
    def make_account(cls, email, username=None, name=None, roles=None, associated_journal_ids=None, attributes:dict[str, list]=None):
        if roles is None:
            roles = []

        if associated_journal_ids is None:
            associated_journal_ids = []

        # If we have an existing account with these credentials, supply it
        a = cls.pull(username) or cls.pull_by_email(email)
        if a:
            return a

        # Create a new account
        _id = username or cls.new_short_uuid()
        a = Account(id=_id)
        a.set_email(email)
        a.set_name(name) if name else None

        for role in roles:
            a.add_role(role)

        for jid in associated_journal_ids:
            a.add_journal(jid)

        if attributes is not None:
            for attr_type, value in attributes.items():
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    a.add_attribute(attr_type, v)

        # New accounts don't have passwords set - create a reset token for password.
        reset_token = uuid.uuid4().hex
        # give them 14 days to create their first password if timeout not specified in config
        a.set_reset_token(reset_token, app.config.get("PASSWORD_CREATE_TIMEOUT",
                                                      app.config.get('PASSWORD_RESET_TIMEOUT', 86400) * 14))
        return a

    @classmethod
    def pull_by_email(cls, email: str):
        if email is None:
            return None
        res = cls.query(q='email:"' + email + '"')
        if res.get('hits', {}).get('total', {}).get('value', 0) == 1:
            acc = cls(**res['hits']['hits'][0]['_source'])
            if acc.email.lower() == email.lower():  # allow case insensitive login
                return acc
        return None

    @classmethod
    def email_in_use(cls, email: str):
        if email is None:
            return None
        res = cls.query(q='email:"' + email + '"')
        return res.get('hits', {}).get('total', {}).get('value', 0) > 0

    @classmethod
    def get_by_reset_token(cls, reset_token, not_expired=True):
        res = cls.query(q='reset_token.exact:"' + reset_token + '"')
        obs = [hit.get("_source") for hit in res.get("hits", {}).get("hits", [])]
        if len(obs) == 0 or len(obs) > 1:
            return None
        expires = obs[0].get("reset_expires")
        if expires is None:
            return None
        if not_expired:
            try:
                ed = dates.parse(expires)
                if ed < dates.now():
                    return None
            except ValueError:
                return None
        return cls(**obs[0])

    # @classmethod
    # def autocomplete(cls, field, prefix, admin_only=False, size=5):
    #
    #     return {"suggestions": super().autocomplete(field, prefix, filter_condition=filter_condition, size=size)}

    @classmethod
    def admin_autocomplete(cls, field, prefix, size=5):
        """Autocomplete for admin users only."""
        filter_condition = {"role.exact": "admin"}
        return cls.autocomplete(field, prefix, filter_condition=filter_condition, size=size)

    @property
    def marketing_consent(self):
        return self.data.get("marketing_consent")

    def set_marketing_consent(self, consent):
        self.data["marketing_consent"] = bool(consent)

    @property
    def name(self):
        return self.data.get("name")

    def set_name(self, name):
        self.data["name"] = name

    @property
    def email(self):
        return self.data.get("email")

    def set_email(self, email):
        self.data["email"] = email

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def set_password_hash(self, hash):
        self.data['password'] = hash

    def clear_password(self):
        if self.data.get('password'):
            del self.data['password']

    def check_password(self, password):
        try:
            return check_password_hash(self.data['password'], password)
        except KeyError:
            app.logger.error("Problem with user '{}' account: no password field".format(self.data['id']))
            raise

    @property
    def journal(self):
        return self.data.get("journal")

    def add_journal(self, jid):
        if jid in self.data.get("journal", []):
            return
        if "journal" not in self.data:
            self.data["journal"] = []
        if jid not in self.data["journal"]:
            self.data["journal"].append(jid)

    def remove_journal(self, jid):
        if "journal" not in self.data:
            return
        self.data["journal"].remove(jid)

    @property
    def reset_token(self):
        return self.data.get('reset_token')

    def set_reset_token(self, token, timeout):
        expires = dates.now() + timedelta(0, timeout)
        self.data["reset_token"] = token
        self.data["reset_expires"] = expires.strftime(FMT_DATETIME_STD)

    def remove_reset_token(self):
        if "reset_token" in self.data:
            del self.data["reset_token"]
        if "reset_expires" in self.data:
            del self.data["reset_expires"]

    @property
    def reset_expires(self):
        return self.data.get("reset_expires")

    @property
    def reset_expires_timestamp(self):
        expires = self.reset_expires
        if expires is None:
            return None
        return dates.parse(expires)

    def is_reset_expired(self):
        expires = self.reset_expires_timestamp
        if expires is None:
            return True
        return expires < dates.now()

    @property
    def is_super(self):
        # return not self.is_anonymous and self.id in app.config['SUPER_USER']
        return Authorise.has_role(app.config["SUPER_USER_ROLE"], self.data.get("role", []))

    def has_role(self, role):
        return Authorise.has_role(role, self.data.get("role", []))

    @classmethod
    def all_top_level_roles(cls):
        return Authorise.top_level_roles()

    def add_role(self, role):
        if "role" not in self.data:
            self.data["role"] = []
        if role not in self.data["role"]:
            self.data["role"].append(role)
        # If we're adding the API role, ensure we also have a key to validate
        if role == 'api' and not self.data.get('api_key', None):
            self.generate_api_key()

    def remove_role(self, role):
        if "role" not in self.data:
            return
        if role in self.data["role"]:
            self.data["role"].remove(role)

    @property
    def role(self):
        return self.data.get("role", [])

    def set_role(self, role):
        if not isinstance(role, list):
            role = [role]
        self.data["role"] = role

    ###############################
    ## user attributes

    @property
    def attributes(self):
        return self.data.get("attributes")

    @attributes.deleter
    def attributes(self):
        if "attributes" in self.data:
            del self.data["attributes"]

    @property
    def attribute_workflow(self):
        return self.data.get("attributes", {}).get(constants.USER_ATTR__WORKFLOW, [])

    @property
    def attribute_language(self):
        return self.data.get("attributes", {}).get(constants.USER_ATTR__LANGUAGE, [])

    @property
    def attribute_country(self):
        return self.data.get("attributes", {}).get(constants.USER_ATTR__COUNTRY, [])

    @property
    def attribute_tag(self):
        return self.data.get("attributes", {}).get(constants.USER_ATTR__TAG, [])

    def add_attribute(self, attribute_type, value):
        if attribute_type not in constants.USER_ATTR__ALL:
            raise ValueError("Unknown user attribute type: {}".format(attribute_type))
        if "attributes" not in self.data:
            self.data["attributes"] = {}
        if attribute_type not in self.data["attributes"]:
            self.data["attributes"][attribute_type] = []
        if value not in self.data["attributes"][attribute_type]:
            self.data["attributes"][attribute_type].append(value)

    def has_attribute(self, attribute_type, value):
        if attribute_type not in constants.USER_ATTR__ALL:
            raise ValueError("Unknown user attribute type: {}".format(attribute_type))
        return value in self.data.get("attributes", {}).get(attribute_type, [])

    def get_attributes(self, attribute_type):
        if attribute_type not in constants.USER_ATTR__ALL:
            raise ValueError("Unknown user attribute type: {}".format(attribute_type))
        return self.data.get("attributes", {}).get(attribute_type, [])

    #######################

    def prep(self):
        self.data['last_updated'] = dates.now_str()

    @property
    def api_key(self):
        if self.has_role('api'):
            return self.data.get('api_key', None)
        else:
            return None

    def generate_api_key(self):
        k = uuid.uuid4().hex
        self.data['api_key'] = k
        return k

    @property
    def is_premium(self):
        return (self.has_role(constants.ROLE_PREMIUM) or
                self.has_role(constants.ROLE_PREMIUM_OAI) or
                self.has_role(constants.ROLE_PREMIUM_PDD) or
                self.has_role(constants.ROLE_PREMIUM_CSV))

    @classmethod
    def pull_by_api_key(cls, key):
        """Find a user by their API key - only succeed if they currently have API access."""
        res = cls.query(q='api_key.exact:"' + key + '"')
        if res.get('hits', {}).get('total', {}).get('value', 0) == 1:
            usr = cls(**res['hits']['hits'][0]['_source'])
            if usr.has_role('api'):
                return usr
        return None

    @classmethod
    def new_short_uuid(cls):
        """ Generate a short UUID and check it's unique in this type """
        trunc_uuid = str(uuid.uuid4())[:8]
        if cls.pull(trunc_uuid) is None:
            return trunc_uuid
        else:
            return cls.new_short_uuid()

    @classmethod
    def get_name_safe(cls, account_id) -> str:
        if account_id:
            author = Account.pull(account_id)
            if author is not None and author.name:
                return author.name
        return ''

    @classmethod
    def is_enable_publisher_email(cls) -> bool:
        # TODO: in the long run this needs to move out to the user's email preferences but for now it
        # is here to replicate the behaviour in the code it replaces
        return app.config.get("ENABLE_PUBLISHER_EMAIL", False)

    @classmethod
    def find_by_attributes(cls, attribute_types_and_values:list[tuple[str, str]], limit=1000):
        q = AttributesQuery(attribute_types_and_values, limit)
        return cls.object_query(q.query())


class AttributesQuery:
    def __init__(self, attribute_types_and_values, page_size):
        self._tup = attribute_types_and_values
        self._size = page_size

    def query(self):
        musts = []
        for t, v in self._tup.items():
            if not isinstance(v, list):
                v = [v]
            f = {"terms": {f"attribute.{t}.exact": v}}
            musts.append(f)

        q = {
            "query": {
                "bool": {
                    "must": musts
                }
            },
            "size": self._size
        }
        return q
