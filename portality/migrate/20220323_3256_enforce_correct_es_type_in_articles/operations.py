def enforce_correct_es_type(article):
    if article.data["es_type"] != "article":
        print(article.data["es_type"])
        article.data["es_type"] = "article"
    return article