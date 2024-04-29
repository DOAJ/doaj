"""
Quick manual test of the asynchronous article bulk article create API.

To run this test first activate the testdrive `/testdrive/publisher_with_journal`, then
insert the API key in the  `API_KEY` variable below. Then you can execute this script
to see articles being bulk created, and the status response.
"""

import requests, json
from doajtest.fixtures.article import ArticleFixtureFactory

API_KEY = "af2185c6bc8c4d47b076e92b7467151b"

# make some articles to bulk load (Use quite a few to justify the async)

articles = ArticleFixtureFactory.make_many_article_sources(800, in_doaj=True, eissn="1111-1111", pissn="2222-2222")
data = json.dumps(articles)

resp = requests.post(f"https://testdoaj.cottagelabs.com/api/bulk/articles?api_key={API_KEY}", data=data)
print(resp.status_code)
print(resp.text)
