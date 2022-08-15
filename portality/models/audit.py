import datetime

from portality.dao import DomainObject


class Audit(DomainObject):
    __type__ = "audit"

    @classmethod
    def create(cls,
               who: dict,
               what: dict,
               created_at: datetime.datetime = None):
        created_at = created_at or datetime.datetime.now()

        raw = {
            'when': created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'who': who,
            'what': what,
        }
        return Audit(**raw)
