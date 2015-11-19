from portality.api.v1.common import Api404Error, Api400Error, Api403Error
from portality.api.v1.crud import ApplicationsCrudApi

class ApplicationsBulkApi(object):

    @classmethod
    def create(cls, applications, account):
        # we run through create twice, once as a dry-run and the second time
        # as the real deal
        for a in applications:
            ApplicationsCrudApi.create(a, account, dry_run=True)

        ids = []
        for a in applications:
            n = ApplicationsCrudApi.create(a, account)
            ids.append(n.id)

        return ids

    @classmethod
    def delete(cls, application_ids, account):
        # we run through create twice, once as a dry-run and the second time
        # as the real deal
        for id in application_ids:
            try:
                ApplicationsCrudApi.delete(id, account, dry_run=True)
            except Api404Error as e:
                raise Api400Error("Id {x} does not exist or does not belong to this user account".format(x=id))
            except Api403Error as e:
                raise Api400Error("Id {x} is not in a state which allows it to be deleted".format(x=id))

        for id in application_ids:
            ApplicationsCrudApi.delete(id, account)