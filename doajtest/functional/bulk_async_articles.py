"""
Quick manual test of the asynchronous article bulk article create API.

To run this test first activate the testdrive `/testdrive/publisher_with_journal`, then
insert the API key in the  `API_KEY` variable below. Then you can execute this script
to see articles being bulk created, and the status response.
"""

import requests, json
from doajtest.fixtures.article import ArticleFixtureFactory

API_KEY = "c7659b4bf01a456f80ec82fcb8295bfa"

# make some articles to bulk load (just a couple is fine)

articles = [ArticleFixtureFactory.make_article_source(in_doaj=True, eissn="1111-1111", pissn="2222-2222")] * 2
data = json.dumps(articles)

resp = requests.post(f"http://localhost:5004/api/bulk/articles?api_key={API_KEY}", data=data)
print(resp.status_code)
print(resp.text)

