from portality.lib.seamless import SeamlessMixin, to_utf8_unicode
from portality.models.v2 import shared_structs
from portality import datasets
from portality.lib import coerce

class JournalLikeBibJSON(SeamlessMixin):

    __SEAMLESS_STRUCT__ = shared_structs.JOURNAL_BIBJSON.get("structs", {}).get("bibjson")

    __SEAMLESS_COERCE__ = coerce.COERCE_MAP

    # constructor
    def __init__(self, bibjson=None, **kwargs):
        super(JournalLikeBibJSON, self).__init__(raw=bibjson, **kwargs)

    @property
    def data(self):
        return self.__seamless__.data

    ####################################################
    # Current getters and setters

    @property
    def alternative_title(self):
        return self.__seamless__.get_single("alternative_title")

    @alternative_title.setter
    def alternative_title(self, val):
        self.__seamless__.set_with_struct("alternative_title", val)

    @property
    def boai(self):
        return self.__seamless__.get_single("boai")

    @boai.setter
    def boai(self, val):
        self.__seamless__.set_with_struct("boai", val)

    @property
    def discontinued_date(self):
        return self.__seamless__.get_single("discontinued_date")

    @discontinued_date.setter
    def discontinued_date(self, val):
        self.__seamless__.set_with_struct("discontinued_date", val)

    @discontinued_date.deleter
    def discontinued_date(self):
        self.__seamless__.delete("discontinued_date")

    @property
    def discontinued_datestamp(self):
        return self.__seamless__.get_single("discontinued_date", coerce=coerce.to_datestamp())

    @property
    def eissn(self):
        return self.__seamless__.get_single("eissn")

    @eissn.setter
    def eissn(self, val):
        self.__seamless__.set_with_struct("eissn", val)

    @eissn.deleter
    def eissn(self):
        self.__seamless__.delete("eissn")

    @property
    def pissn(self):
        return self.__seamless__.get_single("pissn")

    @pissn.setter
    def pissn(self, val):
        self.__seamless__.set_with_struct("pissn", val)

    @pissn.deleter
    def pissn(self):
        self.__seamless__.delete("pissn")

    @property
    def publication_time_weeks(self):
        return self.__seamless__.get_single("publication_time_weeks")

    @publication_time_weeks.setter
    def publication_time_weeks(self, weeks):
        self.__seamless__.set_with_struct("publication_time_weeks", weeks)

    @property
    def title(self):
        return self.__seamless__.get_single("title")

    @title.setter
    def title(self, val):
        self.__seamless__.set_with_struct("title", val)

    @property
    def is_replaced_by(self):
        return self.__seamless__.get_list("is_replaced_by")

    @is_replaced_by.setter
    def is_replaced_by(self, val):
        self.__seamless__.set_with_struct("is_replaced_by", val)

    @is_replaced_by.deleter
    def is_replaced_by(self):
        self.__seamless__.delete("is_replaced_by")

    def add_is_replaced_by(self, val):
        self.__seamless__.add_to_list_with_struct("is_replaced_by", val)

    @property
    def keywords(self):
        return self.__seamless__.get_list("keywords")

    def add_keyword(self, keyword):
        if keyword is not None:
            self.__seamless__.add_to_list_with_struct("keywords", keyword.lower())

    @keywords.setter
    def keywords(self, keywords):
        self.__seamless__.set_with_struct("keywords", keywords)

    @property
    def language(self):
        return self.__seamless__.get_list("language")

    @language.setter
    def language(self, language):
        self.__seamless__.set_with_struct("language", language)

    def add_language(self, language):
        self.__seamless__.add_to_list_with_struct("language", language)

    @property
    def licenses(self):
        return self.__seamless__.get_list("license")

    @property
    def licences(self):
        return self.licenses

    def add_licence(self, license_type, url=None, by=None, sa=None, nc=None, nd=None):
        self.add_license(license_type, url, by, sa, nc, nd)

    def add_license(self, license_type, url=None, by=None, sa=None, nc=None, nd=None):
        lobj = {"type": license_type}
        if url is not None:
            lobj["url"] = url
        if by is not None:
            lobj["BY"] = by
        if sa is not None:
            lobj["SA"] = sa
        if nc is not None:
            lobj["NC"] = nc
        if nd is not None:
            lobj["ND"] = nd

        self.__seamless__.add_to_list_with_struct("license", lobj)

    def remove_licenses(self):
        self.__seamless__.delete("license")

    @property
    def replaces(self):
        return self.__seamless__.get_list("replaces")

    @replaces.setter
    def replaces(self, val):
        self.__seamless__.set_with_struct("replaces", val)

    @replaces.deleter
    def replaces(self):
        self.__seamless__.delete("replaces")

    def add_replaces(self, val):
        self.__seamless__.add_to_list_with_struct("replaces", val)

    @property
    def subject(self):
        return self.__seamless__.get_list("subject")

    @subject.setter
    def subject(self, subjects):
        self.__seamless__.set_with_struct("subject", subjects)

    @subject.deleter
    def subject(self):
        self.__seamless__.delete("subject")

    def add_subject(self, scheme, term, code=None):
        sobj = {"scheme": scheme, "term": term}
        if code is not None:
            sobj["code"] = code
        self.__seamless__.add_to_list_with_struct("subject", sobj)

    @property
    def apc(self):
        return self.__seamless__.get_list("apc.max")

    def add_apc(self, currency, price):
        self.__seamless__.add_to_list_with_struct("apc.max", {"currency": currency, "price" : price})
        self.__seamless__.set_with_struct("apc.has_apc", True)

    @property
    def apc_url(self):
        return self.__seamless__.get_single("apc.url")

    @apc_url.setter
    def apc_url(self, url):
        self.__seamless__.set_with_struct("apc.url", url)

    @property
    def has_apc(self):
        return self.__seamless__.get_single("apc.has_apc")

    @property
    def article_license_display(self):
        return self.__seamless__.get_list("article.license_display")

    @article_license_display.setter
    def article_license_display(self, val):
        self.__seamless__.set_with_struct("article.license_display", val)

    def add_article_license_display(self, val):
        self.__seamless__.add_to_list_with_struct("article.license_display", val)

    @property
    def article_license_display_example_url(self):
        return self.__seamless__.get_single("article.license_display_example_url")

    @article_license_display_example_url.setter
    def article_license_display_example_url(self, url):
        self.__seamless__.set_with_struct("article.license_display_example_url", url)

    @property
    def article_orcid(self):
        return self.__seamless__.get_single("article.orcid")

    @article_orcid.setter
    def article_orcid(self, val):
        self.__seamless__.set_with_struct("article.orcid", val)

    @property
    def article_i4oc_open_citations(self):
        return self.__seamless__.get_single("article.i4oc_open_citations")

    @article_i4oc_open_citations.setter
    def article_i4oc_open_citations(self, val):
        self.__seamless__.set_with_struct("article.i4oc_open_citations", val)

    @property
    def author_retains_copyright(self):
        return self.__seamless__.get_single("copyright.author_retains")

    @author_retains_copyright.setter
    def author_retains_copyright(self, val):
        self.__seamless__.set_single("copyright.author_retains", val)

    @property
    def copyright_url(self):
        return self.__seamless__.get_single("copyright.url")

    @copyright_url.setter
    def copyright_url(self, url):
        self.__seamless__.set_with_struct("copyright.url", url)

    @property
    def deposit_policy(self):
        return self.__seamless__.get_list("deposit_policy.service")

    @deposit_policy.setter
    def deposit_policy(self, policies):
        self.__seamless__.set_with_struct("deposit_policy.service", policies)
        if len(policies) > 0:
            self.__seamless__.set_with_struct("deposit_policy.has_policy", True)

    def add_deposit_policy(self, policy):
        self.__seamless__.add_to_list_with_struct("deposit_policy.service", policy)
        self.__seamless__.set_with_struct("deposit_policy.has_policy", True)

    @property
    def has_deposit_policy(self):
        return self.__seamless__.get_single("deposit_policy.has_policy")

    @has_deposit_policy.setter
    def has_deposit_policy(self, val):
        self.__seamless__.set_with_struct("deposit_policy.has_policy", val)

    @property
    def deposit_policy_registered(self):
        return self.__seamless__.get_single("deposit_policy.is_registered")

    @deposit_policy_registered.setter
    def deposit_policy_registered(self, val):
        self.__seamless__.set_with_struct("deposit_policy.is_registered", val)

    @property
    def deposit_policy_url(self):
        return self.__seamless__.get_single("deposit_policy.url")

    @deposit_policy_url.setter
    def deposit_policy_url(self, url):
        self.__seamless__.set_with_struct("deposit_policy.url", url)

    def set_unregistered_journal_policy(self, url):
        self.deposit_policy_url = url
        self.has_deposit_policy = True

    def set_editorial_review(self, process, review_url, board_url=None):
        self.__seamless__.set_with_struct("editorial.review_process", process)
        self.__seamless__.set_with_struct("editorial.review_url", review_url)
        if board_url is not None:
            self.__seamless__.set_with_struct("editorial.board_url", board_url)

    @property
    def editorial_review_process(self):
        return self.__seamless__.get_list("editorial.review_process")

    @property
    def editorial_review_url(self):
        return self.__seamless__.get_single("editorial.review_url")

    @editorial_review_url.setter
    def editorial_review_url(self, url):
        self.__seamless__.set_with_struct("editorial.review_url", url)

    @property
    def editorial_board_url(self):
        return self.__seamless__.get_single("editorial.board_url")

    @editorial_board_url.setter
    def editorial_board_url(self, url):
        self.__seamless__.set_with_struct("editorial.board_url", url)

    @property
    def institution(self):
        return self.__seamless__.get_single("institution.name")

    @institution.setter
    def institution(self, val):
        self.__seamless__.set_with_struct("institution.name", val)

    @property
    def institution_country(self):
        return self.__seamless__.get_single("institution.country")

    @institution_country.setter
    def institution_country(self, country):
        self.__seamless__.set_with_struct("institution.country", country)

    @property
    def has_other_charges(self):
        return self.__seamless__.get_single("other_charges.has_other_charges")

    @has_other_charges.setter
    def has_other_charges(self, val):
        self.__seamless__.set_with_struct("other_charges.has_other_charges", val)

    @property
    def other_charges_url(self):
        return self.__seamless__.get_single("other_charges.url")

    @other_charges_url.setter
    def other_charges_url(self, url):
        self.__seamless__.set_with_struct("other_charges.url", url)

    @property
    def pid_scheme(self):
        return self.__seamless__.get_list("pid_scheme.scheme")

    @pid_scheme.setter
    def pid_scheme(self, schemes):
        self.__seamless__.set_with_struct("pid_scheme.scheme", schemes)
        if len(schemes) > 0:
            self.__seamless__.set_with_struct("pid_scheme.has_pid_scheme", True)

    def add_pid_scheme(self, scheme):
        self.__seamless__.add_to_list_with_struct("pid_scheme.scheme", scheme)
        self.__seamless__.set_with_struct("pid_scheme.has_pid_scheme", True)

    def set_plagiarism_detection(self, url, has_detection=True):
        self.__seamless__.set_with_struct("plagiarism.detection", has_detection)
        self.__seamless__.set_with_struct("plagiarism.url", url)

    @property
    def plagiarism_detection(self):
        return self.__seamless__.get_single("plagiarism.detection", default={})

    @property
    def plagiarism_url(self):
        return self.__seamless__.get_single("plagiarism.url")

    @plagiarism_url.setter
    def plagiarism_url(self, url):
        self.__seamless__.set_with_struct("plagiarism.url", url)

    @property
    def preservation(self):
        return self.__seamless__.get_single("preservation")

    @property
    def preservation_services(self):
        pres = self.preservation
        ret = []
        if "service" in pres:
            ret += pres["service"]
        if "national_library" in pres:
            for anl in pres["national_library"]:
                ret.append(["A national library", anl])
        return ret

    def set_preservation(self, services, policy_url):
        obj = {}
        known = []
        for p in services:
            if isinstance(p, list):
                k, v = p
                if k.lower() == "a national library":
                    if "national_library" in obj:
                        obj["national_library"].append(v)
                    else:
                        obj["national_library"] = [v]
            else:
                known.append(p)
        if len(known) > 0:
            obj["service"] = known
        if policy_url is not None:
            obj["url"] = policy_url

        self.__seamless__.set_with_struct("preservation", obj)

    def add_preservation(self, service):
        if isinstance(service, list):
            k, v = service
            if k.lower() == "a national library":
                self.__seamless__.add_to_list_with_struct("preservation.national_library", v)
        else:
            self.__seamless__.add_to_list_with_struct("preservation.service", service)

    @property
    def preservation_url(self):
        return self.__seamless__.get_single("preservation.url")

    @preservation_url.setter
    def preservation_url(self, url):
        self.__seamless__.set_with_struct("preservation.url", url)

    @property
    def publisher_name(self):
        return self.__seamless__.get_single("publisher.name")

    @publisher_name.setter
    def publisher_name(self, val):
        self.__seamless__.set_with_struct("publisher.name", val)

    @property
    def publisher_country(self):
        return self.__seamless__.get_single("publisher.country")

    @publisher_country.setter
    def publisher_country(self, country):
        self.__seamless__.set_with_struct("publisher.country", country)

    @property
    def oa_statement_url(self):
        return self.__seamless__.get_single("ref.oa_statement")

    @oa_statement_url.setter
    def oa_statement_url(self, url):
        self.__seamless__.set_with_struct("ref.oa_statement", url)

    @property
    def journal_url(self):
        return self.__seamless__.get_single("ref.journal")

    @journal_url.setter
    def journal_url(self, url):
        self.__seamless__.set_with_struct("ref.journal", url)

    @property
    def aims_scope_url(self):
        return self.__seamless__.get_single("ref.aims_scope")

    @aims_scope_url.setter
    def aims_scope_url(self, url):
        self.__seamless__.set_with_struct("ref.aims_scope", url)

    @property
    def author_instructions_url(self):
        return self.__seamless__.get_single("ref.author_instructions")

    @author_instructions_url.setter
    def author_instructions_url(self, url):
        self.__seamless__.set_with_struct("ref.author_instructions", url)

    @property
    def license_terms_url(self):
        return self.__seamless__.get_single("ref.license_terms")

    @license_terms_url.setter
    def license_terms_url(self, url):
        self.__seamless__.set_with_struct("ref.license_terms", url)

    @property
    def has_waiver(self):
        return self.__seamless__.get_single("waiver.has_waiver")

    @has_waiver.setter
    def has_waiver(self, url):
        self.__seamless__.set_with_struct("waiver.has_waiver", url)

    @property
    def waiver_url(self):
        return self.__seamless__.get_single("waiver.url")

    @waiver_url.setter
    def waiver_url(self, url):
        self.__seamless__.set_with_struct("waiver.url", url)

    #####################################################
    ## External utility functions

    def issns(self):
        issns = []
        if self.pissn:
            issns.append(self.pissn)
        if self.eissn:
            issns.append(self.eissn)
        return issns

    def publisher_country_name(self):
        if self.publisher_country is not None:
            return datasets.get_country_name(self.publisher_country)
        return None

    def language_name(self):
        # copy the languages and convert them to their english forms
        langs = [datasets.name_for_lang(l) for l in self.language]
        langs = [to_utf8_unicode(l) for l in langs]
        return list(set(langs))

    def lcc_paths(self):
        classification_paths = []

        # calculate the classification paths
        from portality.lcc import lcc  # inline import since this hits the database
        for subs in self.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            if scheme == "LCC":
                p = lcc.pathify(term)
                if p is not None:
                    classification_paths.append(p)

        # normalise the classification paths, so we only store the longest ones
        classification_paths = lcc.longest(classification_paths)

        return classification_paths

    # to help with ToC - we prefer to refer to a journal by E-ISSN, or
    # if not, then P-ISSN
    def get_preferred_issn(self):
        if self.eissn:
            return self.eissn
        if self.pissn:
            return self.pissn

    #####################################################
    ## Internal utility functions

    def _normalise_issn(self, issn):
        if issn is None:
            return issn
        issn = issn.upper()
        if len(issn) > 8: return issn
        if len(issn) == 8:
            if "-" in issn: return "0" + issn
            else: return issn[:4] + "-" + issn[4:]
        if len(issn) < 8:
            if "-" in issn: return ("0" * (9 - len(issn))) + issn
            else:
                issn = ("0" * (8 - len(issn))) + issn
                return issn[:4] + "-" + issn[4:]

    #####################################################
    ## Back Compat methods for v1 of the model
    ## ALL DEPRECATED

    @property
    def publication_time(self):
        return self.publication_time_weeks

    @publication_time.setter
    def publication_time(self, weeks):
        self.publication_time_weeks = weeks

    @property
    def publisher(self):
        return self.publisher_name

    @publisher.setter
    def publisher(self, val):
        self.publisher_name = val

    def set_keywords(self, keywords):
        self.keywords = keywords

    def set_language(self, language):
        self.language = language

    @property
    def persistent_identifier_scheme(self):
        return self.pid_scheme

    @persistent_identifier_scheme.setter
    def persistent_identifier_scheme(self, schemes):
        self.pid_scheme = schemes

    def add_persistent_identifier_scheme(self, scheme):
        self.add_pid_scheme(scheme)

    def subjects(self):
        return self.subject

    def set_subjects(self, subjects):
        self.subject = subjects

    def remove_subjects(self):
        del self.subject

    def set_archiving_policy(self, policies, policy_url):
        self.set_preservation(policies, policy_url)

    def add_archiving_policy(self, policy_name):
        self.add_preservation(policy_name)

    @property
    def flattened_archiving_policies(self):
        return [": ".join(p) if isinstance(p, list) else p for p in self.preservation_services]

    # vocab of known identifier types
    P_ISSN = "pissn"
    E_ISSN = "eissn"
    #DOI = "doi"

    IDENTIFIER_MAP = {
        P_ISSN : "pissn",
        E_ISSN : "eissn"
    }

    def add_identifier(self, idtype, value):
        field = self.IDENTIFIER_MAP.get(idtype)
        if field is not None:
            setattr(self, field, value)
            return
        raise RuntimeError("This object does not accept unrecognised identifier types")

    def get_identifiers(self, idtype=None):
        if idtype is None:
            idents = []
            if self.eissn:
                idents.append({"type" : self.E_ISSN, "id" : self.eissn})
            if self.pissn:
                idents.append({"type" : self.P_ISSN, "id" : self.pissn})
            return idents
        field = self.IDENTIFIER_MAP.get(idtype)
        if field is None:
            raise RuntimeError("No identifier of type {x} known".format(x=idtype))

        ident = getattr(self, field)
        if ident is not None:
            return [getattr(self, field)]
        return []

    def get_one_identifier(self, idtype=None):
        if idtype is None:
            raise RuntimeError("This object cannot return a generic identifier")
        results = self.get_identifiers(idtype=idtype)
        if len(results) > 0:
            return results[0]
        else:
            return None

    def _set_attr_with_no_check(self, name, value):
        self.__setattr__(name, value, allow_coerce_failure=True)

    # allowable values for the url types
    HOMEPAGE = "homepage"
    WAIVER_POLICY = "waiver_policy"
    EDITORIAL_BOARD = "editorial_board"
    AIMS_SCOPE = "aims_scope"
    AUTHOR_INSTRUCTIONS = "author_instructions"
    OA_STATEMENT = "oa_statement"
    #FULLTEXT = "fulltext"

    LINK_MAP = {
        HOMEPAGE: "journal_url",
        WAIVER_POLICY: "waiver_url",
        EDITORIAL_BOARD: "editorial_board_url",
        AIMS_SCOPE: "aims_scope_url",
        AUTHOR_INSTRUCTIONS: "author_instructions_url",
        OA_STATEMENT: "oa_statement_url"
    }

    def add_url(self, url, urltype=None, content_type=None):
        if url is None:
            # do not add empty URL-s
            return

        field = self.LINK_MAP.get(urltype)
        if field is not None:
            setattr(self, field, url)
            return
        raise RuntimeError("This object does not accept unrecognised url types")

    def get_urls(self, urltype=None, unpack_urlobj=True):
        if urltype is None:
            raise RuntimeError("This object cannot return lists of urls")

        field = self.LINK_MAP.get(urltype)
        if field is None:
            raise RuntimeError("No url of type {x} known".format(x=urltype))

        url = getattr(self, field)
        if unpack_urlobj:
            return [url]
        else:
            return [{"type" : urltype, "url" : url}]

    def get_single_url(self, urltype, unpack_urlobj=True):
        urls = self.get_urls(urltype=urltype, unpack_urlobj=unpack_urlobj)
        if len(urls) > 0:
            return urls[0]
        return None

    @property
    def first_pissn(self):
        return self.pissn

    @property
    def first_eissn(self):
        return self.eissn

    @property
    def country(self):
        return self.publisher_country

    @country.setter
    def country(self, val):
        self.publisher_country = val

    @property
    def open_access(self):
        return self.boai

    def set_open_access(self, open_access):
        self.boai = open_access

    def country_name(self):
        return self.publisher_country_name()

    #####################################################
    ## Incompatible functions from v1

    def set_license(self, license_title, license_type, url=None, version=None, open_access=None,
                    by=None, sa=None, nc=None, nd=None,
                    embedded=None, embedded_example_url=None):
        """
        # FIXME: why is there not a "remove license" function
        if not license_title and not license_type:  # something wants to delete the license
            self._delete("license")
            return

        lobj = {"title": license_title, "type": license_type}
        if url is not None:
            lobj["url"] = url
        if version is not None:
            lobj["version"] = version
        if open_access is not None:
            lobj["open_access"] = open_access
        if by is not None:
            lobj["BY"] = by
        if sa is not None:
            lobj["SA"] = sa
        if nc is not None:
            lobj["NC"] = nc
        if nd is not None:
            lobj["ND"] = nd
        if embedded is not None:
            lobj["embedded"] = embedded
        if embedded_example_url is not None:
            lobj["embedded_example_url"] = embedded_example_url

        self._set_with_struct("license", [lobj])
        """
        raise RuntimeError("set_license is not back compat")

    def get_license(self):
        """
        ll = self._get_list("license")
        if len(ll) > 0:
            return ll[0]
        return None
        """
        raise RuntimeError("get_license is not back compat")

    def get_license_type(self):
        """
        lobj = self.get_license()
        if lobj is not None:
            return lobj['type']
        return None
        """
        raise RuntimeError("get_lcense_type is not back compat")

    @property
    def editorial_review(self):
        """
        return self._get_single("editorial_review", default={})
        """
        raise RuntimeError("editorial_review is not back compat")

    @property
    def archiving_policy(self):
        """
        ap = self._get_single("archiving_policy", default={})
        ret = {"policy" : []}
        if "url" in ap:
            ret["url"] = ap["url"]
        if "known" in ap:
            ret["policy"] += ap["known"]
        if "nat_lib" in ap:
            ret["policy"].append(["A national library", ap["nat_lib"]])
        if "other" in ap:
            ret["policy"].append(["Other", ap["other"]])
        return ret
        """
        raise RuntimeError("archiving_policy is not back compat")

    def remove_identifiers(self, idtype=None, id=None):
        raise RuntimeError("remove_identifiers is not back compat")

    def remove_urls(self, urltype=None, url=None):
        raise RuntimeError("remove_urls is not back compat")

