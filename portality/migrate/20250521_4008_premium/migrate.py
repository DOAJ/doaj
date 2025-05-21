from portality.models import Cache

delete_caches = ["public_data_dump", "csv"]

for cache in delete_caches:
    cr = Cache.pull(cache)
    if cr is not None:
        cr.delete()
