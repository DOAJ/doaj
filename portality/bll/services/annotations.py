from portality.crosswalks.application_form import ApplicationFormXWalk, JournalFormXWalk
from portality.annotation.resource_bundle import ResourceBundle
from portality import models

from portality.annotation.annotators.issn_active import ISSNActive
from portality.annotation.annotators.keepers_registry import KeepersRegistry

ANNOTATION_PLUGINS = [
    # (journal, application, plugin)
    (True, True, ISSNActive),
    (True, True, KeepersRegistry)
]

class AnnotationsService(object):
    """
    ~~Annotations:Service->DOAJ:Service~~
    """

    def __init__(self, annotation_plugins=None):
        self._annotation_plugins = annotation_plugins if annotation_plugins is not None else ANNOTATION_PLUGINS

    def annotation_applications(self, application_ids=None):
        """
        ~~Annotations:Service->DOAJ:Service~~
        """
        if application_ids is None:
            for application in models.Application.iterate():
                self.annotate_application(application)
        else:
            for application_id in application_ids:
                application = models.Application.pull(application_id)
                if application is None:
                    continue
                self.annotate_application(application)

    def annotate_application(self, application: models.Application, created_date=None, logger=None):
        if logger is None:
            logger = lambda x: x    # does nothing, just swallows the logs

        application_form = ApplicationFormXWalk.obj2form(application)
        resource_bundle = ResourceBundle()
        new_annotations = models.Annotation()
        new_annotations.application = application.id

        if created_date is not None:
            new_annotations.set_created(created_date)

        for j, a, anno in self._annotation_plugins:
            if not a:
                continue

            annotator = anno()
            logger("Running annotation plugin {x}".format(x=annotator.name()))
            annotator.annotate(application_form, application, new_annotations, resource_bundle, logger)

        new_annotations.save()
        logger("Saved new annotation document {id}".format(id=new_annotations.id))

    def annotate_journals(self, journal_ids=None):
        """
        ~~Annotations:Service->DOAJ:Service~~
        """
        if journal_ids is None:
            for journal in models.Journal.iterate():
                self.annotate_journal(journal)
        else:
            for journal_id in journal_ids:
                journal = models.Journal.pull(journal_id)
                if journal is None:
                    continue
                self.annotate_journal(journal)

    def annotate_journal(self, journal: models.Journal, logger=None):
        if logger is None:
            logger = lambda x: x  # does nothing, just swallows the logs

        journal_form = JournalFormXWalk.obj2form(journal)
        resource_bundle = ResourceBundle()
        new_annotations = models.Annotation()
        new_annotations.journal = journal.id

        for j, a, anno in self._annotation_plugins:
            if not j:
                continue

            annotator = anno()
            logger("Running annotation plugin {x}".format(x=annotator.name()))
            annotator.annotate(journal_form, journal, new_annotations, resource_bundle, logger)

        new_annotations.save()
        logger("Saved new annotation document {id}".format(id=new_annotations.id))

    def dismiss(self, annotation_set_id, annotation_id):
        annotations = models.Annotation.pull(annotation_set_id)
        if annotations is None:
            return False
        annotations.dismiss(annotation_id)
        annotations.save()
        return True

    def undismiss(self, annotation_set_id, annotation_id):
        annotations = models.Annotation.pull(annotation_set_id)
        if annotations is None:
            return False
        annotations.undismiss(annotation_id)
        annotations.save()
        return True