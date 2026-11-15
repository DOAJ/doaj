from formulaic.core import Structure, Field, FieldCapability, SINGLE, OPTIONAL, REPEATABLE
from formulaic.serialise.form.controls import Radio, TextInput, NumberInput, Checkbox
from formulaic.serialise.form.core import CompoundFieldCapability, FormFieldCapability
from portality.forms.workflow.core import JinjaCompoundRenderer, GenericROCompoundFieldRenderer, GenericROFieldRenderer, \
    GenericROControlRenderer, GenericRORadioRenderer, GenericElementList, ListEntryROFieldRenderer, \
    InlineROCompoundFieldRenderer, JustControlROFieldRenderer
from portality.forms.application_forms import FieldDefinitions, FieldSetDefinitions


def map_legacy_options(options):
    return [{"value": o.get("value"), "label": o.get("display")} for o in options]


##############################################
## Basic Compliance

class BOAI(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.BOAI.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.BOAI.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "boai"
    capabilities = (C(),)

class OAStatementURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.OA_STATEMENT_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "oa_statement_url"
    capabilities = (C(),)

class OAStart(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.OA_START.get("label")
        control_class = NumberInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "oa_start"
    capabilities = (C(),)

class BasicCompliance(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.BASIC_COMPLIANCE.get("label")
        order = [
            "boai",
            "oa_statement_url",
            "oa_start"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "basic_compliance"
    capabilities_ = (C(),)

    boai = BOAI(OPTIONAL, SINGLE)
    oa_statement_url = OAStatementURL(OPTIONAL, SINGLE)
    oa_start = OAStart(OPTIONAL, SINGLE)

##############################################
## About the Journal

class Title(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.TITLE.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "title"
    capabilities = (C(),)

class AlternativeTitle(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.ALTERNATIVE_TITLE.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "alternative_title"
    capabilities = (C(),)

class JournalURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.JOURNAL_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "journal_url"
    capabilities = (C(),)

class PISSN(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PISSN.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "pissn"
    capabilities = (C(),)

class EISSN(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.EISSN.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "eissn"
    capabilities = (C(),)

class Language(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LANGUAGE.get("label")
        repeatable_label = FieldDefinitions.LANGUAGE.get("label")
        control_class = TextInput   # In reality is a select box
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericROControlRenderer

    name = "language"
    capabilities = (C(),)

class Keywords(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.KEYWORDS.get("label")
        repeatable_label = FieldDefinitions.KEYWORDS.get("label")
        control_class = TextInput
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericROControlRenderer

    name = "keywords"
    capabilities = (C(),)

class About(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.ABOUT_THE_JOURNAL_EXTENDED.get("label")
        order = [
            "title",
            "alternative_title",
            "journal_url",
            "pissn",
            "eissn",
            "language",
            "keywords"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "about_the_journal_extended"
    capabilities_ = (C(),)

    title = Title(OPTIONAL, SINGLE)
    alternative_title = AlternativeTitle(OPTIONAL, SINGLE)
    journal_url = JournalURL(OPTIONAL, SINGLE)
    pissn = PISSN(OPTIONAL, SINGLE)
    eissn = EISSN(OPTIONAL, SINGLE)
    language = Language(OPTIONAL, REPEATABLE)
    keywords = Keywords(OPTIONAL, REPEATABLE)   # Check this

##########################################
## Publisher

class PublisherName(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PUBLISHER_NAME.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "publisher_name"
    capabilities = (C(),)

class PublisherCountry(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PUBLISHER_COUNTRY.get("label")
        control_class = TextInput   # in reality is a select box
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "publisher_country"
    capabilities = (C(),)

class Publisher(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.PUBLISHER.get("label")
        order = [
            "publisher_name",
            "publisher_country"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "publisher"
    capabilities_ = (C(),)

    publisher_name = PublisherName(OPTIONAL, SINGLE)
    publisher_country = PublisherCountry(OPTIONAL, SINGLE)

################################################
## Society or Institution

class InstitutionName(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.INSTITUTION_NAME.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "institution_name"
    capabilities = (C(),)

class InstitutionCountry(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.INSTITUTION_COUNTRY.get("label")
        control_class = TextInput   # in reality is a select box
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "institution_country"
    capabilities = (C(),)

class Institution(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.SOCIETY_OR_INSTITUTION.get("label")
        order = [
            "institution_name",
            "institution_country"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "society_or_institution"
    capabilities_ = (C(),)

    institution_name = InstitutionName(OPTIONAL, SINGLE)
    institution_country = InstitutionCountry(OPTIONAL, SINGLE)

######################################
## Licensing

class License(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LICENSE.get("label")
        repeatable_label = FieldDefinitions.LICENSE.get("label")
        control_class = Checkbox
        options = map_legacy_options(FieldDefinitions.LICENSE.get("options"))
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericRORadioRenderer

    name = "license"
    capabilities = (C(),)

class LicenseAttributes(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LICENSE_ATTRIBUTES.get("label")
        repeatable_label = FieldDefinitions.LICENSE_ATTRIBUTES.get("label")
        control_class = Checkbox
        options = map_legacy_options(FieldDefinitions.LICENSE_ATTRIBUTES.get("options"))
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericRORadioRenderer

    name = "license_attributes"
    capabilities = (C(),)

class LicenseTermsURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LICENSE_TERMS_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "license_terms_url"
    capabilities = (C(),)

class Licensing(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.LICENSING.get("label")
        order = [
            "license",
            "license_attributes",
            "license_terms_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "licensing"
    capabilities_ = (C(),)

    license = License(OPTIONAL, REPEATABLE)
    license_attributes = LicenseAttributes(OPTIONAL, REPEATABLE)
    license_terms_url = LicenseTermsURL(OPTIONAL, SINGLE)

#############################################
## Embedded Licensing

class LicenseDisplay(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LICENSE_DISPLAY.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.LICENSE_DISPLAY.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "license_display"
    capabilities = (C(),)

class LicenseDisplayExampleURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.LICENSE_DISPLAY_EXAMPLE_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "license_display_example_url"
    capabilities = (C(),)

class EmbeddedLicensing(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.EMBEDDED_LICENSING.get("label")
        order = [
            "license_display",
            "license_display_example_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "embedded_licensing"
    capabilities_ = (C(),)

    license_display = LicenseDisplay(OPTIONAL, SINGLE)
    license_display_example_url = LicenseDisplayExampleURL(OPTIONAL, SINGLE)

#####################################
## Copyright

class AuthorRetainsCopyright(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.COPYRIGHT_AUTHOR_RETAINS.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.COPYRIGHT_AUTHOR_RETAINS.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "author_retains_copyright"
    capabilities = (C(),)

class CopyrightURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.COPYRIGHT_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "copyright_url"
    capabilities = (C(),)

class Copyright(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.COPYRIGHT.get("label")
        order = [
            "author_retains_copyright",
            "copyright_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "copyright"
    capabilities_ = (C(),)

    author_retains_copyright = AuthorRetainsCopyright(OPTIONAL, SINGLE)
    copyright_url = CopyrightURL(OPTIONAL, SINGLE)

##########################################
## Peer Review

class ReviewProcess(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.REVIEW_PROCESS.get("label")
        repeatable_label = FieldDefinitions.REVIEW_PROCESS.get("label")
        control_class = Checkbox
        options = map_legacy_options(FieldDefinitions.REVIEW_PROCESS.get("options"))
        list_render_class = GenericElementList
        render_class = ListEntryROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "review_process"
    capabilities = (C(),)

class ReviewProcessOther(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.REVIEW_PROCESS_OTHER.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "review_process_other"
    capabilities = (C(),)

class ReviewURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.REVIEW_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "review_url"
    capabilities = (C(),)

class PeerReview(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.PEER_REVIEW.get("label")
        order = [
            "review_process",
            "review_process_other",
            "review_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "peer_review"
    capabilities_ = (C(),)

    review_process = ReviewProcess(OPTIONAL, REPEATABLE)
    review_process_other = ReviewProcessOther(OPTIONAL, SINGLE)
    review_url = ReviewURL(OPTIONAL, SINGLE)

##############################################
## Editorial

class AimsScopeURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.AIMS_SCOPE_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "aims_scope_url"
    capabilities = (C(),)

class EditorialBoardURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.EDITORIAL_BOARD_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "editorial_board_url"
    capabilities = (C(),)

class AuthorInstructionsURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.AUTHOR_INSTRUCTIONS_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "author_instructions_url"
    capabilities = (C(),)

class PublicationTimeWeeks(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PUBLICATION_TIME_WEEKS.get("label")
        control_class = NumberInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "publication_time_weeks"
    capabilities = (C(),)

class EditorialURLs(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.EDITORIAL.get("label")
        order = [
            "aims_scope_url",
            "editorial_board_url",
            "author_instructions_url",
            "publication_time_weeks"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "editorial"
    capabilities_ = (C(),)

    aims_scope_url = AimsScopeURL(OPTIONAL, SINGLE)
    editorial_board_url = EditorialBoardURL(OPTIONAL, SINGLE)
    author_instructions_url = AuthorInstructionsURL(OPTIONAL, SINGLE)
    publication_time_weeks = PublicationTimeWeeks(OPTIONAL, SINGLE)

#######################################
##

class HasAPC(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.APC.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.APC.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "has_apc"
    capabilities = (C(),)

class APCCurrency(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.APC_CURRENCY.get("label")
        control_class = TextInput # in reality is a select box
        render_class = JustControlROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "apc_currency"
    capabilities = (C(),)

class APCMax(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.APC_MAX.get("label")
        control_class = NumberInput
        render_class = JustControlROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "apc_max"
    capabilities = (C(),)

class APCCharges(Structure):
    class C(CompoundFieldCapability):
        label = FieldDefinitions.APC_CHARGES.get("label")
        repeatable_label = FieldDefinitions.APC_CHARGES.get("label")
        order = [
            "apc_max",
            "apc_currency"
        ]
        list_render_class = GenericElementList
        render_class = InlineROCompoundFieldRenderer

    name_ = "apc_charges"
    capabilities_ = (C(),)

    apc_max = APCMax(OPTIONAL, SINGLE)
    apc_currency = APCCurrency(OPTIONAL, SINGLE)

class APCURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.APC_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "apc_url"
    capabilities = (C(),)

class APC(Structure):
    class C(CompoundFieldCapability):
        label = FieldDefinitions.APC.get("label")
        order = [
            "has_apc",
            "apc_charges",
            "apc_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "apc"
    capabilities_ = (C(),)

    has_apc = HasAPC(OPTIONAL, SINGLE)
    apc_charges = APCCharges(OPTIONAL, REPEATABLE)
    apc_url = APCURL(OPTIONAL, SINGLE)

###########################################
## APC Waiver

class HasWaiver(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.HAS_WAIVER.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.HAS_WAIVER.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "has_waiver"
    capabilities = (C(),)

class WaiverURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.WAIVER_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "waiver_url"
    capabilities = (C(),)

class APCWaivers(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.APC_WAIVERS.get("label")
        order = [
            "has_waiver",
            "waiver_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "apc_waivers"
    capabilities_ = (C(),)

    has_waiver = HasWaiver(OPTIONAL, SINGLE)
    waiver_url = WaiverURL(OPTIONAL, SINGLE)

###############################################
## Other Fees

class HasOtherCharges(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.HAS_OTHER_CHARGES.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.HAS_OTHER_CHARGES.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "has_other_charges"
    capabilities = (C(),)

class OtherChargesURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.OTHER_CHARGES_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "other_charges_url"
    capabilities = (C(),)

class OtherFees(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.OTHER_FEES.get("label")
        order = [
            "has_other_charges",
            "other_charges_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "other_fees"
    capabilities_ = (C(),)

    has_other_charges = HasOtherCharges(OPTIONAL, SINGLE)
    other_charges_url = OtherChargesURL(OPTIONAL, SINGLE)

########################################
## Archiving Policy

class PreservationService(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PRESERVATION_SERVICE.get("label")
        repeatable_label = FieldDefinitions.PRESERVATION_SERVICE.get("label")
        control_class = Checkbox
        options = map_legacy_options(FieldDefinitions.PRESERVATION_SERVICE.get("options"))
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericRORadioRenderer

    name = "preservation_service"
    capabilities = (C(),)

class PreservationServiceLibrary(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PRESERVATION_SERVICE_LIBRARY.get("label")
        repeatable_label = FieldDefinitions.PRESERVATION_SERVICE_LIBRARY.get("label")
        control_class = TextInput
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericROControlRenderer

    name = "preservation_service_library"
    capabilities = (C(),)

class PreservationServiceOther(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PRESERVATION_SERVICE_OTHER.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "preservation_service_other"
    capabilities = (C(),)

class PreservationServiceURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PRESERVATION_SERVICE_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "preservation_service_url"
    capabilities = (C(),)

class ArchivingPolicy(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.ARCHIVING_POLICY.get("label")
        order = [
            "preservation_service",
            "preservation_service_library",
            "preservation_service_other",
            "preservation_service_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "archiving_policy"
    capabilities_ = (C(),)

    preservation_service = PreservationService(OPTIONAL, REPEATABLE)
    preservation_service_library = PreservationServiceLibrary(OPTIONAL, REPEATABLE)
    preservation_service_other = PreservationServiceOther(OPTIONAL, SINGLE)
    preservation_service_url = PreservationServiceURL(OPTIONAL, SINGLE)

#############################################
## Repository Policy

class DepositPolicy(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.DEPOSIT_POLICY.get("label")
        repeatable_label = FieldDefinitions.DEPOSIT_POLICY.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.DEPOSIT_POLICY.get("options"))
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericRORadioRenderer

    name = "deposit_policy"
    capabilities = (C(),)

class DepositPolicyOther(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.DEPOSIT_POLICY_OTHER.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "deposit_policy_other"
    capabilities = (C(),)

class DepositPolicyURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.DEPOSIT_POLICY_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "deposit_policy_url"
    capabilities = (C(),)

class RepositoryPolicy(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.REPOSITORY_POLICY.get("label")
        order = [
            "deposit_policy",
            "deposit_policy_other",
            "deposit_policy_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "repository_policy"
    capabilities_ = (C(),)

    deposit_policy = DepositPolicy(OPTIONAL, REPEATABLE)
    deposit_policy_other = DepositPolicyOther(OPTIONAL, SINGLE)
    deposit_policy_url = DepositPolicyURL(OPTIONAL, SINGLE)

##########################################
## Unique Identifiers

class PersistentIdentifiers(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PERSISTENT_IDENTIFIERS.get("label")
        repeatable_label = FieldDefinitions.PERSISTENT_IDENTIFIERS.get("label")
        control_class = Checkbox
        options = map_legacy_options(FieldDefinitions.PERSISTENT_IDENTIFIERS.get("options"))
        render_class = ListEntryROFieldRenderer
        list_render_class = GenericElementList
        control_render_class = GenericRORadioRenderer

    name = "persistent_identifier"
    capabilities = (C(),)

class PersistentIdentifiersOther(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PERSISTENT_IDENTIFIERS_OTHER.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "persistent_identifier_other"
    capabilities = (C(),)

class UniqueIdentifiers(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.UNIQUE_IDENTIFIERS.get("label")
        order = [
            "persistent_identifiers",
            "persistent_identifiers_other"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "unique_identifiers"
    capabilities_ = (C(),)

    persistent_identifiers = PersistentIdentifiers(OPTIONAL, REPEATABLE)
    persistent_identifiers_other = PersistentIdentifiersOther(OPTIONAL, SINGLE)

###########################################
## Plagiarism

class PlagiarismDetection(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PLAGIARISM_DETECTION.get("label")
        control_class = Radio
        options = map_legacy_options(FieldDefinitions.PLAGIARISM_DETECTION.get("options"))
        render_class = GenericROFieldRenderer
        control_render_class = GenericRORadioRenderer

    name = "plagiarism_detection"
    capabilities = (C(),)

class PlagiarismURL(Field):
    class C(FormFieldCapability):
        label = FieldDefinitions.PLAGIARISM_URL.get("label")
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "plagiarism_url"
    capabilities = (C(),)

class Plagiarism(Structure):
    class C(CompoundFieldCapability):
        label = FieldSetDefinitions.PLAGIARISM.get("label")
        order = [
            "plagiarism_detection",
            "plagiarism_url"
        ]
        render_class = GenericROCompoundFieldRenderer

    name_ = "plagiarism"
    capabilities_ = (C(),)

    plagiarism_detection = PlagiarismDetection(OPTIONAL, SINGLE)
    plagiarism_url = PlagiarismURL(OPTIONAL, SINGLE)