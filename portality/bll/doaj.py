# ~~DOAJ:Service~~
class DOAJ(object):
    """
    Primary entry point to the services which back up the DOAJ Business Logic Layer.
    This is, in effect, a factory for generating the services for the various areas
    of the DOAJ.

    To use it, request the service or services for the area that you are working with, and then
    call functions on the resulting service object.  For example:

    applicationService = DOAJ.applicationService()
    applicationService.application_2_journal(....)
    """

    @classmethod
    def applicationService(cls):
        """
        Obtain an instance of the application service ~~->Application:Service~~

        :return: ApplicationService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import application
        return application.ApplicationService()

    @classmethod
    def journalService(cls):
        """
        Obtain an instance of the journal service ~~->Journal:Service~~

        :return: JournalService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import journal
        return journal.JournalService()

    @classmethod
    def authorisationService(cls):
        """
        Obtain an instance of the authorisation service ~~->AuthNZ:Service~~

        :return: AuthorisationService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import authorisation
        return authorisation.AuthorisationService()

    @classmethod
    def queryService(cls):
        """
        Obtain an instance of the query service ~~->Query:Service~~

        :return: QueryService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import query
        return query.QueryService()

    @classmethod
    def articleService(cls):
        """
        Obtain an instance of the article service   ~~->Article:Service~~

        :return: ArticleService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import article
        return article.ArticleService()

    @classmethod
    def siteService(cls):
        """
        Obtain an instance of the site service  ~~->Site:Service~~
        :return:  SiteService
        """
        from portality.bll.services import site
        return site.SiteService()

    @classmethod
    def eventsService(cls):
        """
        Obtain an instance of the events service
        :return:  SiteService
        """
        from portality.bll.services import events
        return events.EventsService()

    @classmethod
    def notificationsService(cls):
        """
        Obtain an instance of the notifications service ~~->Notifications:Service~~
        :return: NotificationsService
        """
        from portality.bll.services import notifications
        return notifications.NotificationsService()

    @classmethod
    def todoService(cls):
        """
        Obtain an instance of the todo service  ~~->Todo:Service~~
        :return:  SiteService
        """
        from portality.bll.services import todo
        return todo.TodoService()

    @classmethod
    def backgroundTaskStatusService(cls):
        """
        Obtain an instance of the background_task_status service
        ~~->BackgroundTask:Monitoring~~
        :return:  BackgroundTaskStatusService
        """
        from portality.bll.services import background_task_status
        return background_task_status.BackgroundTaskStatusService()

    @classmethod
    def tourService(cls):
        """
        Obtain an instance of the tour service  ~~->Tour:Service~~
        :return:  SiteService
        """
        from portality.bll.services import tour
        return tour.TourService()

    @classmethod
    def autochecksService(cls, autocheck_plugins=None):
        from portality.bll.services import autochecks
        return autochecks.AutocheckService(autocheck_plugins=autocheck_plugins)

    @classmethod
    def urlshortService(cls):
        from portality.bll.services import urlshort
        return urlshort
