from flask import render_template, url_for, request

import portality.formcontext.forms
from portality.crosswalks.article_form import ArticleFormXWalk
from portality.bll import DOAJ
from portality.formcontext import render, choices
from portality.ui.messages import Messages


class FormContext(object):
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
            self.renderer = render.Renderer()

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


class ArticleFormFactory(object):
    @classmethod
    def get_from_context(cls, role, source=None, form_data=None, user=None):
        if role == "admin":
            return AdminMetadataArticleForm(source=source, form_data=form_data, user=user)
        if role == "publisher":
            return PublisherMetadataForm(source=source, form_data=form_data, user=user)


class MetadataForm(FormContext):

    def __init__(self, source, form_data, user):
        self.user = user
        self.author_error = False
        super(MetadataForm, self).__init__(source=source, form_data=form_data)

    def _set_choices(self):
        try:
            ic = choices.Choices.choices_for_article_issns(user=self.user, article_id=self.source.id)
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
        self.form = portality.formcontext.forms.ArticleForm()
        self._set_choices()

    def source2form(self):
        self.form = portality.formcontext.forms.ArticleForm()
        ArticleFormXWalk.obj2form(self.form, article=self.source)
        self._set_choices()

    def data2form(self):
        self.form = portality.formcontext.forms.ArticleForm(formdata=self.form_data)
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

    def __init__(self, source, form_data, user):
        super(AdminMetadataArticleForm, self).__init__(source=source, form_data=form_data, user=user)

    def set_template(self):
        self.template = "admin/article_metadata.html"

    def render_template(self, **kwargs):
        self._check_for_author_errors(**kwargs)
        return render_template(self.template, form=self.form, form_context=self, author_error=self.author_error)
