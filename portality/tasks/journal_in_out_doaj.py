from huey import RedisHuey

from portality.core import app
from portality import models
from portality.decorators import write_required

huey = RedisHuey('doaj', host=app.config['HUEY_REDIS_HOST'], port=app.config['HUEY_REDIS_PORT'])


def journal_manage(journal_id, in_doaj_new_val):
    j = models.Journal.pull(journal_id)
    if j is None:
        raise RuntimeError("Journal with id {} does not exist".format(journal_id))
    j.bibjson().active = in_doaj_new_val
    j.set_in_doaj(in_doaj_new_val)
    j.save()
    j.propagate_in_doaj_status_to_articles()  # will save each article, could take a while


@huey.task()
@write_required(script=True)
def journal_activate(journal_id):
    return journal_manage(journal_id, True)


@huey.task()
@write_required(script=True)
def journal_deactivate(journal_id):
    return journal_manage(journal_id, False)
