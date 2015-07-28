from portality.lib import dates
from copy import deepcopy
import locale, json

#########################################################
## Data coerce functions

def to_unicode():
    def to_utf8_unicode(val):
        if val is None:
            return None

        if isinstance(val, unicode):
            return val
        elif isinstance(val, basestring):
            try:
                return val.decode("utf8", "strict")
            except UnicodeDecodeError:
                raise ValueError(u"Could not decode string")
        else:
            return unicode(val)

    return to_utf8_unicode

def to_int():
    def intify(val):
        if val is None:
            return None

        # strip any characters that are outside the ascii range - they won't make up the int anyway
        # and this will get rid of things like strange currency marks
        if isinstance(val, unicode):
            val = val.encode("ascii", errors="ignore")

        # try the straight cast
        try:
            return int(val)
        except ValueError:
            pass

        # could have commas in it, so try stripping them
        try:
            return int(val.replace(",", ""))
        except ValueError:
            pass

        # try the locale-specific approach
        try:
            return locale.atoi(val)
        except ValueError:
            pass

        raise ValueError(u"Could not convert string to int: {x}".format(x=val))

    return intify

def to_float():
    def floatify(val):
        if val is None:
            return None

        # strip any characters that are outside the ascii range - they won't make up the float anyway
        # and this will get rid of things like strange currency marks
        if isinstance(val, unicode):
            val = val.encode("ascii", errors="ignore")

        # try the straight cast
        try:
            return float(val)
        except ValueError:
            pass

        # could have commas in it, so try stripping them
        try:
            return float(val.replace(",", ""))
        except ValueError:
            pass

        # try the locale-specific approach
        try:
            return locale.atof(val)
        except ValueError:
            pass

        raise ValueError(u"Could not convert string to float: {x}".format(x=val))

    return floatify

def date_str(in_format=None, out_format=None):
    def datify(val):
        if val is None:
            return None
        return dates.reformat(val, in_format=in_format, out_format=out_format)

    return datify

def to_datestamp(in_format=None):
    def stampify(val):
        if val is None:
            return None
        return dates.parse(val, format=in_format)

    return stampify

def to_isolang(output_format=None):
    """
    :param output_format: format from input source to putput.  Must be one of:
        * alpha3
        * alt3
        * alpha2
        * name
        * fr
    Can be a list in order of preference, too
    :return:
    """
    # delayed import, since we may not always want to load the whole dataset for a dataobj
    from portality.lib import isolang as dataset

    # sort out the output format list
    if output_format is None:
        output_format = ["alpha3"]
    if not isinstance(output_format, list):
        output_format = [output_format]

    def isolang(val):
        if val is None:
            return None
        l = dataset.find(val)
        for f in output_format:
            v = l.get(f)
            if v is None or v == "":
                continue
            return v

    return isolang

def to_url(val):
    if val is None:
        return None
    # FIXME: implement
    return val

def to_bool():
    def boolify(val):
        """Conservative boolean cast - don't cast lists and objects to True, just existing booleans and strings."""
        if val is None:
            return None
        if val is True or val is False:
            return val

        if isinstance(val, basestring):
            if val.lower() == 'true':
                return True
            elif val.lower() == 'false':
                return False
            raise ValueError(u"Could not convert string {val} to boolean. Expecting string to either say 'true' or 'false' (not case-sensitive).".format(val=val))

        raise ValueError(u"Could not convert {val} to boolean. Expect either boolean or string.".format(val=val))

    return boolify

############################################################

############################################################
## The core data object which manages all the interactions
## with the underlying data member variable

class DataSchemaException(Exception):
    pass

class DataObj(object):
    """
    Class which provides services to other classes which store their internal data
    as a python data structure in the self.data field.
    """

    DEFAULT_COERCE = {
        "unicode": to_unicode(),
        "utcdatetime": date_str(),
        "integer": to_int(),
        "float": to_float(),
        "isolang": to_isolang(),
        "url": to_url,
        "bool": to_bool()
    }

    def __init__(self, raw=None, struct=None, type=None, drop_extra_fields=False):
        assert isinstance(raw, dict), "The raw data passed in must be iteratable as a dict."
        # if no subclass has set a type and none is passed in, error
        if not hasattr(self, 'type'):
            if not type:
                raise ValueError("Can't create DataObj without a type")
            self.type = type

        # if no subclass has set the coerce, then set it from default
        if not hasattr(self, "coerce"):
            self.coerce = deepcopy(self.DEFAULT_COERCE)

        # if no subclass has set the struct, use the one passed in
        if not hasattr(self, "struct"):
            # if no struct has been passed in, initialise to empty
            if struct:
                self.struct = struct
            else:
                self.struct = {}

        for k, v in raw.iteritems():
            setattr(self, k, v)

        # restructure the object based on the struct if required
        # ET note to self and not isinstance(self.data, DataObj) ?
        # if self.struct is not None:
        #     self.data = self.construct(self.data, self.struct, self.coerce, drop_extra_fields=drop_extra_fields)

    def __getattr__(self, name):
        # If this attribute is not already set in the internal data
        # but it's supposed to be an object (not primitive type)
        # then set it to an empty DataObj with the struct it's
        # supposed to have. That way if the caller is chaining
        # a setter to [name] we'll keep a pointer to the right object.
        # E.g. the caller does:
        # j = JournalDO()
        # j.bibjson.title = 'atitle'
        # This function will be called with name == "bibjson".
        # If we didn't keep track of an empty bibjson object,
        # the .title would be set on an object we would no longer have
        # a handle on.

        # attrs used in creating a DataObj should behave as they usually
        # would in Python
        if name in ['data', 'struct', 'coerce', 'type']:
            return object.__getattribute__(self, name)

        #TODO rework to work with lists! Now they are just wrapped in dataobjects, where that should be lists of dataobjects I guess

        if not self.data.get(name):
        # the requested attribute is not present in the data already
            if name in self.struct.get('structs', {}):
                self.data[name] = DataObj(struct=self.struct['structs'][name], type=name)
            elif name in self.struct.get('fields', {}):
            # it's a primitive field that isn't set
                try:
                    return self.coerce[self.struct['fields'][name]['coerce']](None)
                except ValueError:
                    raise AttributeError('{name} is not set'.format(name=name))
            else:
            # it's not a valid attribute of this object
                raise AttributeError('{name} is not an attribute of {type}'.format(name=name, type=self.type))

        # the requested attribute is in the internal data
        if name in self.struct.get('structs', {}) and not isinstance(self.data[name], DataObj):
            self.data[name] = DataObj(raw=self.data[name], struct=self.struct['structs'][name], type=name)
            # return self.data[name] wrapped in a DataObj with type=name, struct set to self.struct['structs'][name]

        return self.data[name]

    def __setattr__(self, name, value):
        # If what we're trying to set is an object itself,
        # pass it on to its own DataObj.
        # If it's a primitive, coerce it into the defined type.
        # If what we're trying to set is not in the struct, bail.

        # attrs used in creating a DataObj should behave as they usually
        # would in Python
        if name in ['data', 'struct', 'coerce', 'type']:
            return object.__setattr__(self, name, value)

        #TODO rework to work with lists! Now they are just wrapped in dataobjects, where that should be lists of dataobjects I guess

        if name in self.struct.get('structs', {}):
            self.data[name] = DataObj(struct=self.struct['structs'][name], type=name, raw=value)
        elif name in self.struct.get('fields', {}):
            self.data[name] = self.coerce[self.struct['fields'][name]['coerce']](value)
        else:
        # not an allowed attribute
            raise AttributeError('{name} is not an attribute of {type}'.format(name=name, type=self.type))

    @classmethod
    def construct(cls, obj, struct, coerce, context="", drop_extra_fields=False):
        """
        {
            "fields" : {
                "field_name" : {"coerce" :"coerce_function"}

            },
            "objects" : [
                "field_name"
            ],
            "lists" : {
                "field_name" : {"contains" : "object|list|field", "coerce" : "field_coerce_function}
            },
            "reqired" : ["field_name"],
            "structs" : {
                "field_name" : {
                    <construct>
                }
            }
        }

        :param obj:
        :param struct:
        :param coerce:
        :param drop_extra_fields:
        :return:
        """
        if obj is None:
            return None

        # check that all the required fields are there
        keys = obj.keys()
        for r in struct.get("required", []):
            if r not in keys:
                c = context if context != "" else "root"
                raise DataStructureException("Field '{r}' is required but not present at '{c}'".format(r=r, c=c))

        # check that there are no fields that are not allowed if we don't want to drop anything silently
        if not drop_extra_fields:
            allowed = struct.get("fields", {}).keys() + struct.get("objects", []) + struct.get("lists", {}).keys()
            for k in keys:
                if k not in allowed:
                    c = context if context != "" else "root"
                    raise DataStructureException("Field '{k}' is not permitted at '{c}'".format(k=k, c=c))

        # this is the new object we'll be creating from the old
        constructed = {}

        # now check all the fields
        for field_name, instructions in struct.get("fields", {}).iteritems():
            val = obj.get(field_name)
            if val is None:
                continue
            coerce_fn = coerce.get(instructions.get("coerce", "unicode"))
            if coerce_fn is None:
                raise DataStructureException("No coercion function defined for type '{x}' at '{c}'".format(x=instructions.get("coerce", "unicode"), c=context + field_name))

            try:
                constructed[field_name] = coerce_fn(val)
            except ValueError as e:
                raise DataStructureException("Unable to coerce '{v}' to '{fn}' at '{c}'".format(v=val, fn=instructions.get("coerce", "unicode"), c=context + field_name))

        # next check all the objects (which will involve a recursive call to this function
        for field_name in struct.get("objects", []):
            val = obj.get(field_name)
            if val is None:
                continue
            if type(val) != dict:
                raise DataStructureException("Found '{x}' = '{y}' but expected object/dict".format(x=context + field_name, y=val))

            instructions = struct.get("structs", {}).get(field_name)
            if instructions is None:
                constructed[field_name] = deepcopy(val)
            else:
                constructed[field_name] = cls.construct(val, instructions, coerce=coerce, context=context + field_name + ".", drop_extra_fields=drop_extra_fields)

        # now check all the lists
        for field_name, instructions in struct.get("lists", {}).iteritems():
            vals = obj.get(field_name)
            if vals is None:
                continue

            nvals = []
            contains = instructions.get("contains")
            if contains == "field":
                # coerce all the values in the list
                coerce_fn = coerce.get(instructions.get("coerce", "unicode"))
                if coerce_fn is None:
                    raise DataStructureException("No coercion function defined for type '{x}' at '{c}'".format(x=instructions.get("coerce", "unicode"), c=context + field_name))

                for i in xrange(len(vals)):
                    val = vals[i]
                    try:
                        nvals.append(coerce_fn(val))
                    except ValueError as e:
                        raise DataStructureException("Unable to coerce '{v}' to '{fn}' at '{c}' position '{p}'".format(v=val, fn=instructions.get("coerce", "unicode"), c=context + field_name, p=i))

            elif contains == "object":
                # for each object in the list, send it for construction
                for i in range(len(vals)):
                    val = vals[i]

                    if type(val) != dict:
                        raise DataStructureException("Found '{x}[{p}]' = '{y}' but expected object/dict".format(x=context + field_name, y=val, p=i))

                    subinst = struct.get("struct", {}).get(field_name)
                    if subinst is None:
                        nvals.append(deepcopy(val))
                    else:
                        nvals.append(cls.construct(val, subinst, coerce=coerce, context=context + field_name + "[" + str(i) + "].", drop_extra_fields=drop_extra_fields))

            else:
                extra_info = ''
                if contains is None:
                    extra_info += " Perhaps the struct entry for list '{x}' is missing a 'contains' key?"
                raise DataStructureException(("Cannot understand structure where list '{x}' elements contain '{y}'." + extra_info).format(x=context + field_name, y=contains))

            constructed[field_name] = nvals

        return constructed



    ### Old methods from JPER

    def populate(self, fields_and_values):
        for k, v in fields_and_values.iteritems():
            setattr(self, k, v)

    def clone(self):
        return self.__class__(deepcopy(self.data))

    def json(self):
        return json.dumps(self.data)

    def _add_struct(self, struct):
        if hasattr(self, "struct"):
            self.struct = construct_merge(self.struct, struct)
        else:
            self.struct = struct

    def _get_path(self, path, default):
        parts = path.split(".")
        context = self.data

        for i in range(len(parts)):
            p = parts[i]
            d = {} if i < len(parts) - 1 else default
            context = context.get(p, d)
        return context

    def _set_path(self, path, val):
        parts = path.split(".")
        context = self.data

        for i in range(len(parts)):
            p = parts[i]

            if p not in context and i < len(parts) - 1:
                context[p] = {}
                context = context[p]
            elif p in context and i < len(parts) - 1:
                context = context[p]
            else:
                context[p] = val

    def _delete_from_list(self, path, val=None, matchsub=None, prune=True):
        l = self._get_list(path)

        removes = []
        i = 0
        for entry in l:
            if val is not None:
                if entry == val:
                    removes.append(i)
            elif matchsub is not None:
                matches = 0
                for k, v in matchsub.iteritems():
                    if entry.get(k) == v:
                        matches += 1
                if matches == len(matchsub.keys()):
                    removes.append(i)
            i += 1

        removes.sort(reverse=True)
        for r in removes:
            del l[r]

        if len(l) == 0 and prune:
            self._delete(path, prune)

    def _delete(self, path, prune=True):
        parts = path.split(".")
        context = self.data

        stack = []
        for i in range(len(parts)):
            p = parts[i]
            if p in context:
                if i < len(parts) - 1:
                    stack.append(context[p])
                    context = context[p]
                else:
                    del context[p]
                    if prune and len(stack) > 0:
                        stack.pop() # the last element was just deleted
                        self._prune_stack(stack)

    def _prune_stack(self, stack):
        while len(stack) > 0:
            context = stack.pop()
            todelete = []
            for k, v in context.iteritems():
                if isinstance(v, dict) and len(v.keys()) == 0:
                    todelete.append(k)
            for d in todelete:
                del context[d]

    def _coerce(self, val, cast, accept_failure=False):
        if cast is None:
            return val
        try:
            return cast(val)
        except (ValueError, TypeError):
            if accept_failure:
                return val
            raise DataSchemaException(u"Cast with {x} failed on {y}".format(x=cast, y=val))

    def _get_single(self, path, coerce=None, default=None, allow_coerce_failure=True):
        # get the value at the point in the object
        val = self._get_path(path, default)

        if coerce is not None and val is not None:
            # if you want to coerce and there is something to coerce do it
            return self._coerce(val, coerce, accept_failure=allow_coerce_failure)
        else:
            # otherwise return the value
            return val

    def _get_list(self, path, coerce=None, by_reference=True, allow_coerce_failure=True):
        # get the value at the point in the object
        val = self._get_path(path, None)

        # if there is no value and we want to do by reference, then create it, bind it and return it
        if val is None and by_reference:
            mylist = []
            self._set_single(path, mylist)
            return mylist

        # otherwise, default is an empty list
        elif val is None and not by_reference:
            return []

        # check that the val is actually a list
        if not isinstance(val, list):
            raise DataSchemaException(u"Expecting a list at {x} but found {y}".format(x=path, y=val))

        # if there is a value, do we want to coerce each of them
        if coerce is not None:
            coerced = [self._coerce(v, coerce, accept_failure=allow_coerce_failure) for v in val]
            if by_reference:
                self._set_single(path, coerced)
            return coerced
        else:
            if by_reference:
                return val
            else:
                return deepcopy(val)

    def _set_single(self, path, val, coerce=None, allow_coerce_failure=False, allowed_values=None, allowed_range=None,
                    allow_none=True, ignore_none=False):

        if val is None and ignore_none:
            return

        if val is None and not allow_none:
            raise DataSchemaException(u"NoneType is not allowed at {x}".format(x=path))

        # first see if we need to coerce the value (and don't coerce None)
        if coerce is not None and val is not None:
            val = self._coerce(val, coerce, accept_failure=allow_coerce_failure)

        if allowed_values is not None and val not in allowed_values:
            raise DataSchemaException(u"Value {x} is not permitted at {y}".format(x=val, y=path))

        if allowed_range is not None:
            lower, upper = allowed_range
            if (lower is not None and val < lower) or (upper is not None and val > upper):
                raise DataSchemaException("Value {x} is outside the allowed range: {l} - {u}".format(x=val, l=lower, u=upper))

        # now set it at the path point in the object
        self._set_path(path, val)

    def _set_list(self, path, val, coerce=None, allow_coerce_failure=False, allow_none=True, ignore_none=False):
        # first ensure that the value is a list
        if not isinstance(val, list):
            val = [val]

        # now carry out the None check
        # for each supplied value, if it is none, and none is not allowed, raise an error if we do not
        # plan to ignore the nones.
        for v in val:
            if v is None and not allow_none:
                if not ignore_none:
                    raise DataSchemaException(u"NoneType is not allowed at {x}".format(x=path))

        # now coerce each of the values, stripping out Nones if necessary
        val = [self._coerce(v, coerce, accept_failure=allow_coerce_failure) for v in val if v is not None or not ignore_none]

        # check that the cleaned array isn't empty, and if it is behave appropriately
        if len(val) == 0:
            # this is equivalent to a None, so we need to decide what to do
            if ignore_none:
                # if we are ignoring nones, just do nothing
                return
            elif not allow_none:
                # if we are not ignoring nones, and not allowing them, raise an error
                raise DataSchemaException(u"Empty array not permitted at {x}".format(x=path))

        # now set it on the path
        self._set_path(path, val)

    def _add_to_list(self, path, val, coerce=None, allow_coerce_failure=False, allow_none=False, ignore_none=True, unique=False):
        if val is None and ignore_none:
            return

        if val is None and not allow_none:
            raise DataSchemaException(u"NoneType is not allowed in list at {x}".format(x=path))

        # first coerce the value
        if coerce is not None:
            val = self._coerce(val, coerce, accept_failure=allow_coerce_failure)
        current = self._get_list(path, by_reference=True)

        # if we require the list to be unique, check for the value first
        if unique:
            if val in current:
                return

        # otherwise, append
        current.append(val)    

############################################################
## Data structure coercion

class DataStructureException(Exception):
    pass


def construct_merge(target, source):
    merged = deepcopy(target)

    for field, instructions in source.get("fields", {}).iteritems():
        if "fields" not in merged:
            merged["fields"] = {}
        if field not in merged["fields"]:
            merged["fields"][field] = deepcopy(instructions)

    for obj in source.get("objects", []):
        if "objects" not in merged:
            merged["objects"] = []
        if obj not in merged["objects"]:
            merged["objects"].append(obj)

    for field, instructions in source.get("lists", {}).iteritems():
        if "lists" not in merged:
            merged["lists"] = {}
        if field not in merged["lists"]:
            merged["lists"][field] = deepcopy(instructions)

    for r in source.get("required", []):
        if "required" not in merged:
            merged["required"] = []
        if r not in merged["required"]:
            merged["required"].append(r)

    for field, struct in source.get("structs", {}).iteritems():
        if "structs" not in merged:
            merged["structs"] = {}
        if field not in merged["structs"]:
            merged["structs"][field] = deepcopy(struct)

    return merged


############################################################
## Unit test support

def test_dataobj(obj, fields_and_values):
    """
    Test a dataobj to make sure that the getters and setters you have specified
    are working correctly.

    Provide it a data object and a list of fields with the values to set and the expected return values (if required):

    {
        "key" : ("set value", "get value")
    }

    If you provide only the set value, then the get value will be required to be the same as the set value in the test

    {
        "key" : "set value"
    }

    :param obj:
    :param fields_and_values:
    :return:
    """
    for k, valtup in fields_and_values.iteritems():
        if not isinstance(valtup, tuple):
            valtup = (valtup,)
        set_val = valtup[0]
        try:
            setattr(obj, k, set_val)
        except AttributeError:
            assert False, u"Unable to set attribute {x} with value {y}".format(x=k, y=set_val)

    for k, valtup in fields_and_values.iteritems():
        if not isinstance(valtup, tuple):
            valtup = (valtup,)
        get_val = valtup[0]
        if len(valtup) > 1:
            get_val = valtup[1]
        val = getattr(obj, k)
        assert val == get_val, ("Problem get-ting attribute", k, val, get_val)