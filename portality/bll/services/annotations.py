from portality.crosswalks.application_form import ApplicationFormXWalk, JournalFormXWalk
from portality.annotation.resource_bundle import ResourceBundle
from portality import models

from portality.annotation.annotators.issn_active import ISSNActive

ANNOTATION_PLUGINS = [
    # (journal, application, plugin)
    (True, True, ISSNActive)
]

class AnnotationsService(object):
    """
    ~~Annotations:Service->DOAJ:Service~~
    """

    def __init__(self, annotation_plugins=None):
        self._annotation_plugins = annotation_plugins if annotation_plugins is not None else ANNOTATION_PLUGINS

    def annotate_application(self, application: models.Application, logger=None):
        if logger is None:
            logger = lambda x: x    # does nothing, just swallows the logs

        application_form = ApplicationFormXWalk.obj2form(application)
        resource_bundle = ResourceBundle()
        new_annotations = models.Annotation()
        new_annotations.application = application.id

        for j, a, anno in self._annotation_plugins:
            if not a:
                continue

            annotator = anno()
            logger("Running annotation plugin {x}".format(x=annotator.name()))
            annotator.annotate(application_form, application, new_annotations, resource_bundle, logger)

        new_annotations.save()
        logger("Saved new annotation document {id}".format(id=new_annotations.id))

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