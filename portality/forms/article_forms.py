from copy import deepcopy
from datetime import datetime

from flask import render_template, url_for, request
from flask_login import current_user
from wtforms import Form, validators
from wtforms import StringField, TextAreaField, FormField, FieldList
from wtforms.fields.core import UnboundField

from portality import regex, models
from portality.bll import DOAJ
from portality.core import app
from portality.crosswalks.article_form import ArticleFormXWalk
from portality.forms.fields import DOAJSelectField, TagListField
from portality.forms.validate import OptionalIf, ThisOrThat, NoScriptTag, DifferentTo
from portality.ui.messages import Messages


#########################################
# Form infrastructure


class FormContext(object):
    """
    ~~FormContext:FormContext->Formulaic:Library~~
    """
    def __init__(self, form_data=None, source=None, formulaic_context=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None
        self._renderer = None
        self._template = None
        self._alert = []
        self._info = ''
        self._formulaic = formulaic_context

        # initialise the renderer (falling back to a default if necessary)
        self.make_renderer()
        if self.renderer is None:
            self.renderer = Renderer()

        # specify the jinja template that will wrap the renderer
        self.set_template()

        # now create our form instance, with the form_data (if there is any)
        if form_data is not None:
            self.data2form()

        # if there isn't any form data, then we should create the form properties from source instead
        elif source is not None:
            self.source2form()

        # if there is no source, then a blank form object
        else:
            self.blank_form()

    ############################################################
    # getters and setters on the main FormContext properties
    ############################################################

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, val):
        self._form = val

    @property
    def source(self):
        return self._source

    @property
    def form_data(self):
        return self._form_data

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, val):
        self._target = val

    @property
    def renderer(self):
        return self._renderer

    @renderer.setter
    def renderer(self, val):
        self._renderer = val

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, val):
        self._template = val

    @property
    def alert(self):
        return self._alert

    def add_alert(self, val):
        self._alert.append(val)

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, val):
        self._info = val

    ############################################################
    # Lifecycle functions that subclasses should implement
    ############################################################

    def make_renderer(self):
        """
        This will be called during init, and must populate the self.render property
        """
        pass

    def set_template(self):
        """
        This will be called during init, and must populate the self.template property with the path to the jinja template
        """
        pass

    def pre_validate(self):
        """
        This will be run before validation against the form is run.
        Use it to patch the form with any relevant data, such as fields which were disabled
        """
        pass

    def blank_form(self):
        """
        This will be called during init, and must populate the self.form_data property with an instance of the form in this
        context, based on no originating source or form data
        """
        pass

    def data2form(self):
        """
        This will be called during init, and must convert the form_data into an instance of the form in this context,
        and write to self.form
        """
        pass

    def source2form(self):
        """
        This will be called during init, and must convert the source object into an instance of the form in this
        context, and write to self.form
        """
        pass

    def form2target(self):
        """
        Convert the form object into a the target system object, and write to self.target
        """
        pass

    def patch_target(self):
        """
        Patch the target with data from the source.  This will be run by the finalise method (unless you override it)
        """
        pass

    def finalise(self, *args, **kwargs):
        """
        Finish up with the FormContext.  Carry out any final workflow tasks, etc.
        """
        self.form2target()
        self.patch_target()

    ############################################################
    # Functions which can be called directly, but may be overridden if desired
    ############################################################

    def validate(self):
        self.pre_validate()
        f = self.form
        valid = False
        if f is not None:
            valid = f.validate()

        # if this isn't a valid form, record the fields that have errors
        # with the renderer for use later
        if not valid:
            error_fields = []
            for field in self.form:
                if field.errors:
                    error_fields.append(field.short_name)

        return valid

    @property
    def errors(self):
        f = self.form
        if f is not None:
            return f.errors
        return False

    def render_template(self, **kwargs):
        return render_template(self.template, form_context=self, **kwargs)

    def fieldset(self, fieldset_name=None):
        return self._formulaic.fieldset(fieldset_name)

    def fieldsets(self):
        return self._formulaic.fieldsets()

    def check_field_group_exists(self, field_group_name):
        return self.renderer.check_field_group_exists(field_group_name)

    @property
    def ui_settings(self):
        return self._formulaic.ui_settings


class Renderer(object):
    """
    ~~FormContextRenderer:FormContext->FormHelper:FormContext~~
    """
    def __init__(self):
        self.FIELD_GROUPS = {}
        self.fh = FormHelperBS3()
        self._error_fields = []
        self._disabled_fields = []
        self._disable_all_fields = False
        self._highlight_completable_fields = False

    def check_field_group_exists(self, field_group_name):
        """ Return true if the field group exists in this form """
        group_def = self.FIELD_GROUPS.get(field_group_name)
        if group_def is None:
            return False
        else:
            return True

    def render_field_group(self, form_context, field_group_name=None, group_cfg=None):
        if field_group_name is None:
            return self._render_all(form_context)

        # get the group definition
        group_def = self.FIELD_GROUPS.get(field_group_name)
        if group_def is None:
            return ""

        # build the frag
        frag = ""
        for entry in group_def:
            field_name = list(entry.keys())[0]
            config = entry.get(field_name)
            config = deepcopy(config)

            config = self._rewrite_extra_fields(form_context, config)
            field = form_context.form[field_name]

            if field_name in self.disabled_fields or self._disable_all_fields is True:
                config["disabled"] = "disabled"

            if self._highlight_completable_fields is True:
                valid = field.validate(form_context.form)
                config["complete_me"] = not valid

            if group_cfg is not None:
                config.update(group_cfg)

            frag += self.fh.render_field(field, **config)

        return frag

    @property
    def error_fields(self):
        return self._error_fields

    def set_error_fields(self, fields):
        self._error_fields = fields

    @property
    def disabled_fields(self):
        return self._disabled_fields

    def set_disabled_fields(self, fields):
        self._disabled_fields = fields

    def disable_all_fields(self, disable):
        self._disable_all_fields = disable

    def _rewrite_extra_fields(self, form_context, config):
        if "extra_input_fields" in config:
            config = deepcopy(config)
            for opt, field_ref in config.get("extra_input_fields").items():
                extra_field = form_context.form[field_ref]
                config["extra_input_fields"][opt] = extra_field
        return config

    def _render_all(self, form_context):
        frag = ""
        for field in form_context.form:
            frag += self.fh.render_field(form_context, field.short_name)
        return frag

    def find_field(self, field, field_group):
        for index, item in enumerate(self.FIELD_GROUPS[field_group]):
            if field in item:
                return index

    def insert_field_after(self, field_to_insert, after_this_field, field_group):
        self.FIELD_GROUPS[field_group].insert(
            self.find_field(after_this_field, field_group) + 1,
            field_to_insert
        )


class FormHelperBS3(object):
    """
    ~~FormHelper:FormContext->Bootstrap3:Technology~~
    ~~->WTForms:Library~~
    """
    def render_field(self, field, **kwargs):
        # begin the frag
        frag = ""

        # deal with the first error if it is relevant
        first_error = kwargs.pop("first_error", False)
        if first_error:
            frag += '<a name="first_problem"></a>'

        # call the correct render function on the field type
        if field.type == "FormField":
            frag += self._form_field(field, **kwargs)
        elif field.type == "FieldList":
            frag += self._field_list(field, **kwargs)
        else:
            frag += self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)

        return frag

    def _wrap_control_group(self, field, contents, **kwargs):
        hidden = kwargs.pop("hidden", False)
        container_class = kwargs.pop("container_class", None)
        disabled = kwargs.pop("disabled", False)
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)
        complete_me = kwargs.get("complete_me", False)

        frag = '<div class="form-group'
        if field.errors:
            frag += " error"
        if render_subfields_horizontal:
            frag += " row"
        if container_class is not None:
            frag += " " + container_class
        if complete_me:
            frag += " complete-me"
        frag += '" id="'
        frag += field.short_name + '-container"'
        if hidden:
            frag += ' style="display:none;"'
        frag += ">"
        if contents is not None:
            frag += contents
        frag += "</div>"

        return frag

    def _form_field(self, field, **kwargs):
        # get the useful kwargs
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)

        frag = ""
        # for each subfield, do the render
        for subfield in field:
            if render_subfields_horizontal and not (subfield.type == 'CSRFTokenField' and not subfield.value):
                subfield_width = "3"
                remove = []
                for kwarg, val in kwargs.items():
                    if kwarg == 'subfield_display-' + subfield.short_name:
                        subfield_width = val
                        remove.append(kwarg)
                for rm in remove:
                    del kwargs[rm]
                frag += '<div class="col-md-' + subfield_width + ' nested-field-container">'
                frag += self._render_field(subfield, maximise_width=True, **kwargs)
                frag += "</div>"
            else:
                frag += self._render_field(subfield, **kwargs)

        return self._wrap_control_group(field, frag, **kwargs)

    def _field_list(self, field, **kwargs):
        # for each subfield, do the render
        frag = ""
        for subfield in field:
            if subfield.type == "FormField":
                frag += self.render_field(subfield, **kwargs)
            else:
                frag = self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)
        return frag

    def _render_field(self, field, **kwargs):
        # interesting arguments from keywords
        extra_input_fields = kwargs.get("extra_input_fields")
        q_num = kwargs.pop("q_num", None)
        maximise_width = kwargs.pop("maximise_width", False)
        clazz = kwargs.get("class", "")
        label_width = kwargs.get("label_width", 3)
        field_width = 12 - label_width
        field_width = str(kwargs.get("field_width", field_width))
        if label_width > 0:
            label_width = str(label_width)

        if field.type == 'CSRFTokenField' and not field.value:
            return ""

        frag = ""

        # If this is the kind of field that requires a label, give it one
        if field.type not in ['SubmitField', 'HiddenField', 'CSRFTokenField']:
            if q_num is not None:
                frag += '<a class="animated" name="' + q_num + '"></a>'
            if label_width != 0:
                frag += '<label class="control-label col-md-' + label_width + '" for="' + field.short_name + '">'
                if q_num is not None:
                    frag += '<a class="animated orange" href="#' + field.short_name + '-container" title="Link to this question" tabindex="-1">' + q_num + ')</a>&nbsp;'
                frag += field.label.text
                if field.flags.required or field.flags.display_required_star:
                    frag += '&nbsp;<span class="red">*</span>'
                frag += "</label>"

        # determine if this is a checkbox
        is_checkbox = False
        if (field.type == "SelectMultipleField"
                and field.option_widget.__class__.__name__ == 'CheckboxInput'
                and field.widget.__class__.__name__ == 'ListWidget'):
            is_checkbox = True

        extra_class = ""
        if is_checkbox:
            extra_class += " checkboxes"

        frag += '<div class="col-md-' + field_width + ' ' + extra_class + '">'
        if field.type == "RadioField":
            for subfield in field:
                frag += self._render_radio(subfield, **kwargs)
        elif is_checkbox:
            frag += '<ul id="' + field.short_name + '">'
            for subfield in field:
                frag += self._render_checkbox(subfield, **kwargs)
            frag += "</ul>"
        else:
            if maximise_width:
                clazz += " col-xs-12"
                kwargs["class"] = clazz
            render_args = {}
            # filter anything that shouldn't go in as a field attribute
            for k, v in kwargs.items():
                if k in ["class", "style", "disabled"] or k.startswith("data-"):
                    render_args[k] = v
            frag += field(**render_args) # FIXME: this is probably going to do some weird stuff

        if field.errors:
            frag += '<div class="alert alert--danger"><ul>'
            for error in field.errors:
                frag += '<li>' + error + '</li>'
            frag += "</ul></div>"

        if field.description:
            frag += '<p class="help-block">' + field.description + '</p>'

        frag += "</div>"
        return frag

    def _render_radio(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})
        label_width = "12"

        frag = '<label class="radio control-label col-md-' + label_width + '" for="' + field.short_name + '">'
        frag += field(**kwargs)
        frag += '<span class="label-text">' + field.label.text + '</span>'

        if field.label.text in list(extra_input_fields.keys()):
            frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</label>"
        return frag

    def _render_checkbox(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})

        frag = "<li>"
        frag += field(**kwargs)
        frag += '<label class="control-label" for="' + field.short_name + '">' + field.label.text + '</label>'

        if field.label.text in list(extra_input_fields.keys()):
            eif = extra_input_fields[field.label.text]
            if not isinstance(eif, UnboundField):
                frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</li>"
        return frag


#########################################
# Form definition
# ~~Article:Form~~

ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'
EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'
DATE_ERROR = "Date must be supplied in the form YYYY-MM-DD"
DOI_ERROR = 'Invalid DOI. A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'
ORCID_ERROR = "Invalid ORCID iD. Please enter your ORCID iD as a full URL of the form https://orcid.org/0000-0000-0000-0000"
IDENTICAL_ISSNS_ERROR = "The Print and Online ISSNs supplied are identical. If you supply 2 ISSNs they must be different."

start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)
YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year - 1, -1)]
MONTH_CHOICES = [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04"), ("5", "05"), ("6", "06"), ("7", "07"), ("8", "08"), ("9", "09"), ("10", "10"), ("11", "11"), ("12", "12")]
INITIAL_AUTHOR_FIELDS = 3


def choices_for_article_issns(user, article_id=None):
    if "admin" in user.role and article_id is not None:
        # ~~->Article:Model~~
        a = models.Article.pull(article_id)
        # ~~->Journal:Model~~
        issns = models.Journal.issns_by_owner(a.get_owner())
    else:
        issns = models.Journal.issns_by_owner(user.id)
    ic = [("", "Select an ISSN")] + [(i, i) for i in issns]
    return ic


class AuthorForm(Form):
    """
    ~~->$ Author:Form~~
    """
    name = StringField("Name", [validators.Optional(),NoScriptTag()])
    affiliation = StringField("Affiliation", [validators.Optional(), NoScriptTag()])
    orcid_id = StringField("ORCID iD", [validators.Optional(), validators.Regexp(regex=regex.ORCID_COMPILED, message=ORCID_ERROR)])


class ArticleForm(Form):
    title = StringField("Article title <em>(required)</em>", [validators.DataRequired(), NoScriptTag()])
    doi = StringField("DOI", [OptionalIf("fulltext", "You must provide the DOI or the Full-Text URL"), validators.Regexp(regex=regex.DOI_COMPILED, message=DOI_ERROR)], description="(You must provide a DOI and/or a Full-Text URL)")
    authors = FieldList(FormField(AuthorForm), min_entries=1) # We have to do the validation for this at a higher level
    abstract = TextAreaField("Abstract", [validators.Optional(), NoScriptTag()])
    keywords = TagListField("Keywords", [validators.Optional(), NoScriptTag()], description="Use a , to separate keywords") # enhanced with select2
    fulltext = StringField("Full-text URL", [OptionalIf("doi", "You must provide the Full-Text URL or the DOI"), validators.URL()])
    publication_year = DOAJSelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = DOAJSelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = DOAJSelectField("Print", [ThisOrThat("eissn", "Either this field or Online ISSN is required"), DifferentTo("eissn", message=IDENTICAL_ISSNS_ERROR)], choices=[]) # choices set at construction
    eissn = DOAJSelectField("Online", [ThisOrThat("pissn", "Either this field or Print ISSN is required"), DifferentTo("pissn", message=IDENTICAL_ISSNS_ERROR)], choices=[]) # choices set at construction

    volume = StringField("Volume", [validators.Optional(), NoScriptTag()])
    number = StringField("Issue", [validators.Optional(), NoScriptTag()])
    start = StringField("Start", [validators.Optional(), NoScriptTag()])
    end = StringField("End", [validators.Optional(), NoScriptTag()])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        try:
            self.pissn.choices = choices_for_article_issns(current_user)
            self.eissn.choices = choices_for_article_issns(current_user)
        except:
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass



#########################################
# Formcontexts and factory

class ArticleFormFactory(object):
    """
    ~~ArticleForm:Factory->AdminArticleMetadata:FormContext~~
    ~~->PublisherArticleMetadata:FormContext~~
    """
    @classmethod
    def get_from_context(cls, role, source=None, form_data=None, user=None):
        if role == "admin":
            return AdminMetadataArticleForm(source=source, form_data=form_data, user=user)
        if role == "publisher":
            return PublisherMetadataForm(source=source, form_data=form_data, user=user)


class MetadataForm(FormContext):
    """
    ~~ArticleMetadata:FormContext->Article:Form~~
    ~~->ArticleForm:Crosswalk~~
    ~~->Article:Service~~
    """

    def __init__(self, source, form_data, user):
        self.user = user
        self.author_error = False
        super(MetadataForm, self).__init__(source=source, form_data=form_data)

    def _set_choices(self):
        try:
            ic = choices_for_article_issns(user=self.user, article_id=self.source.id)
            self.form.pissn.choices = ic
            self.form.eissn.choices = ic
        except Exception as e:
            print (str(e))
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass

    def modify_authors_if_required(self, request_data):

        more_authors = request_data.get("more_authors")
        remove_author = None
        for v in list(request.values.keys()):
            if v.startswith("remove_authors"):
                remove_author = v.split("-")[1]

        # if the user wants more authors, add an extra entry
        if more_authors:
            return self.render_template(more_authors=True)

        # if the user wants to remove an author, do the various back-flips required
        if remove_author is not None:
            return self.render_template(remove_authors=remove_author)

    def _check_for_author_errors(self, **kwargs):

        if "more_authors" in kwargs and kwargs["more_authors"] == True:
            self.form.authors.append_entry()
        if "remove_authors" in kwargs:
            keep = []
            while len(self.form.authors.entries) > 0:
                entry = self.form.authors.pop_entry()
                if entry.short_name == "authors-" + kwargs["remove_author"]:
                    break
                else:
                    keep.append(entry)
            while len(keep) > 0:
                self.form.authors.append_entry(keep.pop().data)

    def _validate_authors(self):
        counted = 0
        for entry in self.form.authors.entries:
            name = entry.data.get("name")
            if name is not None and name != "":
                counted += 1
        return counted >= 1

    def blank_form(self):
        self.form = ArticleForm()
        self._set_choices()

    def source2form(self):
        self.form = ArticleForm()
        ArticleFormXWalk.obj2form(self.form, article=self.source)
        self._set_choices()

    def data2form(self):
        self.form = ArticleForm(formdata=self.form_data)
        self._set_choices()

    def form2target(self):
        self.target = ArticleFormXWalk.form2obj(form=self.form)

    def validate(self):
        if not self._validate_authors():
            self.author_error = True
        if not self.form.validate():
            return False
        return True

    def finalise(self, duplicate_check = True):
        self.form2target()
        if not self.author_error:
            article_service = DOAJ.articleService()
            article_service.create_article(self.target, self.user, add_journal_info=True,
                                           update_article_id=self.source.id if self.source is not None else None,
                                           duplicate_check = duplicate_check)
            article_url = url_for('doaj.article_page', identifier=self.target.id)
            msg, how = Messages.ARTICLE_METADATA_SUBMITTED_FLASH
            Messages.flash_with_url(msg.format(url=article_url), how)
        else:
            return


class PublisherMetadataForm(MetadataForm):
    """
    ~~PublisherArticleMetadata:FormContext->ArticleMetadata:FormContext~~
    """
    def __init__(self, source, form_data, user):
        super(PublisherMetadataForm, self).__init__(source=source, form_data=form_data, user=user)

    def set_template(self):
        self.template = "publisher/metadata.html"

    def render_template(self, **kwargs):
        self._check_for_author_errors(**kwargs)
        if "validated" in kwargs and kwargs["validated"] == True:
            self.blank_form()
        return render_template(self.template, form=self.form, form_context=self, author_error=self.author_error)


class AdminMetadataArticleForm(MetadataForm):
    """
    ~~AdminArticleMetadata:FormContext->ArticleMetadata:FormContext~~
    """
    def __init__(self, source, form_data, user):
        super(AdminMetadataArticleForm, self).__init__(source=source, form_data=form_data, user=user)

    def set_template(self):
        self.template = "admin/article_metadata.html"

    def render_template(self, **kwargs):
        self._check_for_author_errors(**kwargs)
        return render_template(self.template, form=self.form, form_context=self, author_error=self.author_error)
