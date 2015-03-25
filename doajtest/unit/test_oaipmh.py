from portality.view import oaipmh
from portality.models import OAIPMHJournal, OAIPMHArticle

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
from doajtest.bootstrap import prepare_for_test
prepare_for_test()

oaipmh.list_records(OAIPMHJournal(), "http://localhost:5004/oai", None)