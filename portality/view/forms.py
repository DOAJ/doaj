'''
All the various simple forms that we need in the system

FIXME: probably we need to think more about how we organise forms - maybe a module with different files for different
features, and a bit of refactoring on the organisation of the formcontext stuff to be consistent
'''
from datetime import datetime
import re

from flask_login import current_user

from wtforms import Form, validators
from wtforms import StringField, TextAreaField, FormField, FieldList, HiddenField

from portality.core import app
from portality import models
from portality.formcontext.validate import ThisOrThat, OptionalIf, MaxLen
from portality.formcontext.fields import DOAJSelectField
from portality import regex
from portality.crosswalks import article_form

##########################################################################
## Forms and related features for Article metadata
##########################################################################

DOI_REGEX = regex.DOI_COMPILED
DOI_ERROR = 'Invalid DOI.  A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'

# use the year choices in app.cfg or default to 15 years previous.
start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)

YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year - 1, -1)]
MONTH_CHOICES = [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04"), ("5", "05"), ("6", "06"), ("7", "07"), ("8", "08"), ("9", "09"), ("10", "10"), ("11", "11"), ("12", "12")]

class AuthorForm(Form):
    name = StringField("Name", [validators.Optional()])
    affiliation = StringField("Affiliation", [validators.Optional()])


class ArticleForm(Form):
    title = StringField("Article Title", [validators.DataRequired()])
    doi = StringField("DOI", [OptionalIf("fulltext"), validators.Regexp(regex=DOI_REGEX, message=DOI_ERROR)], description="(You must provide a DOI and/or a Full-Text URL)")
    authors = FieldList(FormField(AuthorForm), min_entries=3) # We have to do the validation for this at a higher level
    abstract = TextAreaField("Abstract", [validators.Optional()])
    keywords = StringField("Keywords", [validators.Optional()], description="Use a , to separate keywords") # enhanced with select2
    fulltext = StringField("Full-Text URL", [OptionalIf("doi"), validators.URL()], description="(The URL for each article must be unique.  You must provide a Full-Text URL and/or a DOI)")
    publication_year = DOAJSelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = DOAJSelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = DOAJSelectField("Journal ISSN (print version)", [ThisOrThat("eissn")], choices=[]) # choices set at construction
    eissn = DOAJSelectField("Journal ISSN (online version)", [ThisOrThat("pissn")], choices=[]) # choices set at construction
 
    volume = StringField("Volume Number", [validators.Optional()])
    number = StringField("Issue Number", [validators.Optional()])
    start = StringField("Start Page", [validators.Optional()])
    end = StringField("End Page", [validators.Optional()])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        if "id" in kwargs:
            a = models.Article.pull(kwargs["id"])
            bibjson = a.bibjson()
            article_form.ArticleFormXWalk.obj2form(self, bibjson)

        try:
            if not current_user.is_anonymous:
                if "admin" in current_user.role:
                    journal = models.Journal.find_by_issn(bibjson.first_eissn)[0]
                    issns = models.Journal.issns_by_owner(journal.owner)
                else:
                    issns = models.Journal.issns_by_owner(current_user.id)
                ic = [("", "Select an ISSN")] + [(i,i) for i in issns]
                self.pissn.choices = ic
                self.eissn.choices = ic
        except:
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass


##########################################################################
## Editor Group Forms
##########################################################################

class UniqueGroupName(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, form, field):
        exists_id = models.EditorGroup.group_exists_by_name(field.data)
        if exists_id is None:
            # if there is no group of the same name, we are fine
            return

        # if there is a group of the same name, we need to check whether it's the
        # same group as we are currently editing
        id_field = form._fields.get("group_id")
        if id_field is None or id_field.data == "" or id_field.data is None:
            # if there is no id field then this is a new group, and so the name clashes
            # with an existing group
            raise validators.ValidationError("The group's name must be unique among the Editor Groups")

        # if we get to here, the id_field exists, so we need to check whether it matches
        # the group with the same id
        if id_field.data != exists_id:
            raise validators.ValidationError("The group's name must be unique among the Editor Groups")


class NotRole(object):
    def __init__(self, role, *args, **kwargs):
        self.role = role

    def __call__(self, form, field):
        accounts = [a.strip() for a in field.data.split(",") if a.strip() != ""]
        if len(accounts) == 0:
            return
        fails = []
        for a in accounts:
            acc = models.Account.pull(a)
            if acc is None:                                              # If the account has been deleted we can't pull
                continue
            elif acc.has_role(self.role) and not acc.is_super:
                fails.append(acc.id)
        if len(fails) == 0:
            return
        have_or_has = "have" if len(fails) > 1 else "has"
        msg = ", ".join(fails) + " " + have_or_has + " role " + self.role + " so cannot be assigned to an Editor Group"
        raise validators.ValidationError(msg)


class EditorGroupForm(Form):
    group_id = HiddenField("Group ID", [validators.Optional()])
    name = StringField("Group Name", [validators.DataRequired(), UniqueGroupName()])
    editor = StringField("Editor", [validators.DataRequired(), NotRole("publisher")])
    associates = StringField("Associate Editors", [validators.Optional(), NotRole("publisher")])

##########################################################################
## Continuations Forms
##########################################################################

ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X){1}$', re.IGNORECASE)
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'


class MakeContinuation(Form):

    title = StringField('Journal Title', [validators.DataRequired()])

    pissn = StringField('Journal ISSN (print version)',
        [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Only provide the print ISSN if your journal has one, otherwise leave this field blank. Write the ISSN with the hyphen "-" e.g. 1234-4321.',
    )
    eissn = StringField('Journal ISSN (online version)',
        [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Cannot be the same as the P-ISSN. Write the EISSN with the hyphen "-" e.g. 1234-4321.',
    )

    type = HiddenField()

##########################################################################
## Contact Forms
##########################################################################


class ContactUs(Form):

    email = StringField('Your Email', [validators.DataRequired(), validators.Email()])

    subject = StringField("Subject", [validators.Optional()])

    message = TextAreaField("Message", [validators.DataRequired(), MaxLen(1000)], description="1000 characters max - <span id='wordcount'></span>")
