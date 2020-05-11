"""
EXAMPLE = {
    "contexts" : {
        "[context name]" : {
            "fieldsets" : [
                "[fieldset name]"
            ],
            "asynchronous_warnings" : [
                "[warning function reference]"
            ]
        }
    },
    "fieldsets" : {
        "[fieldset name]" : {
            "label" : "[label]",
            "fields" : [
                "[field name]"
            ]
        }
    },
    "fields" : {
        "[field name]" : {
            "label" : "[label]",
            "input" : "[input type: radio|text|taglist|select|checkbox]",
            "multiple" : "[select multiple True|False]",
            "datatype" : "[coerce datatype]",
            "options" : [   # for radio, select and checkbox
                {
                    "display" : "[display value]",
                    "value" : "[stored value]",
                    "exclusive" : "[exclusive: True|False]", # if you select this option you can't select others
                    "subfields" : ["[field name]"]
                }
            ],
            "options_fn" : "function name to generate options",
            "default" : "[default value]",
            "disabled" : "[disabled: True|False]",
            "conditional" : [   # conditions to AND together
                {
                    "field" : "[field name]",
                    "value" : "[field value]"
                }
            ],
            "help" : {
                "placeholder" : "[input field placeholder text]",
                "description" : "[description]",
                "tooltip" : "[tooltip/long description]",
                "doaj_criteria" : "[doaj compliance criteria]",
                "seal_criteria" : "[doaj compliance criteria]"
            },
            "validate" : {
                "[validate function]",
                {"[validate function]" : {"arg" : "argval"}}
            },
            "widgets" : {
                "[widget function]",
                {"[widget function]" : {"arg" : "argval"}}
            },
            "postprocessing" : {
                "[processing function]",
                {"[processing function]" : {"arg" : "argval"}}
            },
            "attr" : {
                "[html attribute name]" : "[html attribute value]"
            },
            "contexts" : {
                "[context name]" : {
                    "[field property]" : "[field property value]"
                }
            }
         }
    }
}

CONTEXT_EXAMPLE = {
    "fieldsets" : [
        {
            "name" : "[fieldset name]",
            "label" : "[label]",
            "fields" : [
                {
                    "name" : "[field name]",
                    "[field property]" : "[field property value]"
                }
            ]
        }
    ],
    "asynchronous_warnings" : [
        "[warning function reference]"
    ],
    "template" : "path/to/form/page/template.html",
    "crosswalks" : {
        "obj2form" : "crosswalk.obj2form",
        "form2obj" : "crosswalk.form2obj"
    },
    "processor" : "module.path.to.processor"
}
"""

from copy import deepcopy
from wtforms import Form
from wtforms.fields.core import UnboundField
from portality.lib import plugin
from flask import render_template
import json


UI_CONFIG_FIELDS = [
    "label",
    "input",
    "options",
    "help",
    "validate",
    "visible",
    "conditional",
    "widgets",
    "attr",
    "multiple",
    "repeatable",
    "datatype",
    "disabled",
    "name",
    "subfields",
    "subfield",
    "group"
]


class FormulaicException(Exception):
    def __init__(self, message):
        self.message = message
        super(FormulaicException, self).__init__()


class Formulaic(object):
    def __init__(self, definition, wtforms_builders, function_map=None, javascript_functions=None):
        self._definition = definition
        self._wtforms_builders = wtforms_builders
        self._function_map = function_map
        self._javascript_functions = javascript_functions

    def context(self, context_name):
        context_def = deepcopy(self._definition.get("contexts", {}).get(context_name))
        if context_def is None:
            return None

        fieldsets = context_def.get("fieldsets", [])

        expanded_fieldsets = []
        for fsn in fieldsets:
            fieldset_def = deepcopy(self._definition.get("fieldsets", {}).get(fsn))
            if fieldset_def is None:
                raise FormulaicException("Unable to locate fieldset with name {x} in context {y}".format(x=fsn, y=context_name))
            fieldset_def["name"] = fsn

            expanded_fields = self._process_fields(context_name, fieldset_def.get("fields", []))

            fieldset_def["fields"] = expanded_fields
            expanded_fieldsets.append(fieldset_def)

        context_def["fieldsets"] = expanded_fieldsets
        return FormulaicContext(context_def, self)

    @property
    def wtforms_builders(self):
        return self._wtforms_builders

    @property
    def function_map(self):
        return self._function_map

    @property
    def javascript_functions(self):
        return self._javascript_functions

    def choices_for(self, field_name):
        field_def = self._definition.get("fields", {}).get(field_name)
        if field_def is None:
            return []
        return FormulaicField._options2choices(field_def, self.function_map)

    def _process_fields(self, context_name, field_names):
        field_defs = []
        for fn in field_names:
            field_def = deepcopy(self._definition.get("fields", {}).get(fn))
            field_def["name"] = fn
            if field_def is None:
                raise FormulaicException("Field '{x}' is referenced but not defined".format(x=fn))

            # filter for context
            context_overrides = field_def.get("contexts", {}).get(context_name)
            if context_overrides is not None:
                for k, v in context_overrides.items():
                    field_def[k] = v

            # if there is an options_fn, expand them into the options field
            if "options_fn" in field_def:
                opt_fn = self._function_map.get("options", {}).get(field_def["options_fn"])
                if opt_fn is None:
                    raise FormulaicException("No function mapping defined for function reference '{x}'".format(x=field_def["options_fn"]))
                if isinstance(opt_fn, str):
                    opt_fn = plugin.load_function(opt_fn)
                field_def["options"] = opt_fn(field_def)

            # and remove the context overrides settings, so they don't bleed to contexts that don't require them
            if "contexts" in field_def:
                del field_def["contexts"]

            field_defs.append(field_def)

        return field_defs


class FormulaicContext(object):
    def __init__(self, definition: dict, parent: Formulaic):
        self._definition = definition
        self._formulaic = parent
        self._wtform_class = None
        self._wtform_inst = None

        self._wtform_class = self.wtform_class()
        self._wtform_inst = self.wtform()

    @property
    def wtforms_builders(self):
        return self._formulaic.wtforms_builders

    @property
    def function_map(self):
        return self._formulaic.function_map

    @property
    def wtform_inst(self):
        return self._wtform_inst

    @property
    def javascript_functions(self):
        return self._formulaic.javascript_functions

    @property
    def ui_settings(self):
        ui = deepcopy(self._definition.get("fieldsets", []))
        for fieldset in ui:
            for field in fieldset.get("fields", []):
                for fn in [k for k in field.keys()]:
                    if fn not in UI_CONFIG_FIELDS:
                        del field[fn]
        return ui

    @property
    def default_field_template(self):
        return self._definition.get("templates", {}).get("default_field")

    @property
    def default_group_template(self):
        return self._definition.get("templates", {}).get("default_group")

    def make_wtform_class(self, fields):
        class TempForm(Form):
            pass

        for field in fields:
            self.bind_wtforms_field(TempForm, field)

        return TempForm

    def wtform_class(self):
        if self._wtform_class is not None:
            return self._wtform_class

        # FIXME: we should just store a list of fields in the context, and reference them
        # from the fieldset, which would get rid of a lot of this double-layered looping
        fields = []
        for fieldset in self._definition.get("fieldsets", []):
            for field in fieldset.get("fields", []):
                if "group" in field:
                    continue
                fields.append(field)

        klazz = self.make_wtform_class(fields)
        self._wtform_class = klazz
        return self._wtform_class

    def wtform(self, formdata=None, data=None):
        klazz = self.wtform_class()
        self._wtform_inst = klazz(formdata=formdata, data=data)
        return self._wtform_inst

    def get(self, field_name, parent=None):
        if parent is None:
            parent = self
        for fs in self._definition.get("fieldsets", []):
            for f in fs.get("fields", []):
                if f.get("name") == field_name:
                    return FormulaicField(f, parent)

    def fieldset(self, fieldset_name):
        for fs in self._definition.get("fieldsets", []):
            if fs.get("name") == fieldset_name:
                return FormulaicFieldset(fs, self)
        return None

    def fieldsets(self):
        return [FormulaicFieldset(fs, self) for fs in self._definition.get("fieldsets", [])]

    def json(self):
        return json.dumps(self._definition)

    def render_template(self, **kwargs):
        template = self._definition.get("templates", {}).get("form")
        return render_template(template, formulaic_context=self, **kwargs)

    def processor(self, formdata=None, source=None):
        klazz = self._definition.get("processor")
        if isinstance(klazz, str):
            klazz = plugin.load_class(klazz)
        return klazz(formdata=formdata, source=source, parent=self)

    def obj2form(self, obj):
        xwalk_fn = self._definition.get("crosswalks", {}).get("obj2form")
        if xwalk_fn is None:
            return None
        if isinstance(xwalk_fn, str):
            xwalk_fn = plugin.load_function(xwalk_fn)
        data = xwalk_fn(obj)
        return self.wtform(data=data)

    def form2obj(self):
        xwalk_fn = self._definition.get("crosswalks", {}).get("form2obj")
        if xwalk_fn is None:
            return None
        if isinstance(xwalk_fn, str):
            xwalk_fn = plugin.load_function(xwalk_fn)
        return xwalk_fn(self._wtform_inst)

    def bind_wtforms_field(self, FormClass, field):
        field_name = field.get("name")
        if not hasattr(FormClass, field_name):
            field_definition = FormulaicField.make_wtforms_field(self, field)
            setattr(FormClass, field_name, field_definition)


class FormulaicFieldset(object):
    def __init__(self, definition, parent):
        self._definition = definition
        self._formulaic_context = parent

    @property
    def wtforms_builders(self):
        return self._formulaic_context.wtforms_builders

    @property
    def function_map(self):
        return self._formulaic_context.function_map

    @property
    def wtform_inst(self):
        return self._formulaic_context.wtform_inst

    @property
    def default_field_template(self):
        return self._formulaic_context.default_field_template

    @property
    def default_group_template(self):
        return self._formulaic_context.default_group_template

    def fields(self):
        return [FormulaicField(f, self) for f in
                self._definition.get("fields", []) if not f.get("subfield")]

    def field(self, field_name):
        for f in self._definition.get("fields", []):
            if f.get("name") == field_name:
                return FormulaicField(f, self)

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if name in self._definition:
            return self._definition[name]

        raise AttributeError('{name} is not set'.format(name=name))


class FormulaicField(object):
    def __init__(self, definition, parent):
        self._definition = definition
        self._formulaic_fieldset = parent

    def __contains__(self, item):
        return item in self._definition

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if name in self._definition:
            return self._definition[name]

        raise AttributeError('{name} is not set'.format(name=name))

    def get(self, attr, default=None):
        return self._definition.get(attr, default)

    def help(self, key):
        return self._definition.get("help", {}).get(key)

    @property
    def wtforms_builders(self):
        return self._formulaic_fieldset.wtforms_builders

    @property
    def function_map(self):
        return self._formulaic_fieldset.function_map

    @property
    def wtform_inst(self):
        if "group" in self._definition:
            group = self._definition["group"]
            group_field = self._formulaic_fieldset.field(group)
            return group_field.wtfield
        return self._formulaic_fieldset.wtform_inst

    @property
    def wtfield(self):
        name = self._definition.get("name")
        return getattr(self.wtform_inst, name)

    @property
    def explicit_options(self):
        opts = self._definition.get("options", [])
        if isinstance(opts, list):
            return opts
        return []

    @property
    def has_conditional(self):
        return len(self._definition.get("conditional", [])) > 0

    @property
    def template(self):
        local = self._definition.get("template")
        if local is not None:
            return local

        if self._definition.get("input") == "group":
            return self._formulaic_fieldset.default_group_template

        return self._formulaic_fieldset.default_field_template

    def has_validator(self, validator_name):
        for validator in self._definition.get("validate", []):
            if isinstance(validator, str) and validator == validator_name:
                return True
            if isinstance(validator, dict):
                if list(validator.keys())[0] == validator_name:
                    return True
        return False

    def get_validator_settings(self, validator_name):
        for validator in self._definition.get("validate", []):
            if isinstance(validator, str) and validator == validator_name:
                return {}
            if isinstance(validator, dict):
                name = list(validator.keys())[0]
                if name == validator_name:
                    return validator[name]
        return False

    def validators(self):
        for validator in self._definition.get("validate", []):
            if isinstance(validator, str):
                yield validator, {}
            if isinstance(validator, dict):
                name = list(validator.keys())[0]
                yield name, validator[name]

    def get_subfields(self, option_value):
        for option in self.explicit_options:
            if option.get("value") == option_value:
                sfs = []
                for sf in option.get("subfields", []):
                    subimpl = self._formulaic_fieldset._formulaic_context.get(sf, self._formulaic_fieldset)
                    sfs.append(subimpl)
                return sfs

    def group_subfields(self):
        subs = self._definition.get("subfields")
        if subs is None:
            return None
        return [self._formulaic_fieldset.field(s) for s in subs]

    def has_options_subfields(self):
        for option in self.explicit_options:
            if len(option.get("subfields", [])) > 0:
                return True
        return False

    def has_errors(self):
        return len(self.errors()) > 0

    def errors(self):
        wtf = self.wtfield
        return wtf.errors

    def render_form_control(self, custom_args=None):
        kwargs = deepcopy(self._definition.get("attr", {}))
        if "placeholder" in self._definition.get("help", {}):
            kwargs["placeholder"] = self._definition["help"]["placeholder"]

        render_functions = self.function_map.get("validate", {}).get("render", {})
        for validator, settings in self.validators():
            if validator in render_functions:
                fn = render_functions[validator]
                if isinstance(fn, str):
                    fn = plugin.load_function(fn)
                fn(settings, kwargs)

        if self.has_options_subfields():
            kwargs["formulaic"] = self

        # allow custom args to overwite all other arguments
        if custom_args is not None:
            for k, v in custom_args.items():
                kwargs[k] = v

        wtf = self.wtfield
        return wtf(**kwargs)

    @classmethod
    def make_wtforms_field(cls, formulaic_context, field) -> UnboundField:
        builder = cls._get_wtforms_builder(field, formulaic_context.wtforms_builders)
        if builder is None:
            raise FormulaicException("No WTForms mapping for field '{x}'".format(x=field.get("name")))

        validators = []
        vfuncs = formulaic_context.function_map.get("validate", {}).get("wtforms", {})
        for v in field.get("validate", []):
            vname = v
            args = {}
            if isinstance(v, dict):
                vname = list(v.keys())[0]
                args = v[vname]
            if vname not in vfuncs:
                raise FormulaicException("No validate WTForms function defined for {x} in python function references".format(x=vname))
            vfn = vfuncs[vname]
            if isinstance(vfn, str):
                vfn = plugin.load_function(vfn)
            validators.append(vfn(field, args))

        wtargs = {
            "label" : field.get("label"),
            "validators" : validators,
            "description": field.get("help", {}).get("description"),
        }
        if "default" in field:
            wtargs["default"] = field["default"]
        if "options" in field or "options_fn" in field:
            wtargs["choices"] = cls._options2choices(field, formulaic_context.function_map.get("options", {}))

        return builder(formulaic_context, field, wtargs)

    @classmethod
    def _get_wtforms_builder(self, field, wtforms_builders):
        for builder in wtforms_builders:
            if builder.match(field):
                return builder.wtform
        return None

    @classmethod
    def _options2choices(self, field, function_map):
        options = field.get("options", [])
        if len(options) == 0 and "options_fn" in field:
            fnpath = function_map.get(field["options_fn"])
            if fnpath is None:
                raise FormulaicException("No function mapping defined for function reference '{x}'".format(x=field["options_fn"]))
            fn = plugin.load_function(fnpath)
            options = fn()

        choices = []
        for o in options:
            display = o.get("display")
            value = o.get("value")
            if value is None:
                value = o.get("display")
            choices.append((value, display))

        return choices


class FormProcessor(object):
    def __init__(self, formdata=None, source=None, parent: FormulaicContext=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._formdata = formdata
        self._alert = []
        self._info = ''
        self._formulaic = parent

        # now create our form instance, with the form_data (if there is any)
        if formdata is not None:
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
        # return self._form
        return self._formulaic.wtform_inst

    @property
    def source(self):
        return self._source

    @property
    def form_data(self):
        return self._formdata

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, val):
        self._target = val

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

    #############################################################
    # Lifecycle functions you don't have to overwrite unless you
    # want to do something different
    #############################################################

    def blank_form(self):
        """
        This will be called during init, and must populate the self.form_data property with an instance of the form in this
        context, based on no originating source or form data
        """
        self._formulaic.wtform()

    def data2form(self):
        """
        This will be called during init, and must convert the form_data into an instance of the form in this context,
        and write to self.form
        """
        self._formulaic.wtform(formdata=self.form_data)

    def source2form(self):
        """
        This will be called during init, and must convert the source object into an instance of the form in this
        context, and write to self.form
        """
        self._formulaic.obj2form(self.source)

    def form2target(self):
        """
        Convert the form object into a the target system object, and write to self.target
        """
        self.target = self._formulaic.form2obj()

    ############################################################
    # Lifecycle functions that subclasses should implement
    ############################################################

    def pre_validate(self):
        """
        This will be run before validation against the form is run.
        Use it to patch the form with any relevant data, such as fields which were disabled
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

    def draft(self, *args, **kwargs):
        pass

    ############################################################
    # Functions which can be called directly, but may be overridden if desired
    ############################################################

    def validate(self):
        self.pre_validate()
        f = self.form
        valid = False
        if f is not None:
            valid = f.validate()

        return valid

    @property
    def errors(self):
        f = self.form
        if f is not None:
            return f.errors
        return False


class WTFormsBuilder:
    @staticmethod
    def match(field):
        return False

    @staticmethod
    def wtform(formulaic_context, field, wtfargs):
        return None