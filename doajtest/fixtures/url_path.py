URL_PUBLISHER = '/publisher'
URL_PUBLISHER_UPLOADFILE = f'{URL_PUBLISHER}/uploadfile'


def url_toc(identifier, volume=None, issue=None):
    url = f'/toc/{identifier}'
    if volume:
        url += f'/{volume}'
        if issue:
            url += f'/{issue}'
    return url
