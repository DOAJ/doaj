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
from portality.formcontext.fields import TagListField
import inspect
from portality.lib import plugin


class NumberWidget(widgets.Input):
    input_type = 'number'


def makeListWidget(prefix_label):
    def lw():
        return widgets.ListWidget(prefix_label=prefix_label)
    return lw


WTFORMS_MAP = [
    {
        "match" : {"input" : "radio"},
        "wtforms" : {"class" : RadioField}
    },
    {
        "match" : {"input" : "checkbox", "options" : True},
        "wtforms" : {"class" : SelectMultipleField, "init" : {"option_widget" : widgets.CheckboxInput, "widget" : makeListWidget(prefix_label=False)}}
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
            context_overrides = field_def.get("context", {}).get(context_name)
            if context_overrides is not None:
                for k, v in context_overrides.items():
                    field_def[k] = v

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

    def _add_wtforms_field(self, FormClass, field):
        field_name = field.get("name")
        if not hasattr(FormClass, field_name):
            field_definition = self._wtforms_field_definition(field)
            setattr(FormClass, field_name, field_definition)

    def _wtforms_field_definition(self, field):
        result = self._get_wtforms_map(field)
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
            kwargs["choices"] = self._options2choices(field["options"])

        return klazz(**kwargs)

    def _get_wtforms_map(self, field):
        input = field.get("input")
        options = "options" in field
        datatype = field.get("datatype")

        for possible in self._wtforms_map:
            match = possible.get("match")
            input_match = "input" not in match or match.get("input") == input
            options_match = "options" not in match or match.get("options", False) == options
            datatype_match = "datatype" not in match or match.get("datatype") == datatype

            if input_match and options_match and datatype_match:
                return possible.get("wtforms")

        return None

    def _options2choices(self, options):
        if isinstance(options, str): # it's a function reference
            fnpath = self._function_map.get(options)
            if fnpath is None:
                raise FormulaicException("No function mapping defined for function reference '{x}'".format(x=options))
            fn = plugin.load_function(fnpath)
            options = fn()

            # options = []

        choices = []
        for o in options:
            display = o.get("display")
            value = o.get("value")
            if value is None:
                value = o.get("display")
            choices.append((value, display))

        return choices



