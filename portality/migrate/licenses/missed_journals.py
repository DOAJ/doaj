from esprit import tasks, raw
from portality import models
import json

'''
Use a scroll search to update mis-labelled licenses in the DOAJ.
'''

# The articles missed by the update_licenses script
missed_articles = [u'0028-9930', u'0034-7310', u'1089-6891', u'2014-7351', u'1960-6004', u'1326-2238', u'1678-4226', u'2036-3603', u'1678-4936', u'0104-7930', u'2009-4161', u'0173-5969', u'1863-5245', u'1679-2041', u'2065-7647', u'1406-0000', u'0182-1279', u'0000-0000', u'1301-3438', u'1402-150X', u'1985-8329', u'2163-7984', u'1670-7796', u'1670-7788', u'2067-7694', u'2307-5359', u'1862-4006', u'1985-8353', u'1614-2934', u'0158-1328', u'2163-3987', u'2250-5490', u'1176-4120', u'2008-4073', u'0232-0475']

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
            print ("Failed to create a model")
        except KeyError:
            print ("No license to change")

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print ("writing ", len(write_batch))
        models.Article.bulk(write_batch)
        write_batch = []

# Write all remaining files to index
if len(write_batch) > 0:
    print ("writing ", len(write_batch))
    models.Article.bulk(write_batch)
