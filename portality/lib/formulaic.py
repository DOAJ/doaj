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

import inspect
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
    "datatype",
    "disabled",
    "name"
]


class FormulaicException(Exception):
    def __init__(self, message):
        self.message = message
        super(FormulaicException, self).__init__()


class Formulaic(object):
    def __init__(self, definition, wtforms_map, function_map=None, javascript_functions=None):
        self._definition = definition
        self._wtforms_map = wtforms_map
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
            fieldset_def["name"] = fsn

            expanded_fields = self._process_fields(context_name, fieldset_def.get("fields", []))

            fieldset_def["fields"] = expanded_fields
            expanded_fieldsets.append(fieldset_def)

        context_def["fieldsets"] = expanded_fieldsets
        return FormulaicContext(context_def, self._wtforms_map, self._function_map, self)

    @property
    def javascript_functions(self):
        return self._javascript_functions

    def _process_fields(self, context_name, field_names):
        field_defs = []
        for fn in field_names:
            field_def = deepcopy(self._definition.get("fields", {}).get(fn))
            field_def["name"] = fn
            if field_def is None:
                raise FormulaicException("Field '{x}' is referenced but not defined".format(x=fn))

            # check for subfields
            """
            for o in field_def.get("options", []):
                if isinstance(o, str):  # it's a function reference
                    continue
                subfields = o.get("subfields")
                if subfields is not None:
                    o["subfields"] = self._process_fields(context_name, subfields)
            """
            # filter for context
            context_overrides = field_def.get("contexts", {}).get(context_name)
            if context_overrides is not None:
                for k, v in context_overrides.items():
                    field_def[k] = v

            # and remove the context overrides settings, so they don't bleed to contexts that don't require them
            if "contexts" in field_def:
                del field_def["contexts"]

            field_defs.append(field_def)

        return field_defs


class FormulaicContext(object):
    def __init__(self, definition, wtforms_map, function_map, parent):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map
        self._formulaic = parent

    def wtform_class(self):
        class TempForm(Form):
            pass

        for fieldset in self._definition.get("fieldsets", []):
            for field in fieldset.get("fields", []):
                # add the main fields
                self._add_wtforms_field(TempForm, field)

                # add any subfields
                """
                options = field.get("options", [])
                if not isinstance(options, str):
                    for o in field.get("options", []):
                        for subfield in o.get("subfields", []):
                            self._add_wtforms_field(TempForm, subfield)
                """
        return TempForm

    def wtform(self, formdata=None, data=None):
        klazz = self.wtform_class()
        return klazz(formdata=formdata, data=data)

    def get(self, field_name, parent=None):
        if parent is None:
            parent = self
        for fs in self._definition.get("fieldsets", []):
            for f in fs.get("fields", []):
                if f.get("name") == field_name:
                    return FormulaicField(f, self._wtforms_map, self._function_map, parent)

    def fieldset(self, fieldset_name):
        for fs in self._definition.get("fieldsets", []):
            if fs.get("name") == fieldset_name:
                return FormulaicFieldset(fs, self._wtforms_map, self._function_map, self)
        return None

    def fieldsets(self):
        return [FormulaicFieldset(fs, self._wtforms_map, self._function_map, self) for fs in self._definition.get("fieldsets", [])]

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
    def javascript_functions(self):
        return self._formulaic.javascript_functions

    def json(self):
        return json.dumps(self._definition)

    def render_template(self, **kwargs):
        template = self._definition.get("template")
        return render_template(template, formulaic_context=self, **kwargs)

    def processor(self, form_data=None, source=None):
        processor_path = self._definition.get("processor")
        klazz = plugin.load_class(processor_path)
        return klazz(form_data=form_data, source=source, formulaic_context=self)

    def obj2form(self, obj):
        xwalk_path = self._definition.get("crosswalks", {}).get("obj2form")
        if xwalk_path is None:
            return None
        xwalk_fn = plugin.load_function(xwalk_path)
        data = xwalk_fn(obj)
        return self.wtform(data=data)

    def form2obj(self, form):
        xwalk_path = self._definition.get("crosswalks", {}).get("form2obj")
        if xwalk_path is None:
            return None
        xwalk_fn = plugin.load_function(xwalk_path)
        return xwalk_fn(form)

    def _add_wtforms_field(self, FormClass, field):
        field_name = field.get("name")
        if not hasattr(FormClass, field_name):
            # field_definition = self._wtforms_field_definition(field)
            field_definition = FormulaicField.make_wtforms_field(field, self._wtforms_map, self._function_map)
            setattr(FormClass, field_name, field_definition)


class FormulaicFieldset(object):
    def __init__(self, definition, wtforms_map, function_map, parent):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map
        self._formulaic_context = parent

    def fields(self):
        return [FormulaicField(f, self._wtforms_map, self._function_map, self) for f in
                self._definition.get("fields", []) if not f.get("subfield")]

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if name in self._definition:
            return self._definition[name]

        raise AttributeError('{name} is not set'.format(name=name))


class FormulaicField(object):
    def __init__(self, definition, wtforms_map, function_map, parent):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map
        self._wtform_field = None
        self._wtforms_field_bound = None
        self._formulaic_fieldset = parent

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if name in self._definition:
            return self._definition[name]

        raise AttributeError('{name} is not set'.format(name=name))

    @property
    def explicit_options(self):
        opts = self._definition.get("options", [])
        if isinstance(opts, list):
            return opts
        return []

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

    @property
    def has_conditional(self):
        return len(self._definition.get("conditional", [])) > 0

    def wtforms_field(self):
        if self._wtform_field is None:
            self._wtform_field = FormulaicField.make_wtforms_field(self._definition, self._wtforms_map, self._function_map)
        return self._wtform_field

    def wtforms_field_bound(self):
        if self._wtforms_field_bound is None:
            wtf = self.wtforms_field()
            if isinstance(wtf, UnboundField):
                class TempForm(Form):
                    pass

                setattr(TempForm, self._definition.get("name"), wtf)
                form_instance = TempForm()
                self._wtforms_field_bound = form_instance[self._definition.get("name")]
            else:
                self._wtforms_field_bound = wtf

        return self._wtforms_field_bound

    def get_subfields(self, option_value):
        for option in self.explicit_options:
            if option.get("value") == option_value:
                sfs = []
                for sf in option.get("subfields", []):
                    subimpl = self._formulaic_fieldset._formulaic_context.get(sf, self._formulaic_fieldset)
                    sfs.append(subimpl)
                return sfs

    def has_subfields(self):
        for option in self.explicit_options:
            if len(option.get("subfields", [])) > 0:
                return True
        return False

    def has_errors(self):
        return len(self.errors()) > 0

    def errors(self):
        wtf = self.wtforms_field_bound()
        return wtf.errors

    def render_form_control(self, custom_args=None):
        kwargs = deepcopy(self._definition.get("attr", {}))
        if "placeholder" in self._definition.get("help", {}):
            kwargs["placeholder"] = self._definition["help"]["placeholder"]

        render_functions = self._function_map.get("validate", {}).get("render", {})
        for validator, settings in self.validators():
            if validator in render_functions:
                function_path = render_functions[validator]
                fn = plugin.load_function(function_path)
                fn(settings, kwargs)

        if self.has_subfields():
            kwargs["formulaic"] = self

        # allow custom args to overwite all other arguments
        if custom_args is not None:
            for k, v in custom_args.items():
                kwargs[k] = v

        wtf = self.wtforms_field_bound()
        return wtf(**kwargs)

    @classmethod
    def make_wtforms_field(cls, field, wtforms_map, function_map):
        result = cls._get_wtforms_map(field, wtforms_map)
        if result is None:
            raise FormulaicException("No WTForms mapping for field '{x}'".format(x=field.get("name")))
        klazz = result.get("class")
        kwargs = {
            "label": field.get("label")
        }
        if "init" in result:
            for k, v in result["init"].items():
                if inspect.isclass(v) or inspect.isfunction(v):
                    v = v()
                kwargs[k] = v
        if "description" in field.get("help", {}):
            kwargs["description"] = field["help"]["description"]
        if "default" in field:
            kwargs["default"] = field["default"]
        if "options" in field:
            kwargs["choices"] = cls._options2choices(field["options"], function_map.get("options", {}))

        return klazz(**kwargs)

    @classmethod
    def _get_wtforms_map(self, field, wtforms_map):
        input = field.get("input")
        options = "options" in field
        datatype = field.get("datatype")

        for possible in wtforms_map:
            match = possible.get("match")
            input_match = "input" not in match or match.get("input") == input
            options_match = "options" not in match or match.get("options", False) == options
            datatype_match = "datatype" not in match or match.get("datatype") == datatype

            if input_match and options_match and datatype_match:
                return possible.get("wtforms")

        return None

    @classmethod
    def _options2choices(self, options, function_map):
        if isinstance(options, str): # it's a function reference
            fnpath = function_map.get(options)
            if fnpath is None:
                raise FormulaicException("No function mapping defined for function reference '{x}'".format(x=options))
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
    def __init__(self, form_data=None, source=None, formulaic_context=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None
        self._alert = []
        self._info = ''
        self._formulaic = formulaic_context

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

    #############################################################
    # Lifecycle functions you don't have to overwrite unless you
    # want to do something different
    #############################################################

    def blank_form(self):
        """
        This will be called during init, and must populate the self.form_data property with an instance of the form in this
        context, based on no originating source or form data
        """
        self.form = self._formulaic.wtform()

    def data2form(self):
        """
        This will be called during init, and must convert the form_data into an instance of the form in this context,
        and write to self.form
        """
        self.form = self._formulaic.wtform(formdata=self.form_data)

    def source2form(self):
        """
        This will be called during init, and must convert the source object into an instance of the form in this
        context, and write to self.form
        """
        self.form = self._formulaic.obj2form(self.source)

    def form2target(self):
        """
        Convert the form object into a the target system object, and write to self.target
        """
        self.target = self._formulaic.form2obj(self.form)

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
            if self.renderer is not None:
                self.renderer.set_error_fields(error_fields)

        return valid

    @property
    def errors(self):
        f = self.form
        if f is not None:
            return f.errors
        return False
