# DEPRECATED

from datetime import datetime

from flask_login import current_user
from wtforms import Form, validators
from wtforms import StringField, TextAreaField, BooleanField, FormField, FieldList, RadioField
from wtforms.fields.html5 import IntegerField
from wtforms import widgets

from portality import regex
from portality.core import app

from portality.formcontext.fields import DOAJSelectField, DOAJSelectMultipleField, URLField, TagListField, DisabledTextField, PermissiveSelectField, OptionalRadioField
from portality.forms.validate import HTTPURL, OptionalIf, ExclusiveCheckbox, ExtraFieldRequiredIf, \
    MaxLen, RegexpOnTagList, ReservedUsernames, ThisOrThat

from portality.formcontext.choices import Choices

ISSN_REGEX = regex.ISSN_COMPILED
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'
EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'
BIG_END_DATE_REGEX = regex.BIG_END_DATE_COMPILED
DATE_ERROR = "Date must be supplied in the form YYYY-MM-DD"


###########################################################################
# Definition of the form components
###########################################################################


class JournalInformation(Form):
    """All the bibliographic metadata associated with a journal in the DOAJ"""

    title = StringField('Journal Title', [validators.DataRequired()])
    url = URLField('URL', [validators.DataRequired(), HTTPURL()])
    alternative_title = StringField('Alternative Title', [validators.Optional()])
    pissn = StringField('Journal ISSN (print version)',
                        [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
                        description='Only provide the print ISSN if your journal has one, otherwise leave this field blank. Write the ISSN with the hyphen "-" e.g. 1234-4321.',
                        )
    eissn = StringField('Journal ISSN (online version)',
                        [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
                        description='Cannot be the same as the P-ISSN. Write the EISSN with the hyphen "-" e.g. 1234-4321.',
                        )
    publisher = StringField('Publisher',
                            [validators.DataRequired()]
                            )
    society_institution = StringField('Society or Institution',
                                      [validators.Optional()],
                                      description='The name of the Society or Institution that the journal belongs to.',
                                      )
    # platform = StringField('Platform, Host or Aggregator',
    #     [validators.Optional()],
    #     description='The name of the platform, host or aggregator of the journal content, e.g. OJS, HighWire Press, EBSCO etc.'
    # )
    contact_name = StringField('Name of contact for this journal',
                               [validators.DataRequired()],
                               description='Somebody who DOAJ can contact about this journal.',
                               )
    contact_email = StringField('Contact\'s email address',
                                [validators.DataRequired(), validators.Email(message='Invalid email address.')]
                                )
    confirm_contact_email = StringField('Confirm contact\'s email address',
                                        [validators.DataRequired(), validators.Email(message='Invalid email address.'),
                                         validators.EqualTo('contact_email', EMAIL_CONFIRM_ERROR)]
                                        )
    country = DOAJSelectField('In which country is the publisher of the journal based?',
                              [validators.DataRequired()],
                              description='Select the country where the publishing company carries out its business activities. Addresses registered via a registered agent are not allowed.',
                              choices=Choices.country(),
                              )
    # processing_charges = RadioField('Does the journal have article processing charges (APCs)?',
    #                                 [validators.DataRequired()],
    #                                 # description = 'If "No" proceed to question below',
    #                                 choices=Choices.processing_charges()
    #                                 )
    processing_charges_url = URLField('Enter the URL where this information can be found',
                                      [validators.DataRequired(), HTTPURL()],
                                      # description='This field is optional if you have selected "No" above'
                                      )
    processing_charges_amount = IntegerField('Amount',
                                             [validators.Optional()],
                                             )
    processing_charges_currency = DOAJSelectField('Currency',
                                                  [validators.Optional()],
                                                  choices=Choices.currency()
                                                  )

    # submission_charges = RadioField('Does the journal have article submission charges?',
    #                                 [validators.DataRequired()],
    #                                 # description = 'If "No" proceed to question below',
    #                                 choices=Choices.submission_charges()
    #                                 )
    # submission_charges_url = URLField('Enter the URL where this information can be found',
    #     [validators.DataRequired(), URLOptionalScheme()],
    #     # description='This field is optional if you have selected "No" above'
    # )
    # submission_charges_amount = IntegerField('Amount',
    #     [OptionalIf('submission_charges', optvals=Choices.submission_charges_amount_optional())],
    # )
    # submission_charges_currency = DOAJSelectField('Currency',
    #     [OptionalIf('submission_charges', optvals=Choices.submission_charges_amount_optional())],
    #     choices = Choices.currency()
    # )
    # waiver_policy = RadioField('Does the journal have a waiver policy (for developing country authors etc)?',
    #                            [validators.DataRequired()],
    #                            choices=Choices.waiver_policy()
    #                            )
    waiver_policy_url = URLField('Enter the URL where this information can be found',
                                 [validators.Optional(),
                                  HTTPURL()]
                                 )
    # digital_archiving_policy = DOAJSelectMultipleField('What digital archiving policy does the journal use?',
    #                                                    [
    #                                                        validators.DataRequired(),
    #                                                        ExclusiveCheckbox(
    #                                                            Choices.digital_archiving_policy_val("none")),
    #                                                        ExtraFieldRequiredIf('digital_archiving_policy_library',
    #                                                                             reqval=Choices.digital_archiving_policy_val(
    #                                                                                 "library")),
    #                                                        ExtraFieldRequiredIf('digital_archiving_policy_other',
    #                                                                             reqval=Choices.digital_archiving_policy_val(
    #                                                                                 "other")),
    #                                                    ],
    #                                                    description="Select all that apply. Institutional archives and publishers' own online archives are not valid.",
    #                                                    choices=Choices.digital_archiving_policy(),
    #                                                    option_widget=widgets.CheckboxInput(),
    #                                                    widget=widgets.ListWidget(prefix_label=False)
    #                                                    )
    preservation_services = TagListField('Digital Archiving Policy (Other)',
                                       )
    preservation_library = StringField('Digital Archiving Policy (Library)',
                                       )
    preservation_url = URLField('Enter the URL where this information can be found',
                                [validators.Optional(),
                                 HTTPURL()],
                                description='This field is optional if you selected "No policy in place".',
                                )
    # crawl_permission = RadioField('Does the journal allow software/spiders to automatically crawl the journal content (also known as text mining)?',
    #     [validators.DataRequired()],
    #     choices = Choices.crawl_permission()
    # )
    # article_identifiers = DOAJSelectMultipleField('Which article identifiers does the journal use?',
    #                                               [validators.DataRequired(),
    #                                                ExtraFieldRequiredIf('article_identifiers_other',
    #                                                                     reqval=Choices.article_identifiers_val(
    #                                                                         "other")), ExclusiveCheckbox()],
    #                                               choices=Choices.article_identifiers(),
    #                                               option_widget=widgets.CheckboxInput(),
    #                                               widget=widgets.ListWidget(prefix_label=False),
    #                                               )
    # article_identifiers_other = StringField('Article Identifiers (Other)',
    #                                         )
    # download_statistics = RadioField('Does the journal provide article download statistics?',
    #     [validators.DataRequired()],
    #     description = 'If "No" proceed to question 32.',
    #     choices = Choices.download_statistics()
    # )
    # download_statistics_url = StringField('Enter the URL where this information can be found',
    #     [validators.Optional(), URLOptionalScheme()],
    # )
    # first_fulltext_oa_year = IntegerField('What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles? (Full Text may be provided as PDFs. Does not apply for new journals.)',
    #     [validators.DataRequired(), validators.NumberRange(min=1600, max=(datetime.now().year)) ],
    #     description = 'Use 4 digits for the year, i.e. YYYY format.'
    # )
    # fulltext_format = DOAJSelectMultipleField('Please indicate which formats of full text are available',
    #     [validators.DataRequired(), ExtraFieldRequiredIf('fulltext_format_other', reqval=Choices.fulltext_format_val("other"))],
    #     description = 'Tick all that apply.',
    #     choices = Choices.fulltext_format(),
    #     option_widget=widgets.CheckboxInput(),
    #     widget=widgets.ListWidget(prefix_label=False)
    # )
    # fulltext_format_other = StringField('Fulltext Format (Other)',
    # )
    keywords = TagListField('Add keyword(s) that best describe the journal (comma delimited)',
        [validators.DataRequired(), MaxLen(6, message='You can only enter up to {max_len} keywords.')],
        description='Maximum 6. Keywords must be in English. All keywords are stored in lowercase.'
    )
    languages = DOAJSelectMultipleField('Select the language(s) that the Full Text of the articles is published in',
                                        [validators.DataRequired()],
                                        choices=Choices.language(),
                                        description="You can select multiple languages."
                                        )
    editorial_board_url = URLField('What is the URL for the Editorial Board page?',
                                   [validators.DataRequired(), HTTPURL()],
                                   description='A journal must have an editor and an editorial board. Only in the case of Arts and Humanities journals we will accept a form of editorial review using only two editors and no editorial board. Where an editorial board is present, members must be clearly identifiable with their names and affiliation information.'
                                   )

    pid_scheme = StringField('Persistent Identifier Schema')

    review_process = DOAJSelectField('Please select the review process for papers',
                                     [validators.DataRequired()],
                                     choices=Choices.review_process(),
                                     default=Choices.review_process_default(),
                                     )
    review_process_url = URLField('Enter the URL where this information can be found',
                                  [validators.Optional(),
                                   HTTPURL()],
                                  description='This field is optional if you have selected "None" above.'
                                  )
    aims_scope_url = URLField("What is the URL for the journal's Aims & Scope",
                              [validators.DataRequired(), HTTPURL()]
                              )
    author_instructions_url = URLField("What is the URL for the journal's instructions for authors?",
                                       [validators.DataRequired(), HTTPURL()]
                                       )
    # plagiarism_screening = RadioField('Does the journal have a policy of screening for plagiarism?',
    #                                   [validators.DataRequired()],
    #                                   description='If "No" proceed to question 43.',
    #                                   choices=Choices.plagiarism_screening()
    #                                   )
    publication_time = IntegerField('What is the average number of weeks between submission and publication?',
                                    [validators.DataRequired(), validators.NumberRange(min=0, max=100)]
                                    )
    plagiarism_screening_url = URLField("Enter the URL where this information can be found",
                                        [validators.Optional(),
                                         HTTPURL()],
                                        description="The URL should state that the journal actively checks for plagiarism and detail how this is done."
                                        )
    oa_statement_url = URLField("What is the URL for the journal's Open Access statement?",
                                [validators.DataRequired(), HTTPURL()]
                                )
    license_display = DOAJSelectField('Does the journal embed or display licensing information in its articles?',
                                 [validators.DataRequired()],
                                 choices=Choices.licence_display(),
                                 description='For more information go to <a target="_blank" href="http://wiki.creativecommons.org/CC_REL">http://wiki.creativecommons.org/CC_REL</a><br><br>If "No" proceed to question 47.',
                                )
    license_display_example_url = URLField("Please provide a URL to an example page with embedded licensing information",
                                   [validators.Optional(),
                                    HTTPURL()]
                                   )
    # license = RadioField("Does the journal allow reuse and remixing of content in accordance with a Creative Commons license or <em>other</em> type of license with similar conditions (Select 'Other')?",
    #     [validators.DataRequired(), ExtraFieldRequiredIf('license_other', reqval=Choices.licence_val("other"))],
    #     choices = Choices._licence,
    #     description = 'For more information go to <a href="http://creativecommons.org/licenses/" target="_blank">http://creativecommons.org/licenses/</a>'
    # )
    license_type = StringField('License Typw',
                               )
    license_checkbox = DOAJSelectMultipleField(
        'Which of the following does the content require? (Tick all that apply.)',
        choices=Choices.licence_checkbox(),
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
        )
    license_url = URLField("Enter the URL on your site where your license terms are stated",
                           [validators.Optional(), HTTPURL()]
                           )
    boai = RadioField(
        "Does the journal allow readers to <em>read, download, copy, distribute, print, search, or link to the full texts of its articles</em> and allow readers to <em>use them for any other lawful purpose</em>?",
        [validators.DataRequired()],
        choices=Choices.binary(),
        description='From the <a href="http://www.budapestopenaccessinitiative.org/read" target="_blank">Budapest Open Access Initiative\'s definition of Open Access</a>.',
        )
    # deposit_policy = DOAJSelectMultipleField(
    #     'With which deposit policy directory does the journal have a registered deposit policy?',
    #     [validators.DataRequired(),
    #      ExtraFieldRequiredIf('deposit_policy_other', reqval=Choices.deposit_policy_other_val("other")),
    #      ExclusiveCheckbox()],
    #     description='Select all that apply.',
    #     choices=Choices.deposit_policy(),
    #     option_widget=widgets.CheckboxInput(),
    #     widget=widgets.ListWidget(prefix_label=False)
    #     )
    deposit_policy_service = StringField('Deposit Policy (Other)')
    deposit_policy_url = URLField('Enter the URL where this information can be found',
                                  [validators.Optional(), HTTPURL()]
                                  )
    deposit_policy_is_registered = RadioField('Is deposit policy registered?',
                               [validators.DataRequired()],
                               choices=Choices.binary()
                               )
    # copyright = RadioField('Does the journal allow the author(s) to hold the copyright without restrictions?',
    #                        [validators.DataRequired()],
    #                        choices=Choices.other_charges()
    #                        )
    copyright_url = URLField('Enter the URL where this information can be found',
                             [validators.Optional(), HTTPURL()]
                             )

    # other_charges = RadioField('Do any other charges apply?',
    #                        [validators.DataRequired()],
    #                        choices=Choices.other_charges()
    #                        )

    other_charges_url = URLField('Enter the URL where this information can be found',
                                 [validators.Optional(), HTTPURL()])

    article_orcid = RadioField('Is orcid provided for this article?',
                               [validators.DataRequired()],
                               choices=Choices.orcid()
                               )

    article_i4oc_open_citations = RadioField('Is i4oc provided for this article?',
                               [validators.DataRequired()],
                               choices=Choices.i40c_open_citations()
                               )

    # publishing_rights = RadioField(
    #     'Will the journal allow the author(s) to retain publishing rights without restrictions?',
    #     [validators.DataRequired()],
    #     choices=Choices.publishing_rights()
    #     )
    # publishing_rights_url = URLField('Enter the URL where this information can be found',
    #                                  [OptionalIf('publishing_rights', optvals=Choices.publishing_rights_url_optional()),
    #                                   URLOptionalScheme()]
    #                                  )


class JournalInfoOptionalPaymentURLs(JournalInformation):
    """Overrides fields in the JournalInfo form that are not required for ManEds """

    processing_charges_url = URLField('Enter the URL where this information can be found',
                                      [validators.Optional()],
                                      )

    submission_charges_url = URLField('Enter the URL where this information can be found',
                                      [validators.Optional()],
                                      )


class Suggestion(Form):
    """ Additional bibliographic metadata required when suggesting a journal to the DOAJ """

    # articles_last_year = IntegerField(
    #     'How many research and review articles did the journal publish in the last calendar year?',
    #     [validators.DataRequired(), validators.NumberRange(min=0)],
    #     description='A journal must publish at least 5 articles per year to stay in the DOAJ.',
    #     )
    # articles_last_year_url = URLField('Enter the URL where this information can be found',
    #                                   [validators.DataRequired(), URLOptionalScheme()]
    #                                   )
    # metadata_provision = RadioField('Does the journal provide, or intend to provide, article level metadata to DOAJ?',
    #                                 [validators.DataRequired()],
    #                                 description='If yes, metadata must be provided within 3 months of acceptance into DOAJ.',
    #                                 choices=Choices.metadata_provision()
    #                                 )


class PublicApplicant(Form):
    """ Suggester's contact details to be provided via the public application form """

    applicant_name = StringField('Your name',
                                 [validators.DataRequired()]
                                 )
    applicant_email = StringField('Your email address',
                                  [validators.DataRequired(), validators.Email(message='Invalid email address.')]
                                  )
    applicant_email_confirm = StringField('Confirm your email address',
                                          [validators.DataRequired(),
                                           validators.Email(message='Invalid email address.'),
                                           validators.EqualTo('applicant_email', EMAIL_CONFIRM_ERROR)]
                                          )


class AdminSuggester(Form):
    """ Suggester's contact details as presented to administrators/editors in the DOAJ workflow"""

    suggester_name = StringField("Name",
                                 [validators.DataRequired()]
                                 )
    suggester_email = StringField("Email address",
                                  [validators.DataRequired(), validators.Email(message='Invalid email address.')]
                                  )
    suggester_email_confirm = StringField("Confirm email address",
                                          [validators.DataRequired(),
                                           validators.Email(message='Invalid email address.'),
                                           validators.EqualTo('applicant_email', EMAIL_CONFIRM_ERROR)]
                                          )


class Note(Form):
    """ Note form for use in admin area - recommended to be included by the composing form as a FormField, so it can be
        represented as a multi-field.  Use Notes to achieve this """

    note = TextAreaField('Note')
    date = DisabledTextField('Date')


class Notes(Form):
    """ Multiple notes form for inclusion into admin forms """
    notes = FieldList(FormField(Note))


class ApplicationSubject(Form):
    """ Subject classification entry - with workflow validation"""

    subject = DOAJSelectMultipleField('Subjects', [
        OptionalIf('application_status', optvals=Choices.application_status_subject_optional())],
                                      choices=Choices.subjects())


class JournalSubject(Form):
    """ Subject classification entry - optional"""

    subject = DOAJSelectMultipleField('Subjects', [validators.Optional()], choices=Choices.subjects())


class JournalLegacy(Form):
    """ Legacy information required by some journals that are already in the DOAJ """

    author_pays = OptionalRadioField('Author pays to publish', [validators.Optional()], choices=Choices.author_pays())
    author_pays_url = StringField('Author pays - guide link', [validators.Optional(), validators.URL()])
    oa_end_year = IntegerField('Year in which the journal stopped publishing OA content',
                               [validators.Optional(), validators.NumberRange(max=datetime.now().year)])


class RequiredOwner(Form):
    """ An Owner field which is required - validation will fail if it is not provided.  For use in some admin forms """

    owner = StringField('Owner', [validators.DataRequired(), ReservedUsernames()])


class ApplicationOwner(Form):
    """ An Owner field which is optional under certain conditions.  For use in some admin forms """

    owner = StringField('Owner',
                        [ReservedUsernames(),
                         OptionalIf('application_status', optvals=Choices.application_status_optional())],
                        description='DOAJ account to which the application belongs.'
                                    '<br><br>'
                                    'This field is optional unless the application status is set to Accepted.'
                                    '<br><br>'
                                    'Entering a non-existent account and setting the application status to Accepted will automatically create the account using the Contact information in Questions 9 & 10, and send an email containing the Contact\'s username + password.'
                        )


class OptionalValidation(Form):
    """ Make the form provide an option to bypass validation """

    make_all_fields_optional = BooleanField('Allow incomplete form',
                                            description='<strong>Only tick this box if:</strong>'
                                                        '<br>a/ you are editing an old, incomplete record;'
                                                        '<br>b/ you really, really need to change a value without filling in the whole record;'
                                                        '<br>c/ <strong>you understand that the system will put in default values like "No" and "None" into old records which are missing some information</strong>.'
                                            )


class Editorial(Form):
    """ Editorial group fields """

    editor_group = StringField("Editor Group", [validators.Optional()])
    editor = PermissiveSelectField("Assigned to", default="")  # choices to be assigned at form render time


class Workflow(Form):
    """ Administrator workflow field """

    application_status = DOAJSelectField('Application Status',  # choices are late-binding as they depend on the user
                                         [validators.DataRequired()],
                                         description='Setting the status to In Progress will tell others'
                                                     ' that you have started your review. Setting the status'
                                                     ' to Ready will alert the Managing Editors that you have'
                                                     ' completed your review.'
                                         )


class Seal(Form):
    """ Field to set the DOAJ Seal """

    doaj_seal = BooleanField('Qualifies for Seal', [validators.Optional()],
                             false_values=(BooleanField.false_values + (False,)))


class Continuations(Form):
    """ Fields to manage continuation of journals, and discontinuations """

    replaces = TagListField('This journal continues (add ISSN(s))',
                            [validators.Optional(), RegexpOnTagList(regex=ISSN_REGEX, message=ISSN_ERROR)],
                            description="Enter the ISSN(s) of the Journal which this Journal immediately replaces (i.e. don't include even older Journals here)"
                            )

    is_replaced_by = TagListField('This journal is continued by (add ISSN(s))',
                                  [validators.Optional(), RegexpOnTagList(regex=ISSN_REGEX, message=ISSN_ERROR)],
                                  description="Enter the ISSN(s) of the Journal which this Journal is immediately replaced by (i.e. don't include even newer Journals here)"
                                  )

    # note that although this is a date field, we use a string field with a regex as the conversion to/from form
    # data gets confusing, as DateField produces datetime.date objects, but apparently won't read them.
    # Simpler just to do it this way.
    discontinued_date = StringField("Discontinued Date", [validators.Optional(),
                                                          validators.Regexp(regex=BIG_END_DATE_REGEX,
                                                                            message=DATE_ERROR)],
                                    description="Date this Journal was discontinued or ceased publication, YYYY-MM-DD.  If the day of the month is not know, please use '01'")


#####################################################################
# The context sensitive forms themselves
#####################################################################


class PublicApplicationForm(JournalInformation, PublicApplicant):
    """
    The Public Application Form.  It consists of:
        * JournalInformation - journal bibliographic data
        * Suggestion - additional application metadata
        * PublicSuggested - suggester's contact details, from the suggester's perspective
    """
    pass


class ManEdApplicationReviewForm(Editorial, Workflow, ApplicationOwner, JournalInfoOptionalPaymentURLs, Suggestion,
                                 ApplicationSubject, AdminSuggester, Notes, Seal, Continuations):
    """
    Managing Editor's Application Review form.  It consists of:
        * Editorial - ability to add editorial groups (but ability to add editors individually will be disabled)
        * Workflow - ability to change application status
        * ApplicationOwner - able to set the owner, and for the owner assignment to be optional except under certain circumstances
        * JournalInfoOptionalPaymentURLs - journal bibliographic data, with custom validation for managing editors
        * Suggestion - additional application metadata
        * Subject - ability to use subject hierarchy browser
        * AdminSuggester - suggester's contact details, from an administrator's perspective
        * Notes - repeatable notes field
        * Seal - checkbox for DOAJ seal
    """
    pass


class EditorApplicationReviewForm(Editorial, Workflow, JournalInfoOptionalPaymentURLs, Suggestion, ApplicationSubject,
                                  AdminSuggester, Notes):
    """
    Editor's Application Review form.  It consists of:
        * Editorial - ability to add associate editors (but not change editorial group)
        * Workflow - ability to change application status
        * JournalInformation - journal bibliographic data
        * Suggestion - additional application metadata
        * Subject - ability to use subject hierarchy browser
        * AdminSuggester - suggester's contact details, from an administrator's perspective
        * Notes - repeatable notes field
    """
    pass


class AssEdApplicationReviewForm(Workflow, JournalInfoOptionalPaymentURLs, Suggestion, ApplicationSubject,
                                 AdminSuggester, Notes):
    """
    Editor's Application Review form.  It consists of:
        * Workflow - ability to change application status
        * JournalInformation - journal bibliographic data
        * Suggestion - additional application metadata
        * Subject - ability to use subject hierarchy browser
        * AdminSuggester - suggester's contact details, from an administrator's perspective
        * Notes - repeatable notes field
    """
    pass


class PublisherUpdateRequestForm(JournalInformation, Suggestion):
    """
    Publisher's update request form.  It consists of:
        * JournalInformation - journal bibliographic data
        * Suggestion - additional application metadata
    """
    pass


class PublisherUpdateRequestReadOnlyForm(JournalInformation, Suggestion):
    """
    Read-only application form.  It consists of:
        * JournalInformation - journal bibliographic data
        * Suggestion - additional application metadata
    """
    pass


class ManEdJournalReviewForm(Editorial, RequiredOwner, JournalSubject, JournalLegacy, JournalInformation, Notes,
                             OptionalValidation, Seal, Continuations):
    """
    Managing Editor's Journal Review form.  It consists of:
        * Editorial - ability to add editorial groups (but ability to add editors individually will be disabled)
        * JournalLegacy - ability to edit info present in deprecated fields. Will only be shown by the renderer for records that have data in those fields already.
        * JournalInformation - journal bibliographic data
        * Subject - ability to use subject hierarchy browser
        * Notes - repeatable notes field
        * RequiredOwner - adds an Owner field which is required - validation will fail if it is not provided
        * OptionalValidation - Make the form provide an option to bypass validation
        * Seal - checkbox for DOAJ seal
        * Continuations - allows specification of replaces/is_replaced_by and discontinued date
    """
    pass


class EditorJournalReviewForm(Editorial, JournalSubject, JournalLegacy, JournalInformation, Notes):
    """
    Editor's Journal Review form.  It consists of:
        * Editorial - ability to add editorial groups (but ability to add editors individually will be disabled)
        * JournalLegacy - ability to edit info present in deprecated fields. Will only be shown by the renderer for records that have data in those fields already.
        * JournalInformation - journal bibliographic data
        * Subject - ability to use subject hierarchy browser
        * Notes - repeatable notes field
    """
    pass


class AssEdJournalReviewForm(JournalInformation, JournalSubject, JournalLegacy, Notes):
    """
    Associate Editor's Journal Review form.  It consists of:
        * JournalInformation - journal bibliographic data
        * Subject - ability to use subject hierarchy browser
        * JournalLegacy - ability to edit info present in deprecated fields. Will only be shown by the renderer for records that have data in those fields already.
        * Notes - repeatable notes field
    """
    pass


class ReadOnlyJournalForm(JournalInformation, JournalSubject, JournalLegacy, Notes):
    """
    Read-only journal form.  It consists of:
        * JournalInformation - journal bibliographic data
        * Subject - ability to use subject hierarchy browser
        * JournalLegacy - ability to edit info present in deprecated fields. Will only be shown by the renderer for records that have data in those fields already.
        * Notes - repeatable notes field
    """
    pass


class ManEdBulkEditJournalForm(Form):
    publisher = StringField('Publisher',
                            [validators.Optional()]
                            )
    doaj_seal = DOAJSelectField('Qualifies for Seal',
                                [validators.Optional()],
                                description='How should we change the DOAJ Seal on these journals?',
                                choices=[("", "Leave unchanged"), ("True", "Yes"), ("False", "No")],
                                )
    country = DOAJSelectField('Country',
                              [validators.Optional()],
                              description='Select the country where the publisher carries out its business activities.',
                              choices=Choices.country(),
                              )
    owner = StringField('Owner',
                        [ReservedUsernames(), validators.Optional()],
                        description='DOAJ account to which the application belongs.'
                        )
    platform = StringField('Platform, Host or Aggregator',
                           [validators.Optional()],
                           description='The name of the platform, host or aggregator of the journal content, e.g. OJS, HighWire Press, EBSCO etc.'
                           )
    contact_name = StringField('Contact Name',
                               [validators.Optional()]
                               )
    contact_email = StringField('Contact\'s email address',
                                [validators.Optional(), validators.Email(message='Invalid email address.')]
                                )


DOI_REGEX = regex.DOI_COMPILED
DOI_ERROR = 'Invalid DOI. A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'
ORCID_REGEX = regex.ORCID_COMPILED
ORCID_ERROR = "Invalid ORCID iD. Please enter your ORCID iD as a full URL of the form https://orcid.org/0000-0000-0000-0000"
start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)
YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year - 1, -1)]
MONTH_CHOICES = [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04"), ("5", "05"), ("6", "06"), ("7", "07"), ("8", "08"), ("9", "09"), ("10", "10"), ("11", "11"), ("12", "12")]
INITIAL_AUTHOR_FIELDS = 3


class AuthorForm(Form):
    name = StringField("Name", [validators.Optional()])
    affiliation = StringField("Affiliation", [validators.Optional()])
    orcid_id = StringField("ORCID iD", [validators.Optional(), validators.Regexp(regex=ORCID_REGEX, message=ORCID_ERROR)])


class ArticleForm(Form):
    title = StringField("Article title <em>(required)</em>", [validators.DataRequired()])
    doi = StringField("DOI", [OptionalIf("fulltext"), validators.Regexp(regex=DOI_REGEX, message=DOI_ERROR)], description="(You must provide either a Full-Text URL or a DOI or both)")
    authors = FieldList(FormField(AuthorForm), min_entries=1) # We have to do the validation for this at a higher level
    abstract = TextAreaField("Abstract", [validators.Optional()])
    keywords = TagListField("Keywords", [validators.Optional()], description="Use a , to separate keywords") # enhanced with select2
    fulltext = StringField("Full-text URL", [OptionalIf("doi"), validators.URL()])
    publication_year = DOAJSelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = DOAJSelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = DOAJSelectField("Print", [ThisOrThat("eissn")], choices=[]) # choices set at construction
    eissn = DOAJSelectField("Online", [ThisOrThat("pissn")], choices=[]) # choices set at construction

    volume = IntegerField("Volume", [validators.Optional()])
    number = IntegerField("Issue", [validators.Optional()])
    start = IntegerField("Start", [validators.Optional()])
    end = IntegerField("End", [validators.Optional()])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        try:
            self.pissn.choices = Choices.choices_for_article_issns(current_user)
            self.eissn.choices = Choices.choices_for_article_issns(current_user)
        except:
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass
