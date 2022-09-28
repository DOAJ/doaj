def add_admin_field(article):
    if not "admin" in article.data:
        article.data["admin"] = {"in_doaj": True}
    return article