from datetime import datetime

from flask_login import current_user
from wtforms import Form, validators
from wtforms import StringField, TextAreaField, FormField, FieldList

from portality import regex
from portality.core import app

from portality.formcontext.fields import DOAJSelectField, TagListField
from portality.forms.validate import OptionalIf, ThisOrThat, NoScriptTag

from portality.formcontext.choices import Choices


ISSN_REGEX = regex.ISSN_COMPILED
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'

EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'

BIG_END_DATE_REGEX = regex.BIG_END_DATE_COMPILED
DATE_ERROR = "Date must be supplied in the form YYYY-MM-DD"

DOI_REGEX = regex.DOI_COMPILED
DOI_ERROR = 'Invalid DOI. A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'

ORCID_REGEX = regex.ORCID_COMPILED
ORCID_ERROR = "Invalid ORCID iD. Please enter your ORCID iD as a full URL of the form https://orcid.org/0000-0000-0000-0000"

start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)
YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year - 1, -1)]
MONTH_CHOICES = [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04"), ("5", "05"), ("6", "06"), ("7", "07"), ("8", "08"), ("9", "09"), ("10", "10"), ("11", "11"), ("12", "12")]
INITIAL_AUTHOR_FIELDS = 3


class AuthorForm(Form):
    name = StringField("Name", [validators.Optional(),NoScriptTag()])
    affiliation = StringField("Affiliation", [validators.Optional(), NoScriptTag()])
    orcid_id = StringField("ORCID iD", [validators.Optional(), validators.Regexp(regex=ORCID_REGEX, message=ORCID_ERROR)])


class ArticleForm(Form):
    title = StringField("Article title <em>(required)</em>", [validators.DataRequired(), NoScriptTag()])
    doi = StringField("DOI", [OptionalIf("fulltext", "You must provide the DOI or the Full-Text URL"), validators.Regexp(regex=DOI_REGEX, message=DOI_ERROR)], description="(You must provide a DOI and/or a Full-Text URL)")
    authors = FieldList(FormField(AuthorForm), min_entries=1) # We have to do the validation for this at a higher level
    abstract = TextAreaField("Abstract", [validators.Optional(), NoScriptTag()])
    keywords = TagListField("Keywords", [validators.Optional(), NoScriptTag()], description="Use a , to separate keywords") # enhanced with select2
    fulltext = StringField("Full-text URL", [OptionalIf("doi", "You must provide the Full-Text URL or the DOI"), validators.URL()])
    publication_year = DOAJSelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = DOAJSelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = DOAJSelectField("Print", [ThisOrThat("eissn", "Either this field or Online ISSN is required")], choices=[]) # choices set at construction
    eissn = DOAJSelectField("Online", [ThisOrThat("pissn", "Either this field or Print ISSN is required")], choices=[]) # choices set at construction

    volume = StringField("Volume", [validators.Optional(), NoScriptTag()])
    number = StringField("Issue", [validators.Optional(), NoScriptTag()])
    start = StringField("Start", [validators.Optional(), NoScriptTag()])
    end = StringField("End", [validators.Optional(), NoScriptTag()])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        try:
            self.pissn.choices = Choices.choices_for_article_issns(current_user)
            self.eissn.choices = Choices.choices_for_article_issns(current_user)
        except:
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass
