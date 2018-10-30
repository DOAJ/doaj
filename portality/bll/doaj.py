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
        Obtain an instance of the application service

        :return: ApplicationService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import application
        return application.ApplicationService()

    @classmethod
    def journalService(cls):
        """
        Obtain an instance of the journal service

        :return: JournalService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import journal
        return journal.JournalService()

    @classmethod
    def authorisationService(cls):
        """
        Obtain an instance of the authorisation service

        :return: AuthorisationService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import authorisation
        return authorisation.AuthorisationService()

    @classmethod
    def queryService(cls):
        """
        Obtain an instance of the query service

        :return: QueryService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import query
        return query.QueryService()

    @classmethod
    def articleService(cls):
        """
        Obtain an instance of the article service

        :return: ArticleService
        """
        # Note the use of delayed imports to minimise code pre-loading, and to allow services loaded
        # via this factory to also use the factory to load other services.
        from portality.bll.services import article
        return article.ArticleService()

