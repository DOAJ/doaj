import requests, json, time
from copy import deepcopy
from doajtest.fixtures import ApplicationFixtureFactory, DoajXmlArticleFixtureFactory

# applications
API = "http://localhost:5004/api/v1/bulk/applications"
KEY = "d117ad1b35b94469b3dae09c29bfed55"

dataset = [ApplicationFixtureFactory.incoming_application()] * 10

resp = requests.post(API + "?api_key=" + KEY, data=json.dumps(dataset))
assert resp.status_code == 201

j = resp.json()
assert len(j) == 10

print j

ids = [r.get("id") for r in j]
print ids

time.sleep(2)

resp = requests.delete(API + "?api_key=" + KEY, data=json.dumps(ids))
assert resp.status_code == 204

# articles
# make sure you give the api key of a user who has a journal which is
# in_doaj = True and also has the same ISSNs as the articles in the test
# data - usually this will be PISSN 1234-5678 and EISSN 9876-5432
API = "http://localhost:5004/api/v1/bulk/articles"
KEY = "d117ad1b35b94469b3dae09c29bfed55"

# make the dataset
# if you use the dataset = [ArticleFixtureFactory.make_incoming_api_article()] * 10
# syntax it'll just create 10 references to the same dict, so by changing one (later)
# you'll change all of them
dataset = []
for i in range(0, 10):
    dataset.append(deepcopy(DoajXmlArticleFixtureFactory.make_incoming_api_article()))

for i, d in enumerate(dataset):
    # This will fail if you already have articles with
    # fulltext URL http://www.example.org/article{var} or
    # or DOI 10.000{var}/SOME.IDENTIFIER
    # attached to them due to duplication detection in CRUD API Article create.
    d['bibjson']['identifier'][0] = {'id': '10.000{var}/test/SOME.TOTALLY.DIFFERENT.IDENTIFIER'.format(var=i), 'type': 'doi'}
    d['bibjson']['link'][0] = {'content_type': 'HTML', 'type': 'fulltext', 'url': 'http://www.ohdear.org/article{var}'.format(var=i)}

resp = requests.post(API + "?api_key=" + KEY, data=json.dumps(dataset))
assert resp.status_code == 201

j = resp.json()
assert len(j) == 10

print j

ids = [r.get("id") for r in j]
print ids

time.sleep(2)

resp = requests.delete(API + "?api_key=" + KEY, data=json.dumps(ids))
assert resp.status_code == 204