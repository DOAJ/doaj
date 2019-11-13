from portality import models
from portality.view.forms import AuthorForm


class ArticleFormXWalk(object):
    format_name = "form"

    def crosswalk_form(self, form, add_journal_info=True, limit_to_owner=None):
        article = models.Article()
        bibjson = article.bibjson()

        # title
        bibjson.title = form.title.data

        # doi
        doi = form.doi.data
        if doi is not None and doi != "":
            bibjson.add_identifier(bibjson.DOI, doi)

        # authors
        for subfield in form.authors:
            author = subfield.form.name.data
            aff = subfield.form.affiliation.data
            if author is not None and author != "":
                bibjson.add_author(author, affiliation=aff)

        # abstract
        abstract = form.abstract.data
        if abstract is not None and abstract != "":
            bibjson.abstract = abstract

        # keywords
        keywords = form.keywords.data
        if keywords is not None and keywords != "":
            ks = [k.strip() for k in keywords.split(",")]
            bibjson.set_keywords(ks)

        # fulltext
        ft = form.fulltext.data
        if ft is not None and ft != "":
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
        if pissn is not None and pissn != "":
            bibjson.add_identifier(bibjson.P_ISSN, pissn)

        # eissn
        eissn = form.eissn.data
        if eissn is not None and eissn != "":
            bibjson.add_identifier(bibjson.E_ISSN, eissn)

        # volume
        volume = form.volume.data
        if volume is not None and volume != "":
            bibjson.volume = volume

        # number
        number = form.number.data
        if number is not None and number != "":
            bibjson.number = number

        # start date
        start = form.start.data
        if start is not None and start != "":
            bibjson.start_page = start

        # end date
        end = form.end.data
        if end is not None and end != "":
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
            pissn = bibjson.first_pissn
            if pissn is not None:
                form.pissn.data = pissn
            eissn = bibjson.first_eissn
            if eissn is not None:
                form.eissn.data = eissn
            if bibjson.volume is not None:
                form.volume.data = bibjson.volume
            if bibjson.number is not None:
                form.number.data = bibjson.number
            if bibjson.start_page is not None:
                form.start.data = bibjson.start_page
            if bibjson.end_page is not None:
                form.end.data = bibjson.end_page

