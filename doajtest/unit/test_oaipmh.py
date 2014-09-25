import doajtest  # runs the __init__.py which runs the tests bootstrap code. All tests should import this.
from portality.view import oaipmh
from portality.models import OAIPMHJournal, OAIPMHArticle

oaipmh.list_records(OAIPMHJournal(), "http://localhost:5004/oai")