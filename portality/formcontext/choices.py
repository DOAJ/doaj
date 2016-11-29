from portality.datasets import language_options, main_license_options, country_options, currency_options
from portality import lcc

class Choices(object):
    NONE = "None"
    TRUE = 'True'
    FALSE = 'False'
    OTHER = 'Other'

    _binary = [
        (TRUE, "Yes"),
        (FALSE, "No")
    ]

    _ternary = [
        (TRUE, "Yes"),
        (FALSE, "No"),
        (OTHER, OTHER)
    ]

    _digital_archiving_policy = [
        ("No policy in place", "No policy in place"),
        ('LOCKSS', 'LOCKSS'),
        ('CLOCKSS', 'CLOCKSS'),
        ('Portico', 'Portico'),
        ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'),
        ('A national library', 'A national library'),
        (OTHER, OTHER)
    ]

    _article_identifiers = [
        (NONE, NONE),
        ('DOI', 'DOI'),
        ('Handles', 'Handles'),
        ('ARK', 'ARK'),
        (OTHER, OTHER)
    ]

    _fulltext_format = [
        ('PDF', 'PDF'),
        ('HTML', 'HTML'),
        ('ePUB', 'ePUB'),
        ('XML', 'XML'),
        (OTHER, OTHER)
    ]

    _review_process = [
        ("", ""),
        ('Editorial review', 'Editorial review'),
        ('Peer review', 'Peer review'),
        ('Blind peer review', 'Blind peer review'),
        ('Double blind peer review', 'Double blind peer review'),
        ('Open peer review', 'Open peer review'),
        (NONE, NONE)
    ]

    _licence = main_license_options + [
        (OTHER, OTHER)
    ]

    _license_checkbox = [
        ('BY', 'Attribution'),
        ('NC', 'No Commercial Usage'),
        ('ND', 'No Derivatives'),
        ('SA', 'Share Alike'),
    ]

    _deposit_policy = [
        (NONE, NONE),
        ('Sherpa/Romeo', 'Sherpa/Romeo'),
        ('Dulcinea', 'Dulcinea'),
        ('H\xc3\xa9lo\xc3\xafse'.decode('utf-8'), 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8')),
        ('Diadorim', 'Diadorim'),
        (OTHER, OTHER)
    ]

    _author_pays = [
        ('N', 'No charges'),
        ('CON', 'Conditional charges'),
        ('Y', 'Has charges'),
        ('NY', 'No information'),
    ]

    _application_status_base = [        # This is all the Associate Editor sees
        ('', ' '),
        ('pending', 'Pending'),
        ('in progress', 'In Progress'),
        ('completed', 'Completed')
    ]

    _application_status_admin = _application_status_base + [
        ('reapplication', 'Reapplication Pending'),
        ('submitted', 'Reapplication Submitted'),
        ('on hold', 'On Hold'),
        ('ready', 'Ready'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted')
    ]

    _application_status_editor = _application_status_base + [
        ('ready', 'Ready'),
    ]

    _bulk_journal_article_actions = [
        ('', 'Select action...'),
        ('bulk.withdraw', 'Withdraw from DOAJ'),
        ('bulk.reinstate', 'Reinstate into DOAJ'),
        ('bulk.delete', 'Delete records'),
        ('bulk.editor_group', 'Assign to editor group...')
    ]

    _bulk_application_actions = [
        ('', 'Select action...'),
        ('bulk.change_status', 'Change status...'),
        ('bulk.editor_group', 'Assign to editor group...')
    ]

    ############################################################
    # General utility functions
    ############################################################

    @classmethod
    def basic(cls, val):
        return (val, val)

    @classmethod
    def binary(cls):
        return cls._binary

    @classmethod
    def ternary(cls):
        return cls._ternary

    @classmethod
    def ternary_list(cls):
        return [v[0] for v in cls._ternary]

    ############################################################
    # Loaded from datasets
    ############################################################

    @classmethod
    def country(cls):
        return country_options

    @classmethod
    def currency(cls):
        return currency_options

    @classmethod
    def language(cls):
        return language_options

    @classmethod
    def licence(cls):
        return cls._licence

    @classmethod
    def licence_list(cls):
        return [v[0] for v in cls._licence]

    @classmethod
    def subjects(cls):
        return lcc.lcc_choices

    ############################################################
    # Choices for specific fields
    ############################################################

    @classmethod
    def processing_charges(cls):
        return cls.binary()

    @classmethod
    def processing_charges_url_optional(cls):
        return [cls.FALSE]

    @classmethod
    def processing_charges_amount_optional(cls):
        return [cls.FALSE]

    @classmethod
    def processing_charges_currency_optional(cls):
        return [cls.FALSE]


    @classmethod
    def submission_charges(cls):
        return cls.binary()

    @classmethod
    def submission_charges_url_optional(cls):
        return [cls.FALSE]

    @classmethod
    def submission_charges_amount_optional(cls):
        return [cls.FALSE]

    @classmethod
    def submission_charges_currency_optional(cls):
        return [cls.FALSE]


    @classmethod
    def waiver_policy(cls):
        return cls.binary()

    @classmethod
    def waiver_policy_url_optional(cls):
        return [cls.FALSE]


    @classmethod
    def digital_archiving_policy(cls):
        return cls._digital_archiving_policy

    @classmethod
    def digital_archiving_policy_val(cls, type):
        if type == "none":
            return cls._digital_archiving_policy[0][0]
        elif type == "library":
            return cls._digital_archiving_policy[5][0]
        elif type == "other":
            return cls.OTHER

    @classmethod
    def digital_archiving_policy_label(cls, type):
        if type == "library":
            return cls._digital_archiving_policy[5][1]

    @classmethod
    def digital_archiving_policy_list(cls, type=None):
        if type is None:
            return [v[0] for v in cls._digital_archiving_policy]
        elif type == "named":
            return [v[0] for v in cls._digital_archiving_policy if v not in [cls.digital_archiving_policy_val("library"), cls.digital_archiving_policy_val("other")]]
        elif type == "optional":
            return [cls.digital_archiving_policy_val("library"), cls.digital_archiving_policy_val("other")]

    @classmethod
    def digital_archiving_policy_url_optional(cls):
        return cls._digital_archiving_policy[0]


    @classmethod
    def crawl_permission(cls):
        return cls.binary()


    @classmethod
    def article_identifiers(cls):
        return cls._article_identifiers

    @classmethod
    def article_identifiers_val(cls, type):
        if type == "other":
            return cls.OTHER

    @classmethod
    def article_identifiers_list(cls):
        return [v[0] for v in cls._article_identifiers]

    @classmethod
    def download_statistics(cls):
        return cls.binary()


    @classmethod
    def fulltext_format(cls):
        return cls._fulltext_format

    @classmethod
    def fulltext_format_val(cls, type):
        if type == "other":
            return cls.OTHER

    @classmethod
    def fulltext_format_list(cls):
        return [v[0] for v in cls._fulltext_format]

    @classmethod
    def review_process(cls):
        return cls._review_process

    @classmethod
    def review_process_default(cls):
        return cls._review_process[0][0]

    @classmethod
    def review_process_url_optional(cls):
        return ["", cls.NONE]


    @classmethod
    def plagiarism_screening(cls):
        return cls.binary()

    @classmethod
    def plagiarism_screening_url_optional(cls):
        return [cls.FALSE]


    @classmethod
    def licence_embedded(cls):
        return cls.binary()

    @classmethod
    def licence_embedded_url_optional(cls):
        return [cls.FALSE]

    @classmethod
    def licence_val(cls, type):
        if type == "other":
            return cls.OTHER

    @classmethod
    def licence_checkbox(cls):
        return cls._license_checkbox


    @classmethod
    def open_access(cls):
        return cls.binary()

    @classmethod
    def open_access_val(cls, type):
        if type == "other":
            return cls.OTHER


    @classmethod
    def deposit_policy(cls):
        return cls._deposit_policy

    @classmethod
    def deposit_policy_other_val(cls, type):
        if type == "other":
            return cls.OTHER

    @classmethod
    def deposit_policy_list(cls):
        return [v[0] for v in cls._deposit_policy]

    @classmethod
    def copyright(cls):
        return cls.binary()

    @classmethod
    def copyright_url_optional(cls):
        return [cls.FALSE]

    @classmethod
    def publishing_rights(cls):
        return cls.binary()

    @classmethod
    def publishing_rights_url_optional(cls):
        return [cls.FALSE]


    @classmethod
    def metadata_provision(cls):
        return cls.binary()


    @classmethod
    def author_pays(cls):
        return cls._author_pays

    @classmethod
    def application_status_optional(cls):
        all_s = [v[0] for v in cls._application_status_admin]
        all_s.remove("accepted")
        return all_s

    @classmethod
    def application_status(cls, context=None):
        if context == "admin":
            return cls._application_status_admin
        elif context == "editor":
            return cls._application_status_editor
        elif context == "accepted":
            return [('accepted', 'Accepted')] # just the one status - Accepted
        else:
            return cls._application_status_base

    @classmethod
    def application_status_subject_optional(cls):
        """ The set of permitted statuses we can save an application without a subject classification """
        all_s = [v[0] for v in cls._application_status_admin]
        disallowed_statuses = {'accepted', 'ready', 'completed'}
        return list(set(all_s).difference(disallowed_statuses))

    @classmethod
    def bulk_journal_article_actions(cls):
        return cls._bulk_journal_article_actions

    @classmethod
    def bulk_journal_article_actions_val(cls, type):
        if type == 'editor_group':
            return cls._bulk_journal_article_actions[4][0]

    @classmethod
    def bulk_journal_article_actions_default(cls):
        return cls._bulk_journal_article_actions[0][0]

    @classmethod
    def bulk_application_actions(cls):
        return cls._bulk_application_actions

    @classmethod
    def bulk_application_actions_val(cls, type):
        if type == 'change_status':
            return cls._bulk_journal_article_actions[1][0]
        elif type == 'editor_group':
            return cls._bulk_journal_article_actions[2][0]

    @classmethod
    def bulk_application_actions_default(cls):
        return cls._bulk_application_actions[0][0]
