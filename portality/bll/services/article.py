from portality.lib.argvalidate import argvalidate
from portality.lib.dataobj import to_url
from portality import models, constants, regex
from portality.bll import exceptions
import re

from datetime import datetime

class ArticleService(object):

    def batch_create_articles(self, articles, account, duplicate_check=True, merge_duplicate=True, limit_to_account=True):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("batch_create_article", [
            {"arg": articles, "instance" : list, "allow_none" : False, "arg_name" : "articles"},
            {"arg": account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : duplicate_check, "instance" : bool, "allow_none" : False, "arg_name" : "duplicate_check"},
            {"arg" : merge_duplicate, "instance" : bool, "allow_none" : False, "arg_name" : "merge_duplicate"},
            {"arg" : limit_to_account, "instance" : bool, "allow_none" : False, "arg_name" : "limit_to_account"}
        ], exceptions.ArgumentException)

        # 1. dedupe the batch
        if duplicate_check:
            batch_duplicates = self._batch_contains_duplicates(articles)
            if batch_duplicates:
                raise exceptions.IngestException("One or more articles in this batch have duplicate identifiers")

        # 2. check legitimate ownership
        success = 0
        fail = 0
        update = 0
        new = 0
        all_shared = set()
        all_unowned = set()
        all_unmatched = set()

        for article in articles:
            result = self.create_article(article, account, duplicate_check=duplicate_check, merge_duplicate=merge_duplicate, limit_to_account=limit_to_account, dry_run=True)
            success += result.get("success", 0)
            fail += result.get("fail", 0)
            update += result.get("update", 0)
            new += result.get("new", 0)
            all_shared.update(result.get("shared", set()))
            all_unowned.update(result.get("unowned", set()))
            all_unmatched.update(result.get("unmatched", set()))


        # if there were no failures in the batch, then we can do the save
        if fail == 0:
            for i in xrange(len(articles)):
                block = i == len(articles) - 1
                # block on the final save, so that when this method returns, all articles are
                # available in the index
                articles[i].save(blocking=block)

        # return some stats on the import success or failure
        return {"success" : success, "fail" : fail, "update" : update, "new" : new, "shared" : all_shared, "unowned" : all_unowned, "unmatched" : all_unmatched}


    def _batch_contains_duplicates(self, articles):
        dois = []
        fulltexts = []

        for article in articles:
            doi = article.get_normalised_doi()
            if doi in dois:
                return True
            dois.append(doi)

            ft = article.get_normalised_fulltext()
            if ft in fulltexts:
                return True
            fulltexts.append(ft)

        return False


    def create_article(self, article, account, duplicate_check=True, merge_duplicate=True, limit_to_account=True, dry_run=False):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("create_article", [
            {"arg": article, "instance" : models.Article, "allow_none" : False, "arg_name" : "article"},
            {"arg": account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : duplicate_check, "instance" : bool, "allow_none" : False, "arg_name" : "duplicate_check"},
            {"arg" : merge_duplicate, "instance" : bool, "allow_none" : False, "arg_name" : "merge_duplicate"},
            {"arg" : limit_to_account, "instance" : bool, "allow_none" : False, "arg_name" : "limit_to_account"},
            {"arg" : dry_run, "instance" : bool, "allow_none" : False, "arg_name" : "dry_run"}
        ], exceptions.ArgumentException)

        if limit_to_account:
            legit = self.is_legitimate_owner(article, account)
            if not legit:
                owned, shared, unowned, unmatched = self.issn_ownership_status(article, account)
                return {"success" : 0, "fail" : 1, "update" : 0, "new" : 0, "shared" : shared, "unowned" : unowned, "unmatched" : unmatched}

        # before saving, we need to determine whether this is a new article
        # or an update
        is_update = 0
        if duplicate_check:
            duplicate = self.get_duplicate(article, account.id)
            if duplicate is not None:
                if merge_duplicate:
                    is_update  = 1
                    article.merge(duplicate) # merge will take the old id, so this will overwrite
                else:
                    raise exceptions.DuplicateArticleException()

        # finally, save the new article
        if not dry_run:
            article.save()

        return {"success" : 1, "fail" : 0, "update" : is_update, "new" : 1 - is_update, "shared" : set(), "unowned" : set(), "unmatched" : set()}


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
                    if j.owner is not None:
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
        # dois = b.get_identifiers(b.DOI)
        doi = article.get_normalised_doi()
        if doi is not None:
            if isinstance(doi, basestring) and doi != '':
                articles = models.Article.duplicates(issns=issns, doi=doi)
                if len(articles) > 0:
                    possible_articles['doi'] = [a for a in articles if a.id != article.id]
                    if len(possible_articles['doi']) > 0:
                        found = True

        # Second test is to look by fulltext url
        fulltext = article.get_normalised_fulltext()
        if fulltext is not None:
            articles = models.Article.duplicates(issns=issns, fulltexts=fulltext)
            if len(articles) > 0:
                possible_articles['fulltext'] = [a for a in articles if a.id != article.id]
                if possible_articles['fulltext']:
                    found = True

        if doi is None and fulltext is None:
            raise exceptions.DuplicateArticleException("The article you provided has neither doi nor fulltext url, and as a result cannot be deduplicated")

        return possible_articles if found else None