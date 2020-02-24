from portality.models.v2 import shared_structs

from portality.models.bibjson import GenericBibJSON
from portality.models.lcc import LCC
from portality.models.account import Account
from portality.models.editors import EditorGroup, EditorGroupMemberQuery, EditorGroupQuery
from portality.models.uploads import FileUpload, ExistsFileQuery, OwnerFileQuery, ValidFileQuery
from portality.models.lock import Lock
from portality.models.journal import Journal, JournalBibJSON, JournalQuery, IssnQuery, PublisherQuery, TitleQuery, ContinuationException
from portality.models.suggestion import Suggestion, SuggestionQuery, OwnerStatusQuery
from portality.models.history import ArticleHistory, JournalHistory
from portality.models.article import Article, ArticleBibJSON, ArticleQuery, ArticleVolumesQuery, DuplicateArticleQuery, NoJournalException
from portality.models.oaipmh import OAIPMHRecord, OAIPMHJournal, OAIPMHArticle
from portality.models.atom import AtomRecord
from portality.models.search import JournalArticle, JournalArticleQuery
from portality.models.cache import Cache
from portality.models.openurl import OpenURLRequest
from portality.models.provenance import Provenance
from portality.models.background import BackgroundJob

import sys

def lookup_model(name='', capitalize=True, split_on="_"):
    parts = name.split(split_on)
    if capitalize:
        parts = [p.capitalize() for p in parts]
    name = "".join(parts)
    try:
        return getattr(sys.modules[__name__], name)
    except:
        return None

############################################################################
# Generic/Utility classes and functions
############################################################################
class ObjectDict(object):
    """WTForms requires an object in order to work properly, not a dict or an unpacked dict."""
    def __init__(self, d):
        super(ObjectDict, self).__setattr__('data', d)

    def __getattr__(self, item):
        return self.data[item]

    def __setattr__(self, key, value):
        self.data[key] = value
