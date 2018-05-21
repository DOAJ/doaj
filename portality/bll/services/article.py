from portality.lib.argvalidate import argvalidate
from portality import models
from portality.bll import exceptions

from datetime import datetime

class ArticleService(object):

    def create_article(self, article, account, duplicate_check=True, merge_duplicate=True):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("is_legitimate_owner", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg": account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : duplicate_check, "instance" : bool, "allow_none" : False, "arg_name" : "duplicate_check"},
            {"arg" : merge_duplicate, "instance" : bool, "allow_none" : False, "arg_name" : "merge_duplicate"}
        ], exceptions.ArgumentException)

        # before saving, we need to determine whether this is a new article
        # or an update
        if duplicate_check:
            duplicate = self.get_duplicate(article, account.id)
            if duplicate is not None:
                if merge_duplicate:
                    article.merge(duplicate) # merge will take the old id, so this will overwrite
                else:
                    raise exceptions.DuplicateArticleException()

        # finally, save the new article
        article.save()


    def is_legitimate_owner(self, article, owner):
        """
        Determine if the owner id is the owner of the article

        :param article:
        :param owner:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("is_legitimate_owner", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg" : owner, "instance" : unicode, "allow_none" : False, "arg_name" : "owner"}
        ], exceptions.ArgumentException)

        # get all the issns for the article
        b = article.bibjson()
        issns = b.get_identifiers(b.P_ISSN)
        issns += b.get_identifiers(b.E_ISSN)

        # check each issn against the index, and if a related journal is found
        # record the owner of that journal
        owners = []
        seen_issns = {}
        for issn in issns:
            journals = models.Journal.find_by_issn(issn)
            if journals is not None and len(journals) > 0:
                for j in journals:
                    owners.append(j.owner)
                    if j.owner not in seen_issns:
                        seen_issns[j.owner] = []
                    seen_issns[j.owner] += j.bibjson().issns()

        # deduplicate the list of owners
        owners = list(set(owners))

        # no owner means we can't confirm
        if len(owners) == 0:
            return False

        # multiple owners means ownership of this article is confused
        if len(owners) > 1:
            return False

        # single owner must still know of all supplied issns
        compare = list(set(seen_issns[owners[0]]))
        if len(compare) == 2:   # we only want to check issn parity for journals where there is more than one issn available.
            for issn in issns:
                if issn not in compare:
                    return False

        # true if the found owner is the same as the desired owner, otherwise false
        return owners[0] == owner


    def issn_ownership_status(self, article, owner):
        """
        Determine the ownership status of the supplied owner over the issns in the given article

        This will give you a tuple back which lists the following (in order):

        * which issns are owned by that owner
        * which issns are shared with another owner
        * which issns are not owned by this owner
        * which issns are not found in the DOAJ database

        :param article:
        :param owner:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("issn_ownership_status", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg" : owner, "instance" : unicode, "allow_none" : False, "arg_name" : "owner"}
        ], exceptions.ArgumentException)

        # get all the issns for the article
        b = article.bibjson()
        issns = b.get_identifiers(b.P_ISSN)
        issns += b.get_identifiers(b.E_ISSN)

        owned = []
        shared = []
        unowned = []
        unmatched = []

        # check each issn against the index, and if a related journal is found
        # record the owner of that journal
        seen_issns = {}
        for issn in issns:
            journals = models.Journal.find_by_issn(issn)
            if journals is not None and len(journals) > 0:
                for j in journals:
                    if issn not in seen_issns:
                        seen_issns[issn] = set()
                    seen_issns[issn].add(j.owner)

        for issn in issns:
            if issn not in seen_issns.keys():
                unmatched.append(issn)

        for issn, owners in seen_issns.iteritems():
            owners = list(owners)
            if len(owners) == 0:
                unowned.append(issn)
            elif len(owners) == 1 and owners[0] == owner:
                owned.append(issn)
            elif len(owners) == 1 and owners[0] != owner:
                unowned.append(issn)
            elif len(owners) > 1:
                if owner in owners:
                    shared.append(issn)
                else:
                    unowned.append(issn)

        return owned, shared, unowned, unmatched


    def get_duplicate(self, article, owner=None):
        """
        Get at most one one, most recent, duplicate article for the supplied article.

        If the owner id is provided, this will limit the search to duplicates owned by that owner

        :param article:
        :param owner:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("get_duplicate", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg" : owner, "instance" : unicode, "allow_none" : True, "arg_name" : "owner"}
        ], exceptions.ArgumentException)

        d = self.get_duplicates(article, owner)
        return d[0] if d else None


    def get_duplicates(self, article, owner=None):
        """
        Get all known duplicates of an article

        If the owner id is provided, this will limit the search to duplicates owned by that owner

        :param article:
        :param owner:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("get_duplicates", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg" : owner, "instance" : unicode, "allow_none" : True, "arg_name" : "owner"}
        ], exceptions.ArgumentException)

        possible_articles_dict = self.discover_duplicates(article, owner)
        if not possible_articles_dict:
            return []

        # We don't need the details of duplicate types, so flatten the lists.
        all_possible_articles = [article for dup_type in possible_articles_dict.values() for article in dup_type]

        # An article may fulfil more than one duplication criteria, so needs to be de-duplicated
        ids = []
        possible_articles = []
        for a in all_possible_articles:
            if a.id not in ids:
                ids.append(a.id)
                possible_articles.append(a)

        # Sort the articles newest -> oldest by last_updated so we can get the most recent at [0]
        possible_articles.sort(key=lambda x: datetime.strptime(x.last_updated, "%Y-%m-%dT%H:%M:%SZ"), reverse=True)

        return possible_articles


    def discover_duplicates(self, article, owner=None):
        """
        Identify duplicates, separated by duplication criteria

        If the owner id is provided, this will limit the search to duplicates owned by that owner

        :param article:
        :param owner:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("discover_duplicates", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg" : owner, "instance" : unicode, "allow_none" : True, "arg_name" : "owner"}
        ], exceptions.ArgumentException)

        # Get the owner's ISSNs
        issns = []
        if owner is not None:
            issns = models.Journal.issns_by_owner(owner)

        # We'll need the article bibjson a few times
        b = article.bibjson()

        # if we get more than one result, we'll record them here, and then at the end
        # if we haven't got a definitive match we'll pick the most likely candidate
        # (this isn't as bad as it sounds - the identifiers are pretty reliable, this catches
        # issues like where there are already duplicates in the data, and not matching one
        # of them propagates the issue)
        possible_articles = {}
        found = False

        # Checking by DOI is our first step
        dois = b.get_identifiers(b.DOI)
        if len(dois) > 0:
            # there should only be the one
            doi = dois[0]
            if isinstance(doi, basestring) and doi != '':
                articles = models.Article.duplicates(issns=issns, doi=doi)
                possible_articles['doi'] = [a for a in articles if a.id != article.id]
                if len(possible_articles['doi']) > 0:
                    found = True

        # Second test is to look by fulltext url
        urls = b.get_urls(b.FULLTEXT)
        if len(urls) > 0:
            # there should be only one, but let's allow for multiple
            articles = models.Article.duplicates(issns=issns, fulltexts=urls)
            possible_articles['fulltext'] = [a for a in articles if a.id != article.id]
            if possible_articles['fulltext']:
                found = True

        return possible_articles if found else None