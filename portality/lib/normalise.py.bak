import urlparse
from portality import regex

def normalise_url(url):
    """
    Take a URL and turn it into a form which is suitable for normalised comparison with other normalised
    URLs.

    The function does the following:
    * strips leading/trailing whitespace
    * validates the URL is realistic
    * strips the scheme (so, removes http, https, ftp, ftps, etc)

    :param url:
    :return:
    """
    if url is None:
        return url

    schemes = ["http", "https", "ftp", "ftps"]
    url = url.strip()
    if url.startswith("//"):
        url = "http:" + url

    if "://" not in url:
        url = "http://" + url

    u = urlparse.urlparse(url)

    if u.netloc is None or u.netloc == "":
        raise ValueError("Could not extract a normalised URL from '{x}'".format(x=url))

    if u.scheme not in schemes:
        raise ValueError("URL must be at http(s) or ftp(s), found '{x}'".format(x=u.netloc))

    n = urlparse.ParseResult(None, u.netloc, u.path, u.params, u.query, u.fragment)
    return urlparse.urlunparse(n)


def normalise_doi(doi):
    """
    Take a DOI and turn it into a form which is suitable for normalised comparison with other normalised
    DOIs.

    The function does the following:
    * strips leading/trailing whitespace
    * validates that the DOI meets the regex
    * extracts only the 10.xxxx portion

    :param doi:
    :return:
    """
    if doi is None:
        return None
    doi = doi.strip()
    norm = regex.group_match(regex.DOI_COMPILED, doi, "id")
    if norm is None:
        raise ValueError("Could not extract a normalised DOI from '{x}'".format(x=doi))
    return norm
