import urlparse
from portality import regex

def normalise_url(url):
    if url is None:
        return url
    url = url.strip()
    u = urlparse.urlparse(url)
    if u.netloc is None or u.netloc == "":
        raise ValueError("Could not extract a normalised URL from {x}".format(x=url))
    n = urlparse.ParseResult(None, u.netloc, u.path, u.params, u.query, u.fragment)
    return urlparse.urlunparse(n)


def normalise_doi(doi):
    if doi is None:
        return None
    doi = doi.strip()
    norm = regex.group_match(regex.DOI_COMPILED, doi, "id")
    if norm is None:
        raise ValueError("Could not extract a normalised DOI from {x}".format(x=doi))
    return norm