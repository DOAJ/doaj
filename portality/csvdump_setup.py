from portality.models import Journal


journals = [
    {'title':'Title 1', 'publisher': 'Publisher 1', 'identifier':[{'type':'pissn', 'id': '12345678'}]},
    {'title':'Title 2', 'publisher': 'Publisher 2', 'identifier':[{'type':'pissn', 'id': '01234567'}, {'type':'eissn', 'id': '76543210'}], 'license': [{'type': 'cc-by','open_access': True, 'url': 'http://opendefinition.org/licenses/cc-by/'}]},
    {'title':'Title 3', 'publisher': 'Publisher 3', 'author_pays': False},
    {'title':'Title 4', 'publisher': 'Publisher 3', 'language': 'en', 'active': True},
    {'title':'Title 5', 'publisher': 'Publisher 2', 'identifier':[{'type':'pissn', 'id': '23456789'}], 'active': False, 'language': 'bg', 'author_pays':True},
]

for j in journals:
    jm = Journal(**{'bibjson':j})

    jm.save()

Journal.refresh()
