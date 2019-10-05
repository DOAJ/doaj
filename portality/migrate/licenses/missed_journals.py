from esprit import tasks, raw
from portality import models
import json

'''
Use a scroll search to update mis-labelled licenses in the DOAJ.
'''

# The articles missed by the update_licenses script
missed_articles = ['0028-9930', '0034-7310', '1089-6891', '2014-7351', '1960-6004', '1326-2238', '1678-4226', '2036-3603', '1678-4936', '0104-7930', '2009-4161', '0173-5969', '1863-5245', '1679-2041', '2065-7647', '1406-0000', '0182-1279', '0000-0000', '1301-3438', '1402-150X', '1985-8329', '2163-7984', '1670-7796', '1670-7788', '2067-7694', '2307-5359', '1862-4006', '1985-8353', '1614-2934', '0158-1328', '2163-3987', '2250-5490', '1176-4120', '2008-4073', '0232-0475']

license_correct_dict = { "CC by" : "CC BY",
                         "CC by-nc" : "CC BY-NC",
                         "CC by-nc-nd" : "CC BY-NC-ND",
                         "CC by-nc-sa" : "CC BY-NC-SA",
                         "CC-BY-NC-SA" : "CC BY-NC-SA",
                         "CC by-sa" : "CC BY-SA",
                         "CC by-nd" : "CC BY-ND",
                         "not-cc-like" : "Not CC-like"
                        }

query = \
    { "query" :
        { "query_string" :
                { "default_field" : "index.issn.exact",
                  "query" : "0028-9930"
            }
        }
    }

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

# Edit the Journals

write_batch = []
batch_size = 1000

for article_issn in missed_articles:
    query['query']['query_string']['query'] = article_issn

    for a in tasks.scroll(conn, 'article', query):
        try:
            article_model = models.Article(_source=a)
            a_license = article_model.data.get('index')['license']
            # Change the license
            article_model.data.get('index')['license'] = [license_correct_dict[a_license[0]]]
            write_batch.append(article_model.data)
        except ValueError:
            print("Failed to create a model")
        except KeyError:
            print("No license to change")

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print("writing ", len(write_batch))
        models.Article.bulk(write_batch)
        write_batch = []

# Write all remaining files to index
if len(write_batch) > 0:
    print("writing ", len(write_batch))
    models.Article.bulk(write_batch)
