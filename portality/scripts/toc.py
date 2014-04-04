from portality import models
import os, json

q = {
  "query" : {
    "terms" : {"index.issn.exact" : ["1916-9760", "1916-9752"]}
  }
}

articles = models.Article.iterate(q, page_size=1000)

volume_table = {}
year_table = {}
vol_num_table = {}
year_month_table = {}
year_to_vol = []
yearmonth_to_volnum = []
missing = {
    "totally" : [],
    "month" : [],
    "number" : []
}

for article in articles:
    tracked = False
    b = article.bibjson()
    vol = b.volume
    num = b.number
    year = b.year
    month = b.month
    
    # record the article against volume/issue
    if vol is not None:
        tracked = True
        
        # record the article against the volume, whether we have the number or not
        if vol not in volume_table:
            volume_table[vol] = []
        volume_table[vol].append(article.id)
        
        if num is not None: # we have the volume and the issue
            if vol not in vol_num_table:
                vol_num_table[vol] = {}
            if num not in vol_num_table[vol]:
                vol_num_table[vol][num] = []
            vol_num_table[vol][num].append(article.id)
        else:
            missing["number"].append(article.id)
        
    # record the article against year/month
    if year is not None:
        tracked = True
        # record the article against the year, whether we have the month or not
        if year not in year_table:
            year_table[year] = []
        year_table[year].append(article.id)
        
        if month is not None: # we have the year and the month
            if year not in year_month_table:
                year_month_table[year] = {}
            if month not in year_month_table[year]:
                year_month_table[year][month] = []
            year_month_table[year][month].append(article.id)
        else:
            missing["month"].append(article.id)
    
    # record year/month to vol/issue equivalences
    if vol is not None and year is not None:
        # record the year to vol relationship
        year_to_vol.append((year, vol))
        
        if num is not None and month is not None: # we have issue number and month
            yearmonth_to_volnum.append(((year, month), (vol, num)))
    
    if not tracked:
        missing["totally"].append(article.id)

# deduplicate the year/volume mappings
year_to_vol = list(set(year_to_vol))
yearmonth_to_volnum = list(set(yearmonth_to_volnum))

outdir = "/home/richard/tmp/doaj/toc"

with open(os.path.join(outdir, "volume.json"), "wb") as f:
    f.write(json.dumps(volume_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year.json"), "wb") as f:
    f.write(json.dumps(year_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "vol_num.json"), "wb") as f:
    f.write(json.dumps(vol_num_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year_month.json"), "wb") as f:
    f.write(json.dumps(year_month_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year_to_vol.json"), "wb") as f:
    f.write(json.dumps(year_to_vol, sort_keys=True, indent=2))

with open(os.path.join(outdir, "yearmonth_to_volnum.json"), "wb") as f:
    f.write(json.dumps(yearmonth_to_volnum, sort_keys=True, indent=2))

with open(os.path.join(outdir, "missing.json"), "wb") as f:
    f.write(json.dumps(missing, sort_keys=True, indent=2))
























    
