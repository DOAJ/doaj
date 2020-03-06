from portality import constants
from portality import lcc
from portality.datasets import language_options, main_license_options, country_options, currency_options, CURRENCY_DEFAULT
from portality.formcontext import FormContextException


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
        ('CINES', 'CINES'),
        ('CLOCKSS', 'CLOCKSS'),
        ('LOCKSS', 'LOCKSS'),
        ('PKP PN', 'PKP PN'),
        ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'),
        ('Portico', 'Portico'),
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
        ('Héloïse', 'Héloïse'),
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
        (constants.APPLICATION_STATUS_PENDING, 'Pending'),
        (constants.APPLICATION_STATUS_IN_PROGRESS, 'In Progress'),
        (constants.APPLICATION_STATUS_COMPLETED, 'Completed')
    ]

    _application_status_admin = _application_status_base + [
        (constants.APPLICATION_STATUS_UPDATE_REQUEST, 'Update Request'),
        (constants.APPLICATION_STATUS_REVISIONS_REQUIRED, 'Revisions Required'),
        (constants.APPLICATION_STATUS_ON_HOLD, 'On Hold'),
        (constants.APPLICATION_STATUS_READY, 'Ready'),
        (constants.APPLICATION_STATUS_REJECTED, 'Rejected'),
        (constants.APPLICATION_STATUS_ACCEPTED, 'Accepted')
    ]

    _application_status_editor = _application_status_base + [
        (constants.APPLICATION_STATUS_READY, 'Ready'),
    ]

    ############################################################
    # General utility functions
    ############################################################

    @classmethod
    def basic(cls, val):
        return val, val

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
    def currency_default(cls):
        return CURRENCY_DEFAULT

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
            return cls._digital_archiving_policy[7][0]
        elif type == "other":
            return cls.OTHER

    @classmethod
    def digital_archiving_policy_label(cls, type):
        if type == "library":
            return cls._digital_archiving_policy[7][1]

    @classmethod
    def digital_archiving_policy_list(cls, type=None):
        if type is None:
            return [v[0] for v in cls._digital_archiving_policy]
        elif type == "named":
            return [v[0] for v in cls._digital_archiving_policy if v[0] not in [cls.digital_archiving_policy_val("library"), cls.digital_archiving_policy_val("other")]]
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
        all_s.remove(constants.APPLICATION_STATUS_ACCEPTED)
        return all_s

    @classmethod
    def application_status(cls, context=None):
        if context == "admin":
            return cls._application_status_admin
        elif context == "editor":
            return cls._application_status_editor
        elif context == "accepted":
            return [(constants.APPLICATION_STATUS_ACCEPTED, 'Accepted')] # just the one status - Accepted
        else:
            return cls._application_status_base

    @classmethod
    def application_status_subject_optional(cls):
        """ The set of permitted statuses we can save an application without a subject classification """
        all_s = [v[0] for v in cls._application_status_admin]
        disallowed_statuses = {constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_READY, constants.APPLICATION_STATUS_COMPLETED}
        return list(set(all_s).difference(disallowed_statuses))

    @classmethod
    def validate_status_change(cls, role, source_status, target_status):
        """ Check whether the editorial pipeline permits a change to the target status for a role.
        Don't run this for admins, since they can change to any role at any time. """
        choices_for_role = list(sum(cls.application_status(role), ()))                     # flattens the list of tuples

        # Don't allow edits to application when status is beyond this user's permissions in the pipeline
        if source_status not in choices_for_role:
            raise FormContextException(
                "You don't have permission to edit applications which are in status {0}.".format(source_status))

        # Don't permit changes to status in reverse of the editorial process
        if choices_for_role.index(target_status) < choices_for_role.index(source_status):
            # Except that editors can revert 'completed' to 'in progress'
            if role == 'editor' and source_status == constants.APPLICATION_STATUS_COMPLETED and target_status == constants.APPLICATION_STATUS_IN_PROGRESS:
                pass
            else:
                raise FormContextException(
                    "You are not permitted to revert the application status from {0} to {1}.".format(source_status,
                                                                                                     target_status))

    @classmethod
    def choices_for_status(cls, role, status):
        """ :raises ValueError if status is outwith role's permitted statuses """

        role_choices = cls.application_status(role)

        # Get the full tuple of application status for the current source
        [full_current_status] = filter(lambda x: status in x, role_choices)

        # Admins can set any role at any time
        if role == 'admin':
            return role_choices
        else:
            # Show options forward in the editorial pipeline for users other than admins
            forward_choices = role_choices[role_choices.index(full_current_status):]

            # But allow an exception: Editors can revert to 'in progress' from 'completed'
            if role == 'editor' and status == constants.APPLICATION_STATUS_COMPLETED:
                forward_choices = [(constants.APPLICATION_STATUS_IN_PROGRESS, 'In Progress')] + forward_choices

            return forward_choices
