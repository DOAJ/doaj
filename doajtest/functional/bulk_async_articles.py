"""
Quick manual test of the asynchronous article bulk article create API.

To run this test first activate the testdrive `/testdrive/publisher_with_journal`, then
insert the API key in the  `API_KEY` variable below. Then you can execute this script
to see articles being bulk created, and the status response.
"""

import requests, json
from doajtest.fixtures.article import ArticleFixtureFactory

API_KEY = "606d4a0a92ac432f9f86d05ddf8d381b"

# make some articles to bulk load (Use quite a few to justify the async)

#TODO: we could use the testdrive fixtures to seed the fixtures below (i.e. a dynamic ISSN)
articles = ArticleFixtureFactory.make_many_article_sources(100, in_doaj=True, eissn="1x11-1111", pissn="2222-2222")
data = json.dumps(articles)

resp = requests.post(f"https://testdoaj.cottagelabs.com/api/bulk/articles?api_key={API_KEY}", data=data)
print(resp.status_code)
print(resp.text)
