from portality.models import Journal


journals = [
    {'title':'Title 1', 'publisher': 'Publisher 1', 'issn': '12345678'},
    {'title':'Title 2', 'publisher': 'Publisher 2', 'issn': '01234567', 'eissn': '76543210', 'license': 'cc-by'},
    {'title':'Title 3', 'publisher': 'Publisher 3', 'apc': False},
    {'title':'Title 4', 'publisher': 'Publisher 3', 'language': 'en', 'content_in_doaj': True},
    {'title':'Title 5', 'publisher': 'Publisher 2', 'issn': '23456789', 'content_in_doaj': False, 'language': 'bg', 'apc':True},
]

for j in journals:
    jm = Journal(**j)
    jm.save()

Journal.refresh()
