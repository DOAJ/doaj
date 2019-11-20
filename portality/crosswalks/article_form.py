from portality import models
from portality.view.forms import AuthorForm


class ArticleFormXWalk(object):
    format_name = "form"

    def crosswalk_form(self, form, add_journal_info=True, limit_to_owner=None, id=None):
        if id is not None:
            article = models.Article.pull(id)
            bibjson = article.bibjson()
        else:
            article = models.Article()
            bibjson = article.bibjson()

        # title
        bibjson.title = form.title.data

        # doi
        doi = form.doi.data
        if doi is not None:
            bibjson.remove_identifiers(bibjson.DOI)
        if doi is not "":
            bibjson.add_identifier(bibjson.DOI, doi)

        # authors
        if bibjson.author:
            bibjson.author = []
        for subfield in form.authors:
            if subfield.form.name.data is not "":
                author = subfield.form.name.data
                aff = subfield.form.affiliation.data
                if author is not None and author != "":
                    bibjson.add_author(author, affiliation=aff)

        # abstract
        abstract = form.abstract.data
        if abstract is not None:
            bibjson.abstract = abstract

        # keywords
        keywords = form.keywords.data
        if keywords is not None:
            ks = [k.strip() for k in keywords.split(",")]
            bibjson.set_keywords(ks)

        # fulltext
        ft = form.fulltext.data
        if ft is not None:
            bibjson.remove_urls("fulltext")
            bibjson.add_url(ft, "fulltext")

        # publication year/month
        py = form.publication_year.data
        pm = form.publication_month.data
        if pm is not None:
            bibjson.month = pm
        if py is not None:
            bibjson.year = py

        # pissn
        pissn = form.pissn.data
        if pissn is not None:
            bibjson.remove_identifiers(bibjson.P_ISSN)
            bibjson.add_identifier(bibjson.P_ISSN, pissn)

        # eissn
        eissn = form.eissn.data
        if eissn is not None:
            bibjson.remove_identifiers(bibjson.E_ISSN)
            bibjson.add_identifier(bibjson.E_ISSN, eissn)

        # volume
        volume = form.volume.data
        if volume is not None:
            bibjson.volume = volume

        # number
        number = form.number.data
        if number is not None:
            bibjson.number = number

        # start date
        start = form.start.data
        if start is not None:
            bibjson.start_page = start

        # end date
        end = form.end.data
        if end is not None:
            bibjson.end_page = end

        # add the journal info if requested
        if add_journal_info:
            article.add_journal_metadata()

        """
        # before finalising, we need to determine whether this is a new article
        # or an update
        duplicate = self.get_duplicate(article, limit_to_owner)
        # print duplicate
        if duplicate is not None:
            article.merge(duplicate) # merge will take the old id, so this will overwrite
        """

        return article

    @classmethod
    def obj2form(cls, form, bibjson):
            if bibjson.title is not None:
                form.title.data = bibjson.title
            doi = bibjson.get_one_identifier("doi")
            if doi is not None:
                form.doi.data = doi
            if bibjson.author is not None:
                for a in bibjson.author:
                    author = AuthorForm()
                    if "name" in a:
                        author.name = a["name"]
                    else:
                        author.name = ""
                    if "affiliation" in a:
                        author.affiliation = a["affiliation"]
                    else:
                        author.affiliation = ""
                    form.authors.append_entry(author)
            if bibjson.keywords is not None:
                form.keywords.data = ""
                for k in bibjson.keywords:
                    if form.keywords.data == "":
                        form.keywords.data = k
                    else:
                        form.keywords.data = form.keywords.data + "," + k
            url = bibjson.get_single_url("fulltext")
            if url is not None:
                form.fulltext.data = url
            if bibjson.month is not None:
                form.publication_month.data = bibjson.month
            if bibjson.year is not None:
                form.publication_year.data = bibjson.year
            pissn = bibjson.get_identifiers(bibjson.P_ISSN)
            if len(pissn) > 0:
                form.pissn.data = pissn[0]
            eissn = bibjson.get_identifiers(bibjson.E_ISSN)
            if len(eissn) > 0:
                form.eissn.data = eissn[0]
            if bibjson.volume is not None:
                form.volume.data = bibjson.volume
            if bibjson.number is not None:
                form.number.data = bibjson.number
            if bibjson.start_page is not None:
                form.start.data = bibjson.start_page
            if bibjson.end_page is not None:
                form.end.data = bibjson.end_page
            if bibjson.abstract is not None:
                form.abstract.data = bibjson.abstract

