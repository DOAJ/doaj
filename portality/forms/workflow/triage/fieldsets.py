from formulaic.core import Structure, SINGLE, OPTIONAL
from formulaic.serialise.form.core import FieldsetCapability
from portality.forms.workflow.core import GenericFieldset
from portality.forms.workflow.triage.fields import EthicsNotExcludedGroup, EthicsNoNonStandardMetricsGroup, \
    EthicsNoFakeImpactGroup, EthicsNoFalseDOAJClaimGroup, \
    EthicsNoSuspiciousTiesGroup, ISSNAtLeastOneGroup, \
    DatabaseWithdrawnGroup, DatabaseEmbargoGroup, DatabaseNotListedGroup, DatabaseNotDuplicateGroup, \
    ISSNTitleMatchGroup, ISSNContinuationGroup, WebsiteWorkingGroup, WebsiteISSNGroup, WebsiteURLGroup, \
    WebsiteLicensePolicyGroup, WebsiteCopyrightGroup, ContentNoLoginGroup, \
    ContentNoEmbargoGroup, ContentPublishEnoughGroup, ContentUniqueLinkGroup, ContentFormatGroup, \
    ContentNewJournalGroup, AdminMetadataReviewGroup, AdminSpecialExceptionGroup, EthicsPubTimeGroup, ISSNCountryMatchGroup


class EthicsCriteria(Structure):
    class C(FieldsetCapability):
        label = "Ethics criteria"
        order = [
            "not_excluded",
            "no_nonstandard_metrics",
            "no_fake_impact",
            "no_false_doaj_claim",
            "publication_time",
            "no_suspicious_ties",
        ]
        render_class = GenericFieldset

    name_ = "ethics_criteria"
    capabilities_ = (C(),)

    not_excluded = EthicsNotExcludedGroup(OPTIONAL, SINGLE)
    no_nonstandard_metrics = EthicsNoNonStandardMetricsGroup(OPTIONAL, SINGLE)
    no_fake_impact = EthicsNoFakeImpactGroup(OPTIONAL, SINGLE)
    no_false_doaj_claim = EthicsNoFalseDOAJClaimGroup(OPTIONAL, SINGLE)
    publication_time = EthicsPubTimeGroup(OPTIONAL, SINGLE)
    no_suspicious_ties = EthicsNoSuspiciousTiesGroup(OPTIONAL, SINGLE)

class Database(Structure):
    class C(FieldsetCapability):
        label = "DOAJ Database"
        order = [
            "withdrawn",
            #"withdrawn_exception_ignore_embargo",
            #"withdrawn_exception_website_unavailable",
            #"withdrawn_exception_content",
            "embargo",
            # "embargo_exception_issn",
            # "embargo_exception_maned",
            # "embargo_exception_website",
            # "embargo_exception_content",
            "not_listed",
            "not_duplicate"
        ]
        render_class = GenericFieldset

    name_ = "database"
    capabilities_ = (C(),)

    withdrawn = DatabaseWithdrawnGroup(OPTIONAL, SINGLE)
    #withdrawn_exception_ignore_embargo = DatabaseWithdrawnIgnoreEmbargoGroup(OPTIONAL, SINGLE)
    #withdrawn_exception_website_unavailable = DatabaseWithdrawnWebsiteUnavailableGroup(OPTIONAL, SINGLE)
    #withdrawn_exception_content = DatabaseWithdrawnContentGroup(OPTIONAL, SINGLE)
    embargo = DatabaseEmbargoGroup(OPTIONAL, SINGLE)
    # embargo_exception_issn = DatabaseEmbargoISSNGroup(OPTIONAL, SINGLE)
    # embargo_exception_maned = DatabaseEmbargoManedGroup(OPTIONAL, SINGLE)
    # embargo_exception_website = DatabaseEmbargoWebsiteGroup(OPTIONAL, SINGLE)
    # embargo_exception_content = DatabaseEmbargoContentGroup(OPTIONAL, SINGLE)
    not_listed = DatabaseNotListedGroup(OPTIONAL, SINGLE)
    not_duplicate = DatabaseNotDuplicateGroup(OPTIONAL, SINGLE)

class ISSN(Structure):
    class C(FieldsetCapability):
        label = "ISSN"
        order = [
            "at_least_one",
            "country_match",
            "title_match",
            "continuation"
        ]
        render_class = GenericFieldset

    name_ = "issn"
    capabilities_ = (C(),)

    at_least_one = ISSNAtLeastOneGroup(OPTIONAL, SINGLE)
    country_match = ISSNCountryMatchGroup(OPTIONAL, SINGLE)
    title_match = ISSNTitleMatchGroup(OPTIONAL, SINGLE)
    continuation = ISSNContinuationGroup(OPTIONAL, SINGLE)

class Website(Structure):
    class C(FieldsetCapability):
        label = "Website"
        order = [
            "working",
            "issn",
            "url",
            "license_policy",
            "copyright"
        ]
        render_class = GenericFieldset

    name_ = "website"
    capabilities_ = (C(),)

    working = WebsiteWorkingGroup(OPTIONAL, SINGLE)
    issn = WebsiteISSNGroup(OPTIONAL, SINGLE)
    url = WebsiteURLGroup(OPTIONAL, SINGLE)
    license_policy = WebsiteLicensePolicyGroup(OPTIONAL, SINGLE)
    copyright = WebsiteCopyrightGroup(OPTIONAL, SINGLE)

class Content(Structure):
    class C(FieldsetCapability):
        label = "Journal Content"
        order = [
            "no_login",
            "no_embargo",
            "publish_enough",
            "unique_link",
            "format",
            "new_journal"
        ]
        render_class = GenericFieldset

    name_ = "content"
    capabilities_ = (C(),)

    no_login = ContentNoLoginGroup(OPTIONAL, SINGLE)
    no_embargo = ContentNoEmbargoGroup(OPTIONAL, SINGLE)
    publish_enough = ContentPublishEnoughGroup(OPTIONAL, SINGLE)
    unique_link = ContentUniqueLinkGroup(OPTIONAL, SINGLE)
    format = ContentFormatGroup(OPTIONAL, SINGLE)
    new_journal = ContentNewJournalGroup(OPTIONAL, SINGLE)

class SpecialException(Structure):
    class C(FieldsetCapability):
        label = "Special Exception"
        order = [
            "special_exception"
        ]
        render_class = GenericFieldset

    name_ = "special_exception"
    capabilities_ = (C(),)

    special_exception = AdminSpecialExceptionGroup(OPTIONAL, SINGLE)

class MetadataReview(Structure):
    class C(FieldsetCapability):
        label = "Admin"
        order = [
            "metadata_review"
        ]
        render_class = GenericFieldset

    name_ = "metadata_review"
    capabilities_ = (C(),)

    metadata_review = AdminMetadataReviewGroup(OPTIONAL, SINGLE)