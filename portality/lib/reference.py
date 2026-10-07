"""
Helpers for rendering article references

~~Reference:Library~~
"""
import re

from markupsafe import Markup, escape

#~~Reference:Regex~~
# the URL for DOI
REFERENCE_LINK = r'(https?://(?:(?!,(?:doi:\s*)?10\.\d{4,9}/)[^\s<>"\'])+|(?:doi:\s*)?10\.\d{4,9}/[^\s<>"\']+)'
REFERENCE_LINK_COMPILED = re.compile(REFERENCE_LINK, re.IGNORECASE)
DOI_LABEL_PREFIX = re.compile(r'^doi:\s*', re.IGNORECASE)

# punctuation which may terminate a sentence, and is therefore not part of the link
TRAILING_PUNCTUATION = ".,;:)]"


def hyperlink_reference(reference):
    """
    Turn any URLs and DOIs found in a reference string into hyperlinks.  The reference
    text is escaped, so the result is safe to render as HTML.

    :param reference: the raw reference string
    :return: the escaped reference string with links applied
    """
    if not reference:
        return Markup("")

    parts = []
    position = 0
    for match in REFERENCE_LINK_COMPILED.finditer(reference):
        parts.append(escape(reference[position:match.start()]))
        position = match.end()

        token = match.group(0)
        trailing = ""
        while token and token[-1] in TRAILING_PUNCTUATION:
            trailing = token[-1] + trailing
            token = token[:-1]

        if not token:
            parts.append(escape(trailing))
            continue

        if token.lower().startswith("http"):
            url = token
        else:
            # only strip a leading "doi:" label - the rest of the token is the DOI
            url = "https://doi.org/" + DOI_LABEL_PREFIX.sub("", token).strip()

        parts.append(Markup('<a href="{}" target="_blank" rel="noopener">{}</a>').format(url, token))
        parts.append(escape(trailing))

    parts.append(escape(reference[position:]))
    return Markup("").join(parts)
