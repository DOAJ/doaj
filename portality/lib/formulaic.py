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
    ]
}
"""

from copy import deepcopy
from wtforms import Form, validators
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, FormField, FieldList, RadioField, SelectMultipleField, SelectField
from wtforms import widgets
from wtforms.fields.core import UnboundField
from wtforms.widgets.core import html_params, HTMLString
from portality.formcontext.fields import TagListField
from portality.lib import plugin

import inspect
import json

class NumberWidget(widgets.Input):
    input_type = 'number'


class ListWidgetWithSubfields(object):
    """
    Renders a list of fields as a `ul` or `ol` list.

    This is used for fields which encapsulate many inner fields as subfields.
    The widget will try to iterate the field to get access to the subfields and
    call them to render them.

    If `prefix_label` is set, the subfield's label is printed before the field,
    otherwise afterwards. The latter is useful for iterating radios or
    checkboxes.
    """
    def __init__(self, html_tag='ul', prefix_label=False):
        assert html_tag in ('ol', 'ul')
        self.html_tag = html_tag
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        #required = False
        #if required in kwargs:
        #    required = True
        #    del kwargs["required"]
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<li>%s %s' % (subfield.label, subfield(**kwargs)))
            else:
                html.append('<li>%s %s' % (subfield(**kwargs), subfield.label))

            if "formulaic" in kwargs:
                sfs = kwargs["formulaic"].get_subfields(subfield._value())
                for sf in sfs:
                    html.append(sf.render_form_control())

            html.append("</li>")

        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


WTFORMS_MAP = [
    {
        "match" : {"input" : "radio"},
        "wtforms" : {"class" : RadioField}
    },
    {
        "match" : {"input" : "checkbox", "options" : True},
        "wtforms" : {"class" : SelectMultipleField, "init" : {"option_widget" : widgets.CheckboxInput, "widget" : ListWidgetWithSubfields}}
    },
    {
        "match" : {"input" : "checkbox", "options" : False},
        "wtforms" : {"class" : BooleanField}
    },
    {
        "match" : {"input" : "select"},
        "wtforms" : {"class" : SelectField}
    },
    {
        "match" : {"input" : "select"},
        "wtforms" : {"class", SelectMultipleField}
    },
    {
        "match" : {"input" : "text"},
        "wtforms" : {"class" : StringField}
    },
    {
        "match" : {"input" : "taglist"},
        "wtforms" : {"class" : TagListField}
    },
    {
        "match" : {"input" : "number", "datatype" : "integer"},
        "wtforms" : {"class": IntegerField, "init" : {"widget" : NumberWidget}}
    }
]

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
    def __init__(self, definition, wtforms_map=WTFORMS_MAP, function_map=None):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map

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
        return FormulaicContext(context_def, self._wtforms_map, self._function_map)

    def _process_fields(self, context_name, field_names):
        field_defs = []
        for fn in field_names:
            field_def = deepcopy(self._definition.get("fields", {}).get(fn))
            field_def["name"] = fn
            if field_def is None:
                raise FormulaicException("Field '{x}' is referenced but not defined".format(x=fn))

            # check for subfields
            for o in field_def.get("options", []):
                if isinstance(o, str):  # it's a function reference
                    continue
                subfields = o.get("subfields")
                if subfields is not None:
                    o["subfields"] = self._process_fields(context_name, subfields)

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
    def __init__(self, definition, wtforms_map, function_map):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map

    def wtform_class(self):
        class TempForm(Form):
            pass

        for fieldset in self._definition.get("fieldsets", []):
            for field in fieldset.get("fields", []):
                # add the main fields
                self._add_wtforms_field(TempForm, field)

                # add any subfields
                options = field.get("options", [])
                if not isinstance(options, str):
                    for o in field.get("options", []):
                        for subfield in o.get("subfields", []):
                            self._add_wtforms_field(TempForm, subfield)

        return TempForm

    def wtform(self, form_data=None):
        klazz = self.wtform_class()
        return klazz(form_data)

    def get(self, field_name):
        """returns the first instance of the field, only really for use in testing"""
        for fs in self._definition.get("fieldsets", []):
            for f in fs.get("fields", []):
                if f.get("name") == field_name:
                    return FormulaicField(f, self._wtforms_map, self._function_map)

    def fieldsets(self):
        return [FormulaicFieldset(fs, self._wtforms_map, self._function_map) for fs in self._definition.get("fieldsets", [])]

    @property
    def ui_settings(self):
        ui = deepcopy(self._definition.get("fieldsets", []))
        for fieldset in ui:
            for field in fieldset.get("fields", []):
                for fn in [k for k in field.keys()]:
                    if fn not in UI_CONFIG_FIELDS:
                        del field[fn]
        return ui

    def json(self):
        return json.dumps(self._definition)

    def _add_wtforms_field(self, FormClass, field):
        field_name = field.get("name")
        if not hasattr(FormClass, field_name):
            # field_definition = self._wtforms_field_definition(field)
            field_definition = FormulaicField.make_wtforms_field(field, self._wtforms_map, self._function_map)
            setattr(FormClass, field_name, field_definition)


class FormulaicFieldset(object):
    def __init__(self, definition, wtforms_map, function_map):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map

    def fields(self):
        return [FormulaicField(f, self._wtforms_map, self._function_map) for f in
                self._definition.get("fields", [])]

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if name in self._definition:
            return self._definition[name]

        raise AttributeError('{name} is not set'.format(name=name))


class FormulaicField(object):
    def __init__(self, definition, wtforms_map, function_map):
        self._definition = definition
        self._wtforms_map = wtforms_map
        self._function_map = function_map
        self._wtform_field = None
        self._wtforms_field_bound = None

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
                return [FormulaicField(sfs, self._wtforms_map, self._function_map) for sfs in
                        option.get("subfields", [])]

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

    def render_form_control(self):
        kwargs = deepcopy(self._definition.get("attr", {}))
        if "placeholder" in self._definition.get("help", {}):
            kwargs["placeholder"] = self._definition["help"]["placeholder"]

        if self.has_validator("required"):
            kwargs["required"] = ""

        if self.has_subfields():
            kwargs["formulaic"] = self

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
            kwargs["choices"] = cls._options2choices(field["options"], function_map)

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
