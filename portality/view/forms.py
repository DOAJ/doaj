'''
All the various simple forms that we need in the system

FIXME: probably we need to think more about how we organise forms - maybe a module with different files for different
features, and a bit of refactoring on the organisation of the formcontext stuff to be consistent
'''
import re

from wtforms import Form, validators
from wtforms import StringField, TextAreaField, HiddenField

from portality import models
from portality.forms.validate import OptionalIf, MaxLen


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

    recaptcha_value = HiddenField()

    email = StringField('Your Email', [validators.DataRequired(), validators.Email()])

    subject = StringField("Subject", [validators.Optional()])

    message = TextAreaField("Message", [validators.DataRequired(), MaxLen(1000)], description="1000 characters max - <span id='wordcount'></span>")
