from copy import deepcopy

from portality.lib import swagger
from portality.lib.seamless import SeamlessMixin

from portality.models.v2.shared_structs import JOURNAL_BIBJSON
_SHARED_STRUCT = JOURNAL_BIBJSON

class OutgoingCommonJournalApplication(SeamlessMixin, swagger.SwaggerSupport):
    """
    ~~APIOutgoingCommonJournalApplication:Model->Seamless:Library~~
    """
    @classmethod
    def from_model(cls, journal_or_app):
        d = deepcopy(journal_or_app.data)
        # Prevent the field from appearing in the outgoing API models
        if d["bibjson"]["oa_start"]:
            del d["bibjson"]["oa_start"]
        return cls(d)
