from portality.crosswalks.application_form import ApplicationFormXWalk, JournalFormXWalk
from portality.autocheck.resource_bundle import ResourceBundle
from portality import models

from portality.autocheck.checkers.issn_active import ISSNActive
from portality.autocheck.checkers.keepers_registry import KeepersRegistry

AUTOCHECK_PLUGINS = [
    # (journal, application, plugin)
    (True, True, ISSNActive),
    (True, True, KeepersRegistry)
]


class AutocheckService(object):
    """
    ~~Autochecks:Service->DOAJ:Service~~
    """

    def __init__(self, autocheck_plugins=None):
        self._autocheck_plugins = autocheck_plugins if autocheck_plugins is not None else AUTOCHECK_PLUGINS

    def autocheck_applications(self, application_ids=None):
        """
        ~~Autochecks:Service->DOAJ:Service~~
        """
        if application_ids is None:
            for application in models.Application.iterate():
                self.autocheck_application(application)
        else:
            for application_id in application_ids:
                application = models.Application.pull(application_id)
                if application is None:
                    continue
                self.autocheck_application(application)

    def autocheck_application(self, application: models.Application, created_date=None, logger=None):
        if logger is None:
            logger = lambda x: x    # does nothing, just swallows the logs

        application_form = ApplicationFormXWalk.obj2form(application)
        resource_bundle = ResourceBundle()
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

    def autocheck_journals(self, journal_ids=None):
        """
        ~~autochecks:Service->DOAJ:Service~~
        """
        if journal_ids is None:
            for journal in models.Journal.iterate():
                self.autocheck_journal(journal)
        else:
            for journal_id in journal_ids:
                journal = models.Journal.pull(journal_id)
                if journal is None:
                    continue
                self.autocheck_journal(journal)

    def autocheck_journal(self, journal: models.Journal, logger=None):
        if logger is None:
            logger = lambda x: x  # does nothing, just swallows the logs

        journal_form = JournalFormXWalk.obj2form(journal)
        resource_bundle = ResourceBundle()
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