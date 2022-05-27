def enforce_correct_es_type(article):
    if article.data["es_type"] != "article":
        article.data["es_type"] = "article"
    return article