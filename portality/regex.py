import re

DOI = r"^((https?://)?((dx\.)?doi\.org/|hdl\.handle\.net/)|doi:|info:doi/|info:hdl/)?(?P<id>10\.\S+/\S+)$"
DOI_COMPILED = re.compile(DOI, re.IGNORECASE)

def is_match(pattern, string, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    return match is not None

def group_match(pattern, string, name, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    if match is None:
        return None
    return match.group(name)
