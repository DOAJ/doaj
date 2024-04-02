import re

#~~DOI:Regex~~
DOI = r"^((https?://)?((dx\.)?doi\.org/|hdl\.handle\.net/)|doi:|info:doi/|info:hdl/)?(?P<id>10\.\S+/\S+)$"
DOI_COMPILED = re.compile(DOI, re.IGNORECASE)

#~~ORCID:Regex~~
ORCID = r"^https://orcid\.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-\d{3}[\dX]$"
ORCID_COMPILED = re.compile(ORCID)

#~~ISSN:Regex~~
ISSN = r'^\d{4}-\d{3}(\d|X|x){1}$'
ISSN_COMPILED = re.compile(ISSN)

#~~Date:Regex~~
BIG_END_DATE = r'^\d{4}-\d{2}-\d{2}$'
BIG_END_DATE_COMPILED = re.compile(BIG_END_DATE)

#~~URL:Regex~~
HTTP_URL = (
    r'^(?:https?)://'     # Scheme: http(s) or ftp
    r'(?:[\w-]+\.)*[\w-]+'    # Domain name (optional subdomains)
    r'(?:\.[a-z]{2,})'        # Top-level domain (e.g., .com, .org)
    r'(?:\:(0|6[0-5][0-5][0-3][0-5]|[1-5][0-9][0-9][0-9][0-9]|[1-9][0-9]{0,3}))?'   # port (0-65535) preceded with `:`
    r'(?:\/[^\/\s]*)*'        # Path (optional)
    r'(?:\?[^\/\s]*)?'        # Query string (optional)
    r'(?:#[^\/\s]*)?$'        # Fragment (optional)
)

HTTP_URL_COMPILED = re.compile(HTTP_URL, re.IGNORECASE)


def is_match(pattern, string, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    return match is not None


def group_match(pattern, string, name, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    if match is None:
        return None
    return match.group(name)
