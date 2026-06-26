from portality.models import Cache, JournalCSV, DataDump

csv_cache = Cache.pull("csv")
if csv_cache is not None:
    # Note, we are not going to migrate the csv cache as these are generated regularly,
    # and the cache record does not contain the container and filename, so the csv cannot be
    # cleaned up afterward
    csv_cache.delete()

pdd_cache = Cache.pull("public_data_dump")
if pdd_cache is not None:
    ddd = DataDump()
    ddd.dump_date = pdd_cache.created_date
    article = pdd_cache.data.get("article", {})
    journal = pdd_cache.data.get("journal", {})
    ddd.set_article_dump(
        container=article.get("container"),
        filename=article.get("filename"),
        size=article.get("size"),
        url=article.get("url")
    )
    ddd.set_journal_dump(
        container=journal.get("container"),
        filename=journal.get("filename"),
        size=journal.get("size"),
        url=journal.get("url")
    )
    ddd.save()
    pdd_cache.delete()
