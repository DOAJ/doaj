from portality.api.v2 import ArticlesCrudApi
from portality.core import app
from portality.lib import plugin, dates
from portality.models import Journal, Account
from portality.models.harvester import HarvesterProgressReport as Report
from portality.models.harvester import HarvestState
from portality.lib.dataobj import DataObjException


class DefaultLogger(object):
    def __init__(self):
        self._log = []

    def log(self, msg):
        self._log.append({
            "timestamp": dates.now_with_microseconds(),
            "message" : msg
        })


class HarvesterWorkflow(object):

    def __init__(self, custom_logger=None):
        self.logger = DefaultLogger() if custom_logger is None else custom_logger

    def _write_to_logger(self, msg):
        self.logger.log(msg)

    def process_account(self, account_id):
        self._write_to_logger("Harvesting for Account:{x}".format(x=account_id))
        issns = self.get_journals_issns(account_id)
        self._write_to_logger("Account:{x} has {y} issns to harvest for: {z}".format(x=account_id, y=len(issns), z=",".join(issns)))

        # now update the issn states
        self.process_issn_states(account_id, issns)

        for issn in issns:
            self.process_issn(account_id, issn)

    def get_journals_issns(self, account_id):
        return Journal.issns_by_owner(account_id, in_doaj=True)

    def process_issn_states(self, account_id, issns):
        # first check that there are state records for all the provided issns,
        # and that if they were deactivated they are now reactivated
        for issn in issns:
            state = HarvestState.find_by_issn(account_id, issn)
            if state is not None:
                if state.suspended:
                    state.reactivate()
                    state.save(blocking=True)
            else:
                state = HarvestState()
                state.issn = issn
                state.account = account_id
                state.save(blocking=True)

        # now check if there are are any other issns for this account that we haven't
        # been provided - in that case they need to be deactivated
        hss = [hs for hs in HarvestState.find_by_account(account_id)]    # read straight away, as the iterator can timeout
        for hs in hss:
            if hs.issn not in issns and not hs.suspended:
                hs.suspend()
                hs.save(blocking=True)

    def process_issn(self, account_id, issn):
        self._write_to_logger("Processing ISSN:{x} for Account:{y}".format(y=account_id, x=issn))

        state = HarvestState.find_by_issn(account_id, issn)
        # if this issn is suspended, don't process it
        if state.suspended:
            return
        Report.set_state_by_issn(issn, state)

        try:
            # get all the plugins that we need to run
            harvesters = app.config.get("HARVESTERS", [])
            for h in harvesters:
                p = plugin.load_class(h)()
                p_name = p.get_name()
                lh = state.get_last_harvest(p_name)
                if lh is None:
                    lh = app.config.get("INITIAL_HARVEST_DATE")
                Report.set_start_by_issn(p_name, issn, lh)

                for article, lhd in p.iterate(issn, lh):
                    saved = self.process_article(account_id, article)
                    Report.increment_articles_processed(p_name)

                    # if the above worked, then we can update the harvest state
                    if saved:
                        state.set_harvested(p_name, lhd)
                        Report.increment_articles_saved_successfully(p_name)

                self._write_to_logger(p.logger)
        except Exception:
            self._write_to_logger("Exception Processing ISSN:{x} for Account:{y} ".format(y=account_id, x=issn))
            raise
        finally:
            # once we've finished working with this issn, we should update the state
            # this is especially true if there is an exception, as this will allow us
            # to record where we got to, without having to do a save after each article
            # create
            state.save(blocking=True)
            self._write_to_logger("Saved state record for ISSN:{x} for Account:{y}".format(y=account_id, x=issn))

    def process_article(self, account_id, article):
        self._write_to_logger("Processing Article for Account:{y}".format(y=account_id))

        try:
            article.is_api_valid()
        except DataObjException as e:
            self._write_to_logger("Article for Account:{y} was not API valid ... skipping".format(y=account_id))
            Report.record_error((article.get_identifier("doi") or "< DOI MISSING >") + " - " + str(e))
            return False

        # FIXME: in production, we will need a way to get the account_id's api_key
        # but in this version we just need to have a list of the api keys that we're
        # working with
        # if this throws an exception other than DOAJ complaint, allow the harvester to die, because it is either
        # systemic or the doaj is down.
        acc = Account.pull(account_id)
        try:
            id = ArticlesCrudApi.create(article.data, acc).id
        except Exception as e:
            self._write_to_logger("Article caused DOAJException: {m} ... skipping".format(m=e))
            Report.record_error((article.get_identifier("doi") or "< DOI MISSING >"))
            return False
        self._write_to_logger("Created article in DOAJ for Account:{x} with ID: {y}".format(x=account_id, y=id))
        return True
