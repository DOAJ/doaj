URL_PUBLISHER = '/publisher'
URL_PUBLISHER_UPLOADFILE = f'{URL_PUBLISHER}/uploadfile'
URL_ADMIN = '/admin'
URL_ADMIN_BGJOBS = URL_ADMIN + '/background_jobs'
URL_ACC = '/account'
URL_LOGOUT = URL_ACC + '/logout'


def url_toc(identifier, volume=None, issue=None):
    url = f'/toc/{identifier}'
    if volume:
        url += f'/{volume}'
        if issue:
            url += f'/{issue}'
    return url
