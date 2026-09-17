from formulaic.core import Structure, OPTIONAL, SINGLE
from formulaic.serialise.form.core import FieldsetCapability
from portality.forms.workflow.core import GenericROFieldsetRenderer
from portality.forms.workflow.submission.fields import BasicCompliance, About, Publisher, Institution, Licensing, \
    EmbeddedLicensing, Copyright, PeerReview, EditorialURLs, APC, APCWaivers, OtherFees, ArchivingPolicy, \
    RepositoryPolicy, UniqueIdentifiers, Plagiarism


class OACompliance(Structure):
    class C(FieldsetCapability):
        label = "Open Access Compliance"
        order = [
            "basic_compliance"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "oa_compliance"
    capabilities_ = (C(),)

    basic_compliance = BasicCompliance(OPTIONAL, SINGLE)

class AboutTheJournal(Structure):
    class C(FieldsetCapability):
        label = "About the Journal"
        order = [
            "about",
            "publisher",
            "institution"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "about_the_journal"
    capabilities_ = (C(),)

    about = About(OPTIONAL, SINGLE)
    publisher = Publisher(OPTIONAL, SINGLE)
    institution = Institution(OPTIONAL, SINGLE)

class CopyrightLicensing(Structure):
    class C(FieldsetCapability):
        label = "Copyright & Licensing"
        order = [
            "licensing",
            "embedded_licensing",
            "copyright"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "copyright_licensing"
    capabilities_ = (C(),)

    licensing = Licensing(OPTIONAL, SINGLE)
    embedded_licensing = EmbeddedLicensing(OPTIONAL, SINGLE)
    copyright = Copyright(OPTIONAL, SINGLE)

class Editorial(Structure):
    class C(FieldsetCapability):
        label = "Editorial"
        order = [
            "peer_review",
            "editorial"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "editorial"
    capabilities_ = (C(),)

    peer_review = PeerReview(OPTIONAL, SINGLE)
    editorial = EditorialURLs(OPTIONAL, SINGLE)

class BusinessModel(Structure):
    class C(FieldsetCapability):
        label = "Business Model"
        order = [
            "apc",
            "apc_waivers",
            "other_fees"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "business_model"
    capabilities_ = (C(),)

    apc = APC(OPTIONAL, SINGLE)
    apc_waivers = APCWaivers(OPTIONAL, SINGLE)
    other_fees = OtherFees(OPTIONAL, SINGLE)

class BestPractices(Structure):
    class C(FieldsetCapability):
        label = "Best Practices"
        order = [
            "archiving_policy",
            "repository_policy",
            "unique_identifiers",
            "plagiarism_detection"
        ]
        render_class = GenericROFieldsetRenderer

    name_ = "best_practices"
    capabilities_ = (C(),)

    archiving_policy = ArchivingPolicy(OPTIONAL, SINGLE)
    repository_policy = RepositoryPolicy(OPTIONAL, SINGLE)
    unique_identifiers = UniqueIdentifiers(OPTIONAL, SINGLE)
    plagiarism_detection = Plagiarism(OPTIONAL, SINGLE)