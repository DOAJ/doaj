from wtforms import FieldList, FormField

from portality import models
from portality.view import forms


class ArticleFormXWalk(object):
    format_name = "form"

    @classmethod
    def form2obj(cls, form, add_journal_info=True):
        article = models.Article()
        bibjson = article.bibjson()

        # title
        if form.title.data is not None and form.title.data is not "":
            bibjson.title = form.title.data

        # doi
        doi = form.doi.data
        if doi is not None and doi is not "":
            bibjson.add_identifier(bibjson.DOI, doi)

        # authors
        if bibjson.author:
            bibjson.author = []
        for subfield in form.authors:
            if subfield.form.name.data is not "":
                author = subfield.form.name.data
                if subfield.form.affiliation.data is not "":
                    aff = subfield.form.affiliation.data
                if subfield.form.orcid_id.data is not "":
                    aff = subfield.form.orcid_id.data
        if author is not None and author != "":
            bibjson.add_author(author, affiliation=aff, orcid_id=orcid_id)

        # abstract
        abstract = form.abstract.data
        if abstract is not None and abstract is not "":
            bibjson.abstract = abstract

        # keywords
        keywords = form.keywords.data
        if keywords is not None and keywords is not []:
            ks = [k.strip() for k in keywords.split(",")]
            bibjson.set_keywords(ks)

        # fulltext
        ft = form.fulltext.data
        if ft is not None and ft is not "":
            bibjson.add_url(ft, "fulltext")

        # publication year/month
        py = form.publication_year.data
        pm = form.publication_month.data
        if pm is not None and pm is not "":
            bibjson.month = pm
        if py is not None and py is not "":
            bibjson.year = py

        # pissn
        pissn = form.pissn.data
        if pissn is not None and pissn is not "":
            bibjson.add_identifier(bibjson.P_ISSN, pissn)

        # eissn
        eissn = form.eissn.data
        if eissn is not None and eissn is not "":
            bibjson.add_identifier(bibjson.E_ISSN, eissn)

        # volume
        volume = form.volume.data
        if volume is not None and volume is not "":
            bibjson.volume = volume

        # number
        number = form.number.data
        if number is not None and number is not "":
            bibjson.number = number

        # start date
        start = form.start.data
        if start is not None and start is not "":
            bibjson.start_page = start

        # end date
        end = form.end.data
        if end is not None and end is not "":
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
            if bibjson.title:
                form.title.data = bibjson.title
            doi = bibjson.get_one_identifier("doi")
            if doi:
                form.doi.data = doi
            if bibjson.author:
                for i in range(len(form.authors)):
                    form.authors.pop_entry()
                for a in bibjson.author:
                    author = forms.AuthorForm()
                    if "name" in a:
                        author.name = a["name"]
                    else:
                        author.name = ""
                    if "affiliation" in a:
                        author.affiliation = a["affiliation"]
                    else:
                        author.affiliation = ""
                    form.authors.append_entry(author)

            if bibjson.keywords:
                form.keywords.data = ""
                for k in bibjson.keywords:
                    if form.keywords.data == "":
                        form.keywords.data = k
                    else:
                        form.keywords.data = form.keywords.data + "," + k
            url = bibjson.get_single_url("fulltext")
            if url:
                form.fulltext.data = url
            if bibjson.month:
                form.publication_month.data = bibjson.month
            if bibjson.year:
                form.publication_year.data = bibjson.year
            pissn = bibjson.get_identifiers(bibjson.P_ISSN)
            if len(pissn) > 0:
                form.pissn.data = pissn[0]
            eissn = bibjson.get_identifiers(bibjson.E_ISSN)
            if len(eissn) > 0:
                form.eissn.data = eissn[0]
            if bibjson.volume:
                form.volume.data = bibjson.volume
            if bibjson.number:
                form.number.data = bibjson.number
            if bibjson.start_page:
                form.start.data = bibjson.start_page
            if bibjson.end_page:
                form.end.data = bibjson.end_page
            if bibjson.abstract:
                form.abstract.data = bibjson.abstract

