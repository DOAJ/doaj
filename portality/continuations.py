from wtforms import Form, validators
from wtforms import StringField, HiddenField
from portality.formcontext.validate import URLOptionalScheme, OptionalIf, ExclusiveCheckbox, ExtraFieldRequiredIf, MaxLen, RegexpOnTagList
import re

ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'

class MakeContinuation(Form):

    title = StringField('New Journal Title', [validators.DataRequired()])

    pissn = StringField('New Journal ISSN (print version)',
        [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Only provide the print ISSN if your journal has one, otherwise leave this field blank. Write the ISSN with the hyphen "-" e.g. 1234-4321.',
    )
    eissn = StringField('New Journal ISSN (online version)',
        [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Cannot be the same as the P-ISSN. Write the EISSN with the hyphen "-" e.g. 1234-4321.',
    )

    type = HiddenField()