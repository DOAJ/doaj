from portality.formcontext.formhelper import FormHelperBS3
from copy import deepcopy


class Renderer(object):
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
