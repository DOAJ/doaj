from portality.models import Journal
def add_admin_field(article):
    log = ""
    if not "admin" in article.data:
        print(article.data["index"]["issn"])
        try:
            j_data = Journal.find_by_issn(article.data["index"]["issn"])
            if len(j_data):
                log += "Article matches more than one journal: "
                log += j_data
            else:
                j = Journal.pull(j_data[0]["id"])
        except:
            log += "\n Corrupted article, no issn: ";
            log += article.data;
        if j is not None:
            article.data["admin"] = {"in_doaj": j.is_in_doaj}
        else:
            log += "\n Article with no journal found: ";
            log += article.data;
    if log != "":
        with open('1735_log.txt','w') as file:
            file.write(log);
    return article