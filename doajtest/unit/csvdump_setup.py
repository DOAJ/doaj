from portality.models import Journal
import sys

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
from doajtest.bootstrap import prepare_for_test
prepare_for_test()

journals = [
    {'title':'Title 1', 'publisher': 'Publisher 1', 'identifier':[{'type':'pissn', 'id': '1234-5678'}], 'active':True},
    {'title':'Title 2', 'publisher': 'Publisher 2', 'identifier':[{'type':'pissn', 'id': '0123-4567'}, {'type':'eissn', 'id': '7654-3210'}], 'license': [{'type': 'cc-by','open_access': True, 'url': 'http://opendefinition.org/licenses/cc-by/'}], 'active': True},
    {'title':'Title 3', 'publisher': 'Publisher 3', 'author_pays': False, 'active': False},
    {'title':'Title 4', 'publisher': 'Publisher 3', 'language': 'en', 'active': True},
    {'title':'The "Quoted" Journal of Testing CSV Quotes', 'publisher': 'Publisher 2', 'identifier':[{'type':'pissn', 'id': '2345-6789'}], 'active': False, 'language': 'bg', 'author_pays':True, 'active':True, },
]

for j in journals:
    jm = Journal(**{'bibjson':j})

    jm.save()

print 'Sent {0} Journal documents to the index'.format(len(journals))
print 'Refreshing the index'
Journal.refresh()
