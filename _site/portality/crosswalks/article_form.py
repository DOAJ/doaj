from portality import models

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
            orcid_id = subfield.form.orcid_id.data
            if author is not None and author != "":
                bibjson.add_author(author, affiliation=aff, orcid_id=orcid_id)

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
