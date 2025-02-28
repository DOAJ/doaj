import uuid
import csv
import random
import string
import os

from portality.core import app
from portality.store import StoreFactory, StoreException
from portality.util import no_op
from portality import models
from portality.crosswalks.journal_questions import Journal2QuestionXwalk
from portality.lib import dates

class ExportService(object):
    def csv(self, model: models.JournalLikeObject, query=None, logger=None, out_file=None,
            biblio_fieldset=True,
            meta_fieldset=True,
            article_fieldset=True,
            doaj_link=True,
            admin_fieldset=False,
            obscure_accounts=True,
            add_sensitive_account_info=False,
            custom_columns=None,
            exclude_no_issn=True):

        # None isn't executable, so convert logger to NO-OP
        if logger is None:
            logger = no_op

        filename = None
        out = out_file
        if out_file is None:
            filename = 'csv_' + uuid.uuid4().hex + '_utf8.csv'
            container_id = "csv_export_tmp_container"
            tmpStore = StoreFactory.tmp()
            try:
                out = tmpStore.path(container_id, filename, create_container=True, must_exist=False)
                logger("Temporary CSV will be written to {x}".format(x=out))
            except StoreException as e:
                logger("Could not create temporary CSV file: {x}".format(x=e))
                raise e

        if filename is None:
            filename = os.path.basename(out)

        with open(out, 'w', encoding='utf-8') as csvfile:
            first = True
            csvwriter = csv.writer(csvfile)
            for obj in model.scroll(query, page_size=100, keepalive='1m'):
                logger("Exporting {f} {x}".format(f=model.__type__, x=obj.id))

                if exclude_no_issn:
                    bj = obj.bibjson()
                    issn = bj.get_one_identifier(idtype=bj.P_ISSN)
                    if issn is None:
                        issn = bj.get_one_identifier(idtype=bj.E_ISSN)
                    if issn is None:
                        continue

                row = self.object_as_question_and_answer(obj, biblio_fieldset=biblio_fieldset,
                                                            meta_fieldset=meta_fieldset,
                                                            article_fieldset=article_fieldset,
                                                            doaj_link=doaj_link,
                                                            admin_fieldset=admin_fieldset,
                                                            obscure_accounts=obscure_accounts,
                                                            add_sensitive_account_info=add_sensitive_account_info,
                                                            custom_columns=custom_columns)
                if first is True:
                    qs = [q for q, _ in row]
                    csvwriter.writerow(qs)
                    first = False

                vs = [v for _, v in row]
                csvwriter.writerow(vs)

        logger("All records exported and CSV written to temp store {}".format(out))
        return out, filename

    def object_as_question_and_answer(self, obj: models.JournalLikeObject,
                                      biblio_fieldset=True,
                                      meta_fieldset=True,
                                      article_fieldset=True,
                                      doaj_link=True,
                                      admin_fieldset=False,
                                      obscure_accounts=True,
                                      add_sensitive_account_info=False,
                                      custom_columns=None):
        YES_NO = {True: 'Yes', False: 'No', None: '', '': ''}
        unmap = {}

        def _get_doaj_meta_kvs(journal):
            """
            Get key, value pairs for some meta information we want from the journal object
            :param journal: a models.Journal
            :return: a list of (key, value) tuples for our metadata
            """
            kvs = [
                ("Subjects", ' | '.join(journal.bibjson().lcc_paths())),
                ("DOAJ Seal", YES_NO.get(journal.has_seal(), "")),
                # ("Tick: Accepted after March 2014", YES_NO.get(journal.is_ticked(), "")),
                ("Added on Date", journal.created_date),
                ("Last updated Date", journal.last_manual_update)
            ]
            return kvs

        def _get_doaj_toc_kv(journal):
            return "URL in DOAJ", app.config.get('JOURNAL_TOC_URL_FRAG', 'https://doaj.org/toc/') + journal.id

        def _get_article_kvs(journal):
            stats = journal.article_stats()
            kvs = [
                ("Number of Article Records", str(stats.get("total"))),
                ("Most Recent Article Added", stats.get("latest"))
            ]
            return kvs

        def _usernames(j):
            o = j.owner
            if obscure_accounts:
                if o in unmap:
                    sub = unmap[o]
                else:
                    sub = "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(8))
                    unmap[o] = sub
                return [("Owner", sub)]
            else:
                return [("Owner", o)]

        def _acc_name(j):
            o = j.owner
            a = models.Account.pull(o)
            return [("Account Name", a.name)] if a is not None else ""

        def _acc_email(j):
            o = j.owner
            a = models.Account.pull(o)
            return [("Account Email", a.email)] if a is not None else ""

        biblio_kvs = []
        meta_kvs = []
        article_kvs = []
        toc_kv = None
        admin_kvs = []
        custom_kvs = []

        if biblio_fieldset:
            biblio_kvs = Journal2QuestionXwalk.journal2question(obj)
        if meta_fieldset:
            meta_kvs = _get_doaj_meta_kvs(obj)
        if article_fieldset:
            article_kvs = _get_article_kvs(obj)
        if doaj_link:
            toc_kv = _get_doaj_toc_kv(obj)
        if admin_fieldset:
            admin_kvs = _usernames(obj)
            if add_sensitive_account_info:
                admin_kvs += _acc_name(obj) + _acc_email(obj)
        if custom_columns is not None:
            for cc in custom_columns:
                custom_kvs.append(cc(obj))

        if biblio_fieldset and doaj_link:
            biblio_kvs.insert(2, toc_kv)
        else:
            biblio_kvs.append(toc_kv)

        row = biblio_kvs + meta_kvs + article_kvs + admin_kvs + custom_kvs
        return row

    def delete_tmp_csv(self, filename):
        tmpStore = StoreFactory.tmp()
        container_id = "csv_export_tmp_container"
        tmpStore.delete_file(container_id, filename)

    def publish(self, source_file, filename, requester=None, request_date=None, name=None, query=None, model=None):
        mainStore = StoreFactory.get("export")
        container_id = app.config.get("STORE_EXPORT_CONTAINER")
        mainStore.store(container_id, filename, source_path=source_file)

        e = models.Export()
        e.generated_date = dates.now_str()
        e.requester = requester
        e.request_date = request_date
        e.name = name if name is not None else filename
        e.filename = filename
        e.constraints = query
        e.model = model
        e.save()

        return e

    def retrieve(self, report_id):
        report = models.Export.pull(report_id)
        mainStore = StoreFactory.get("export")
        container_id = app.config.get("STORE_EXPORT_CONTAINER")
        fh = mainStore.get(container_id, report.filename)
        return report, fh
