from portality.api.v1.client import client as doajclient
from portality.core import app
from portality.lib import plugin
from portality.decorators import capture_sigterm
from portality.models.harvester import HarvesterProgressReport as Report
from portality.models.harvester import HarvestState
from portality.lib.dataobj import DataObjException

class HarvesterWorkflow(object):

    @classmethod
    @capture_sigterm
    def process_account(cls, account_id):
        app.logger.info("Harvesting for Account:{x}".format(x=account_id))

        doaj = doajclient.DOAJv1API()
        gen = doaj.field_search_iterator("journals", "username", account_id)
        issns = []
        for journal in gen:
            issns += journal.all_issns()
        issns = list(set(issns))

        app.logger.info("Account:{x} has {y} issns to harvest for: {z}".format(x=account_id, y=len(issns), z=",".join(issns)))

        # now update the issn states
        HarvesterWorkflow.process_issn_states(account_id, issns)

        for issn in issns:
            HarvesterWorkflow.process_issn(account_id, issn)

    @classmethod
    def process_issn_states(cls, account_id, issns):
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

    @classmethod
    @capture_sigterm
    def process_issn(cls, account_id, issn):
        app.logger.info("Processing ISSN:{x} for Account:{y}".format(y=account_id, x=issn))

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
                app.logger.info("Processing ISSN:{x} for Account:{y} with Plugin:{z} Since:{a}".format(y=account_id, x=issn, z=p_name, a=lh))
                Report.set_start_by_issn(p_name, issn, lh)

                for article, lhd in p.iterate(issn, lh):
                    saved = HarvesterWorkflow.process_article(account_id, article)
                    Report.increment_articles_processed(p_name)

                    # if the above worked, then we can update the harvest state
                    if saved:
                        state.set_harvested(p_name, lhd)
                        Report.increment_articles_saved_successfully(p_name)
        except Exception:
            app.logger.info("Exception Processing ISSN:{x} for Account:{y} ".format(y=account_id, x=issn))
            raise
        finally:
            # once we've finished working with this issn, we should update the state
            # this is especially true if there is an exception, as this will allow us
            # to record where we got to, without having to do a save after each article
            # create
            state.save(blocking=True)
            app.logger.info("Saved state record for ISSN:{x} for Account:{y}".format(y=account_id, x=issn))

    @classmethod
    def process_article(cls, account_id, article):
        app.logger.info("Processing Article for Account:{y}".format(y=account_id))

        try:
            article.is_api_valid()
        except DataObjException as e:
            app.logger.info("Article for Account:{y} was not API valid ... skipping".format(y=account_id))
            Report.record_error(article.get_identifier("doi") + " - " + e.message)
            return False

        # FIXME: in production, we will need a way to get the account_id's api_key
        # but in this version we just need to have a list of the api keys that we're
        # working with
        api_key = HarvesterWorkflow.get_api_key(account_id)
        doaj = doajclient.DOAJv1API(api_key=api_key)

        # if this throws an exception other than DOAJ complaint, allow the harvester to die, because it is either
        # systemic or the doaj is down.
        try:
            id, loc = doaj.create_article(article)
        except doajclient.DOAJException as e:
            app.logger.info("Article caused DOAJException: {m} ... skipping".format(m=e.message))
            Report.record_error(article.get_identifier("doi") + " - " + e.message)
            return False
        app.logger.info("Created article in DOAJ for Account:{x} with ID: {y}".format(x=account_id, y=id))
        return True

    @classmethod
    def get_api_key(cls, account_id):
        return app.config.get("HARVESTER_API_KEYS", {}).get(account_id)
