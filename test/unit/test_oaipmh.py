from portality.view import oaipmh
from portality.models import OAIPMHJournal, OAIPMHArticle

oaipmh.list_records(OAIPMHJournal(), "http://localhost:5004/oai")