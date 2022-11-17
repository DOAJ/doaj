from portality.models import Journal
def add_admin_field(article):
    if not "admin" in article.data:
        try:
            j_data = Journal.find_by_issn(article.data["index"]["issn"])
            if len(j_data):
                print("Article matches more than one journal: ");
                print(j_data);
            else:
                j = Journal.pull(j_data[0]["id"])
        except:
            print("\n Corrupted article, no issn: ");
            print(article.data);
        if j is not None:
            article.data["admin"] = {"in_doaj": j.is_in_doaj}
        else:
            print("\n Article with no journal found: ");
            log += article.data;
    return article