from copy import deepcopy

from portality.lib import swagger
from portality.lib.seamless import SeamlessMixin


class OutgoingCommonJournalApplication(SeamlessMixin, swagger.SwaggerSupport):

    # def __init__(self, raw=None, struct=None):
    #     super(OutgoingCommonJournalApplication, self).__init__(raw, struct=struct)

    @classmethod
    def from_model(cls, journal_or_app):
        d = deepcopy(journal_or_app.data)
        return cls(d)
