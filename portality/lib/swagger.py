from copy import deepcopy
from .dataobj import DataSchemaException

class SwaggerSupport(object):
    # Translation between our simple field types and swagger spec types.
    # For all the ones that have a note to add support to the swagger-ui front-end,
    # for now those fields will just display whatever is in the "type"
    # section when viewing the interactive documentation. "type" must be
    # a valid Swagger type ( https://github.com/swagger-api/swagger-spec/blob/master/versions/2.0.md#data-types )
    # and "format" will just be ignored if it is not a default format in
    # the Swagger spec *and* a format that the swagger-ui Javascript library understands.
    # The spec says it's possible to define your own formats - we'll see.
    DEFAULT_SWAGGER_TRANS = {
        # The default translation from our coerce to swagger is {"type": "string"}
        # if there is no matching entry in the trans dict here.
        "unicode": {"type": "string"},
        "utcdatetime": {"type": "string", "format": "date-time"},
        "integer": {"type": "integer"},
        "bool": {"type": "boolean"},
        "float": {"type": "float"},
        "isolang": {"type": "string", "format": "isolang"},  # TODO extend swagger-ui with isolang format support and let it produce example values etc. on the front-end
        "url": {"type": "string", "format": "url"},  # TODO add suppport to swagger-ui doc frontend for URL or grab from somewhere we can't be the first!
        "isolang_2letter": {"type": "string", "format": "isolang-alpha2"},  # TODO add support to swagger-ui front for this
        "country_code": {"type": "string", "format": "country_code"},  # TODO add support to swagger-ui front for this
        "currency_code": {"type": "string", "format": "currency_code"},  # TODO add support to swagger-ui front for this
        "license": {"type": "string", "format": "license_type"},  # TODO add support to swagger-ui front for this. Ideal if we could display the list of allowed values from the coerce map.
        "persistent_identifier_scheme": {"type": "string", "format": "persistent_identifier_scheme"},  # TODO add support to swagger-ui front for this. Ideal if we could display the list of allowed values from the coerce map.
        "format": {"type": "string", "format": "format"},  # TODO add support to swagger-ui front for this. Ideal if we could display the list of allowed values from the coerce map.
        "deposit_policy": {"type": "string", "format": "deposit_policy"},  # TODO add support to swagger-ui front for this. Ideal if we could display the list of allowed values from the coerce map.
    }

    def __init__(self, swagger_trans=None, *args, **kwargs):
        # make a shortcut to the object.__getattribute__ function
        og = object.__getattribute__

        # if no subclass has set the swagger translation dict, then set it from default
        try:
            og(self, "_swagger_trans")
        except:
            self._swagger_trans = swagger_trans if swagger_trans is not None else deepcopy(self.DEFAULT_SWAGGER_TRANS)

        # super(SwaggerSupport, self).__init__(*args, **kwargs) # UT fails with args and kwargs - takes only one argument, object to initialize
        super(SwaggerSupport, self).__init__()

    def struct_to_swag(self, struct=None, schema_title='', **kwargs):
        if not struct:
            if not self._struct:
                raise DataSchemaException("No struct to translate to Swagger.")
            struct = self._struct

        swag = {
            "properties": self.__struct_to_swag_properties(struct=struct, **kwargs),
            "required": deepcopy(struct.get('required', []))
        }
        if schema_title:
            swag['title'] = schema_title

        return swag

    def __struct_to_swag_properties(self, struct=None, path=''):
        '''A recursive function to translate the current DataObject's struct to Swagger Spec.'''
        # If no struct is specified this is the first call, so set the
        # operating struct to the entire current DO struct.

        if not isinstance(struct, dict):
            raise DataSchemaException("The struct whose properties we're translating to Swagger should always be a dict-like object.")

        swag_properties = {}

        # convert simple fields
        for simple_field, instructions in iter(struct.get('fields', {}).items()):
            # no point adding to the path here, it's not gonna recurse any further from this field
            swag_properties[simple_field] = self._swagger_trans.get(instructions['coerce'], {"type": "string"})

        # convert objects
        for obj in struct.get('objects', []):
            newpath = obj if not path else path + '.' + obj
            instructions = struct.get('structs', {}).get(obj, {})

            swag_properties[obj] = {}
            swag_properties[obj]['title'] = newpath
            swag_properties[obj]['type'] = 'object'
            swag_properties[obj]['properties'] = self.__struct_to_swag_properties(struct=instructions, path=newpath)  # recursive call, process sub-struct(s)
            swag_properties[obj]['required'] = deepcopy(instructions.get('required', []))

        # convert lists
        for l, instructions in iter(struct.get('lists', {}).items()):
            newpath = l if not path else path + '.' + l

            swag_properties[l] = {}
            swag_properties[l]['type'] = 'array'
            swag_properties[l]['items'] = {}
            if instructions['contains'] == 'field':
                swag_properties[l]['items'] = self._swagger_trans.get(instructions['coerce'], {"type": "string"})
            elif instructions['contains'] == 'object':
                swag_properties[l]['items']['type'] = 'object'
                swag_properties[l]['items']['title'] = newpath
                swag_properties[l]['items']['properties'] = self.__struct_to_swag_properties(struct=struct.get('structs', {}).get(l, {}), path=newpath)  # recursive call, process sub-struct(s)
                swag_properties[l]['items']['required'] = deepcopy(struct.get('structs', {}).get(l, {}).get('required', []))
            else:
                raise DataSchemaException("Instructions for list {x} unclear. Conversion to Swagger Spec only supports lists containing \"field\" and \"object\" items.".format(x=newpath))

        return swag_properties
