from portality.crosswalks.application_form import ApplicationFormXWalk, JournalFormXWalk
from portality.autocheck.resource_bundle import ResourceBundle
from portality import models

from portality.autocheck.checkers.issn_active import ISSNActive
from portality.autocheck.checkers.keepers_registry import KeepersRegistry
from portality.autocheck.checkers.publication_time import PublicationTime

AUTOCHECK_PLUGINS = [
    # (Active on Journal?, Active on Application?, Plugin Class)
    (True, True, ISSNActive),
    (True, True, KeepersRegistry),
    (True, True, PublicationTime)

]


class AutocheckService(object):
    """
    ~~Autochecks:Service->DOAJ:Service~~
    """

    def __init__(self, autocheck_plugins=None):
        self._autocheck_plugins = autocheck_plugins if autocheck_plugins is not None else AUTOCHECK_PLUGINS

    def autocheck_applications(self, application_ids=None, logger=None):
        """
        ~~Autochecks:Service->DOAJ:Service~~
        """
        resource_bundle = ResourceBundle()
        if application_ids is None:
            for application in models.Application.iterate():
                self.autocheck_application(application, logger=logger, resource_bundle=resource_bundle)
        else:
            for application_id in application_ids:
                application = models.Application.pull(application_id)
                if application is None:
                    continue
                self.autocheck_application(application, logger=logger, resource_bundle=resource_bundle)

    def autocheck_application(self, application: models.Application, created_date=None, logger=None, resource_bundle=None):
        if logger is None:
            logger = lambda x: x    # does nothing, just swallows the logs

        if resource_bundle is None:
            resource_bundle = ResourceBundle()

        application_form = ApplicationFormXWalk.obj2form(application)
        new_autochecks = models.Autocheck()
        new_autochecks.application = application.id

        if created_date is not None:
            new_autochecks.set_created(created_date)

        for j, a, klazz in self._autocheck_plugins:
            if not a:
                continue

            checker = klazz()
            logger("Running autocheck plugin {x}".format(x=checker.name()))
            checker.check(application_form, application, new_autochecks, resource_bundle, logger)

        new_autochecks.save()
        logger("Saved new autocheck document {id}".format(id=new_autochecks.id))

        models.Autocheck.delete_all_but_latest(application_id=application.id)

        return new_autochecks

    def autocheck_journals(self, journal_ids=None, logger=None):
        """
        ~~autochecks:Service->DOAJ:Service~~
        """
        resource_bundle = ResourceBundle()
        if journal_ids is None:
            for journal in models.Journal.iterate():
                self.autocheck_journal(journal, logger=logger, resource_bundle=resource_bundle)
        else:
            for journal_id in journal_ids:
                journal = models.Journal.pull(journal_id)
                if journal is None:
                    continue
                self.autocheck_journal(journal, logger=logger, resource_bundle=resource_bundle)

    def autocheck_journal(self, journal: models.Journal, logger=None, resource_bundle=None):
        if logger is None:
            logger = lambda x: x  # does nothing, just swallows the logs

        if resource_bundle is None:
            resource_bundle = ResourceBundle()

        journal_form = JournalFormXWalk.obj2form(journal)
        new_autochecks = models.Autocheck()
        new_autochecks.journal = journal.id

        for j, a, klazz in self._autocheck_plugins:
            if not j:
                continue

            checker = klazz()
            logger("Running autocheck plugin {x}".format(x=checker.name()))
            checker.check(journal_form, journal, new_autochecks, resource_bundle, logger)

        new_autochecks.save()
        logger("Saved new autocheck document {id}".format(id=new_autochecks.id))

        models.Autocheck.delete_all_but_latest(journal_id=journal.id)

        return new_autochecks

    def dismiss(self, autocheck_set_id, autocheck_id):
        autochecks = models.Autocheck.pull(autocheck_set_id)
        if autochecks is None:
            return False
        autochecks.dismiss(autocheck_id)
        autochecks.save()
        return True

    def undismiss(self, autocheck_set_id, autocheck_id):
        autochecks = models.Autocheck.pull(autocheck_set_id)
        if autochecks is None:
            return False
        autochecks.undismiss(autocheck_id)
        autochecks.save()
        return True