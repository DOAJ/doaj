import locale
from urllib.parse import urlparse
from copy import deepcopy
from datetime import datetime

###############################################
## Common coerce functions
###############################################

def to_utf8_unicode(val):
    if isinstance(val, str):
        return val
    elif isinstance(val, str):
        try:
            return val.decode("utf8", "strict")
        except UnicodeDecodeError:
            raise ValueError("Could not decode string")
    else:
        return str(val)


def to_unicode_upper(val):
    val = to_utf8_unicode(val)
    return val.upper()


def to_unicode_lower(val):
    val = to_utf8_unicode(val)
    return val.lower()


def intify(val):
    # strip any characters that are outside the ascii range - they won't make up the int anyway
    # and this will get rid of things like strange currency marks
    if isinstance(val, str):
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

    raise ValueError("Could not convert string to int: {x}".format(x=val))

def floatify(val):
    # strip any characters that are outside the ascii range - they won't make up the float anyway
    # and this will get rid of things like strange currency marks
    if isinstance(val, str):
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

    raise ValueError("Could not convert string to float: {x}".format(x=val))


def to_url(val):
    if not isinstance(val, str):
        raise ValueError("Argument passed to to_url was not a string, but type '{t}': '{val}'".format(t=type(val),val=val))

    val = val.strip()

    if val == '':
        return val

    # parse with urlparse
    url = urlparse(val)

    # now check the url has the minimum properties that we require
    if url.scheme and url.scheme.startswith("http"):
        return to_utf8_unicode(val)
    else:
        raise ValueError("Could not convert string {val} to viable URL".format(val=val))


def to_bool(val):
    """Conservative boolean cast - don't cast lists and objects to True, just existing booleans and strings."""
    if val is None:
        return None
    if val is True or val is False:
        return val

    if isinstance(val, str):
        if val.lower() == 'true':
            return True
        elif val.lower() == 'false':
            return False
        raise ValueError("Could not convert string {val} to boolean. Expecting string to either say 'true' or 'false' (not case-sensitive).".format(val=val))

    raise ValueError("Could not convert {val} to boolean. Expect either boolean or string.".format(val=val))


def to_datetime(val):
    try:
        datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
        return val
    except:
        raise ValueError("Could not convert string {val} to UTC Datetime".format(val=val))


def string_canonicalise(canon, allow_fail=False):
    normalised = {}
    for a in canon:
        normalised[a.strip().lower()] = a

    def sn(val):
        if val is None:
            if allow_fail:
                return None
            raise ValueError("NoneType not permitted")

        try:
            norm = val.strip().lower()
        except:
            raise ValueError("Unable to treat value as a string")

        uc = to_utf8_unicode
        if norm in normalised:
            return uc(normalised[norm])
        if allow_fail:
            return uc(val)

        raise ValueError("Unable to canonicalise string")

    return sn


class SeamlessException(Exception):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(SeamlessException, self).__init__(message, *args, **kwargs)


class SeamlessMixin(object):

    __SEAMLESS_STRUCT__ = None

    __SEAMLESS_COERCE__ = {
        "unicode": to_utf8_unicode,
        "unicode_upper" : to_unicode_upper,
        "unicode_lower" : to_unicode_lower,
        "integer": intify,
        "float": floatify,
        "url": to_url,
        "bool": to_bool,
        "datetime" : to_datetime
    }

    __SEAMLESS_DEFAULT_COERCE__ = "unicode"

    __SEAMLESS_PROPERTIES__ = None

    __SEAMLESS_APPLY_STRUCT_ON_INIT__ = True
    __SEAMLESS_CHECK_REQUIRED_ON_INIT__ = True
    __SEAMLESS_SILENT_PRUNE__ = False
    __SEAMLESS_ALLOW_OTHER_FIELDS__ = False

    def __init__(self,
                    raw=None,    # The raw data
                    struct=None,
                    coerce=None,
                    properties=None,
                    default_coerce=None,
                    apply_struct_on_init=None,
                    check_required_on_init=None,
                    silent_prune=None,
                    allow_other_fields=None,
                    *args, **kwargs
                 ):

        # set all the working properties
        self.__seamless_coerce__ = coerce if coerce is not None else self.__SEAMLESS_COERCE__
        self.__seamless_default_coerce__ = default_coerce if default_coerce is not None else self.__SEAMLESS_DEFAULT_COERCE__
        self.__seamless_properties__ = properties if properties is not None else self.__SEAMLESS_PROPERTIES__
        self.__seamless_apply_struct_on_init__ = apply_struct_on_init if apply_struct_on_init is not None else self.__SEAMLESS_APPLY_STRUCT_ON_INIT__
        self.__seamless_check_required_on_init__ = check_required_on_init if check_required_on_init is not None else self.__SEAMLESS_CHECK_REQUIRED_ON_INIT__
        self.__seamless_silent_prune__ = silent_prune if silent_prune is not None else self.__SEAMLESS_SILENT_PRUNE__
        self.__seamless_allow_other_fields__ = allow_other_fields if allow_other_fields is not None else self.__SEAMLESS_ALLOW_OTHER_FIELDS__

        struct = struct if struct is not None else self.__SEAMLESS_STRUCT__
        if isinstance(struct, list):
            struct = Construct.merge(*struct)
        self.__seamless_struct__ = Construct(struct,
                                              self.__seamless_coerce__,
                                              self.__seamless_default_coerce__)

        self.__seamless__ = SeamlessData(raw, struct=self.__seamless_struct__)

        if (self.__seamless_struct__ is not None and
                raw is not None and
                self.__seamless_apply_struct_on_init__):
            self.__seamless__ = self.__seamless_struct__.construct(self.__seamless__.data,
                                    check_required=self.__seamless_check_required_on_init__,
                                    silent_prune=self.__seamless_silent_prune__,
                                    allow_other_fields=self.__seamless_allow_other_fields__)

        self.custom_validate()

        super(SeamlessMixin, self).__init__(*args, **kwargs)

    def __getattr__(self, name):

        # workaround to prevent debugger from disconnecting at the deepcopy method
        # https://stackoverflow.com/questions/32831050/pycharms-debugger-gives-up-when-hitting-copy-deepcopy
        # if name.startswith("__"):
        #    raise AttributeError

        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)

        if self.__seamless_properties__ is not None:
            prop = self.__seamless_properties__.get(name)
            if prop is not None:
                path = prop["path"]
                wrap = prop.get("wrapper")
                return self.__seamless__.get_property(path, wrap)

        raise AttributeError('{name} is not set'.format(name=name))

    def __setattr__(self, name, value, allow_coerce_failure=False):
        if hasattr(self.__class__, name):
            return object.__setattr__(self, name, value)

        if name.startswith("__seamless"):
            return object.__setattr__(self, name, value)

        if self.__seamless_properties__ is not None:
            prop = self.__seamless_properties__.get(name)
            if prop is not None:
                path = prop["path"]
                unwrap = prop.get("unwrapper")
                wasset = self.__seamless__.set_property(path, value, unwrap, allow_coerce_failure)
                if wasset:
                    return

        # fall back to the default approach of allowing any attribute to be set on the object
        return object.__setattr__(self, name, value)

    def __deepcopy__(self):
        # FIXME: should also reflect all the constructor arguments
        return self.__class__(deepcopy(self.__seamless__.data))

    def custom_validate(self):
        """
            Should be implemented on the higher level
        """
        pass

    def verify_against_struct(self, check_required=True, silent_prune=None, allow_other_fields=None):

        silent_prune = silent_prune if silent_prune is not None else self.__seamless_silent_prune__
        allow_other_fields = allow_other_fields if allow_other_fields is not None else self.__seamless_allow_other_fields__

        if (self.__seamless_struct__ is not None and
                self.__seamless__ is not None):
            self.__seamless_struct__.construct(deepcopy(self.__seamless__.data),    # use a copy of the data, to avoid messing with any references to the current data
                check_required=check_required,
                silent_prune=silent_prune,
                allow_other_fields=allow_other_fields)

    def apply_struct(self, check_required=True, silent_prune=None, allow_other_fields=None):

        silent_prune = silent_prune if silent_prune is not None else self.__seamless_silent_prune__
        allow_other_fields = allow_other_fields if allow_other_fields is not None else self.__seamless_allow_other_fields__

        if (self.__seamless_struct__ is not None and
                self.__seamless__ is not None):
            self.__seamless__ = self.__seamless_struct__.construct(self.__seamless__.data,
                check_required=check_required,
                silent_prune=silent_prune,
                allow_other_fields=allow_other_fields)

    def extend_struct(self, struct):
        self.__seamless_struct__ = Construct.merge(self.__seamless_struct__, struct)


class SeamlessData(object):
    def __init__(self, raw=None, struct=None):
        self.data = raw if raw is not None else {}
        self._struct = struct

    def get_single(self, path, coerce=None, default=None, allow_coerce_failure=True):
        # get the value at the point in the object
        val = self._get_path(path, default)

        if coerce is not None and val is not None:
            # if you want to coerce and there is something to coerce do it
            try:
                return self._coerce(val, coerce, accept_failure=allow_coerce_failure)
            except SeamlessException as e:
                e.message += "; get_single, path {x}".format(x=path)
                raise
        else:
            # otherwise return the value
            return val

    def set_single(self, path, val, coerce=None, allow_coerce_failure=False, allowed_values=None, allowed_range=None,
                    allow_none=True, ignore_none=False, context=""):

        if val is None and ignore_none:
            return

        if val is None and not allow_none:
            raise SeamlessException("NoneType is not allowed at '{x}'".format(x=context + "." + path))

        # first see if we need to coerce the value (and don't coerce None)
        if coerce is not None and val is not None:
            try:
                val = self._coerce(val, coerce, accept_failure=allow_coerce_failure)
            except SeamlessException as e:
                e.message += "; set_single, path {x}".format(x=context + "." + path)
                raise

        if allowed_values is not None and val not in allowed_values:
            raise SeamlessException("Value '{x}' is not permitted at '{y}'".format(x=val, y=context + "." + path))

        if allowed_range is not None:
            lower, upper = allowed_range
            if (lower is not None and val < lower) or (upper is not None and val > upper):
                raise SeamlessException("Value '{x}' is outside the allowed range: {l} - {u} at '{y}'".format(x=val, l=lower, u=upper, y=context + "." + path))

        # now set it at the path point in the object
        self._set_path(path, val)

    def delete(self, path, prune=True):
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

    def get_list(self, path, coerce=None, by_reference=True, allow_coerce_failure=True, context=""):
        # get the value at the point in the object
        val = self._get_path(path, None)

        # if there is no value and we want to do by reference, then create it, bind it and return it
        if val is None and by_reference:
            mylist = []
            self.set_single(path, mylist)
            return mylist

        # otherwise, default is an empty list
        elif val is None and not by_reference:
            return []

        # check that the val is actually a list
        if not isinstance(val, list):
            raise SeamlessException("Expecting a list at '{x}' but found '{y}'".format(x=context + "." + path, y=val))

        # if there is a value, do we want to coerce each of them
        if coerce is not None:
            try:
                coerced = [self._coerce(v, coerce, accept_failure=allow_coerce_failure) for v in val]
            except SeamlessException as e:
                e.message += "; get_list, path {x}".format(x=context + "." + path)
                raise
            if by_reference:
                self.set_single(path, coerced)
            return coerced
        else:
            if by_reference:
                return val
            else:
                return deepcopy(val)

    def set_list(self, path, val, coerce=None, allow_coerce_failure=False, allow_none=True,
                 ignore_none=False, allowed_values=None, context=""):
        # first ensure that the value is a list
        if not isinstance(val, list):
            val = [val]

        # now carry out the None check
        # for each supplied value, if it is none, and none is not allowed, raise an error if we do not
        # plan to ignore the nones.
        for v in val:
            if v is None and not allow_none:
                if not ignore_none:
                    raise SeamlessException("NoneType is not allowed at '{x}'".format(x=context + "." + path))
            if allowed_values is not None and v not in allowed_values:
                raise SeamlessException("Value '{x}' is not permitted at '{y}'".format(x=val, y=context + "." + path))

        # now coerce each of the values, stripping out Nones if necessary
        try:
            val = [self._coerce(v, coerce, accept_failure=allow_coerce_failure) for v in val if v is not None or not ignore_none]
        except SeamlessException as e:
            e.message += "; set_list, path {x}".format(x=context + "." + path)
            raise

        # check that the cleaned array isn't empty, and if it is behave appropriately
        if len(val) == 0:
            # this is equivalent to a None, so we need to decide what to do
            if ignore_none:
                # if we are ignoring nones, just do nothing
                return
            elif not allow_none:
                # if we are not ignoring nones, and not allowing them, raise an error
                raise SeamlessException("Empty array not permitted at '{x}'".format(x=context + "." + path))

        # now set it on the path
        self._set_path(path, val)

    def add_to_list(self, path, val, coerce=None, allow_coerce_failure=False, allow_none=False,
                    ignore_none=True, unique=False, allowed_values=None, context=""):
        if val is None and ignore_none:
            return

        if val is None and not allow_none:
            raise SeamlessException("NoneType is not allowed in list at '{x}'".format(x=context + "." + path))
        if allowed_values is not None and val not in allowed_values:
            raise SeamlessException("Value '{x}' is not permitted at '{y}'".format(x=val, y=context + "." + path))

        # first coerce the value
        if coerce is not None:
            try:
                val = self._coerce(val, coerce, accept_failure=allow_coerce_failure)
            except SeamlessException as e:
                e.message += "; add_to_list, path {x}".format(x=context + "." + path)
                raise
        current = self.get_list(path, by_reference=True, context=context)

        # if we require the list to be unique, check for the value first
        if unique:
            if val in current:
                return

        # otherwise, append
        current.append(val)

    def delete_from_list(self, path, val=None, matchsub=None, prune=True, apply_struct_on_matchsub=True):
        """
        Note that matchsub will be coerced with the struct if it exists, to ensure
        that the match is done correctly

        :param path:
        :param val:
        :param matchsub:
        :param prune:
        :return:
        """
        l = self.get_list(path)

        removes = []
        i = 0
        for entry in l:
            if val is not None:
                if entry == val:
                    removes.append(i)
            elif matchsub is not None:
                # attempt to coerce the sub
                if apply_struct_on_matchsub:
                    try:
                        type, struct, instructions = self._struct.lookup(path)
                        if struct is not None:
                            matchsub = struct.construct(matchsub, struct).data
                    except:
                        pass

                matches = 0
                for k, v in matchsub.items():
                    if entry.get(k) == v:
                        matches += 1
                if matches == len(list(matchsub.keys())):
                    removes.append(i)
            i += 1

        removes.sort(reverse=True)
        for r in removes:
            del l[r]

        if len(l) == 0 and prune:
            self.delete(path, prune)

    def set_with_struct(self, path, val, check_required=True, silent_prune=False):
        typ, substruct, instructions = self._struct.lookup(path)

        if typ == "field":
            coerce_name, coerce_fn = self._struct.get_coerce(instructions)
            if coerce_fn is None:
                raise SeamlessException("No coersion function defined for type '{x}' at '{c}'".format(x=coerce_name, c=path))
            kwargs = self._struct.kwargs(typ, "set", instructions)
            self.set_single(path, val, coerce=coerce_fn, **kwargs)
        elif typ == "list":
            if not isinstance(val, list):
                val = [val]
            if substruct is not None:
                val = [substruct.construct(x, check_required=check_required, silent_prune=silent_prune).data for x in val]
            kwargs = self._struct.kwargs(typ, "set", instructions)
            coerce_fn = None
            if instructions.get("contains") != "object":
                coerce_name, coerce_fn = self._struct.get_coerce(instructions)
            self.set_list(path, val, coerce=coerce_fn, **kwargs)
        elif typ == "object" or typ == "struct":
            if substruct is not None:
                val = substruct.construct(val, check_required=check_required, silent_prune=silent_prune).data
            self.set_single(path, val)
        else:
            raise SeamlessException("Attempted to set_with_struct on path '{x}' but no such path exists in the struct".format(x=path))

    def add_to_list_with_struct(self, path, val):
        type, struct, instructions = self._struct.lookup(path)
        if type != "list":
            raise SeamlessException("Attempt to add to list '{x}' failed - it is not a list element".format(x=path))
        if struct is not None:
            val = struct.construct(val).data
        kwargs = Construct.kwargs(type, "set", instructions)
        self.add_to_list(path, val, **kwargs)

    def get_property(self, path, wrapper=None):
        if wrapper is None:
            wrapper = lambda x : x

        # pull the object from the structure, to find out what kind of retrieve it needs
        # (if there is a struct)
        type, substruct, instructions = None, None, None
        if self._struct:
            type, substruct, instructions = self._struct.lookup(path)

        if type is None:
            # if there is no struct, or no object mapping was found, try to pull the path
            # as a single node (may be a field, list or dict, we'll find out in a mo)
            val = self.get_single(path)

            # if a wrapper is supplied, wrap it
            if isinstance(val, list):
                return [wrapper(v) for v in val]
            else:
                return wrapper(val)

        if instructions is None:
            instructions = {}

        # if the struct contains a reference to the path, always return something, even if it is None - don't raise an AttributeError
        kwargs = self._struct.kwargs(type, "get", instructions)
        coerce_name, coerce_fn = self._struct.get_coerce(instructions)
        if coerce_fn is not None:
            kwargs["coerce"] = coerce_fn

        if type == "field" or type == "object":
            return wrapper(self.get_single(path, **kwargs))
        elif type == "list":
            l = self.get_list(path, **kwargs)
            return [wrapper(o) for o in l]

        return None

    def set_property(self, path, value, unwrapper=None, allow_coerce_failure=False):
        if unwrapper is None:
            unwrapper = lambda x : x

        # pull the object from the structure, to find out what kind of retrieve it needs
        # (if there is a struct)
        type, substruct, instructions = None, None, None
        if self._struct:
            type, substruct, instructions = self._struct.lookup(path)

        # if no type is found, then this means that either the struct was undefined, or the
        # path did not point to a valid point in the struct.  In the case that the struct was
        # defined, this means the property is trying to set something outside the struct, which
        # isn't allowed.  So, only set types which are None against objects which don't define
        # the struct.
        if type is None:
            if self._struct is None:
                if isinstance(value, list):
                    value = [unwrapper(v) for v in value]
                    self.set_list(path, value, allow_coerce_failure)
                else:
                    value = unwrapper(value)
                    self.set_single(path, value, allow_coerce_failure)

                return True
            else:
                return False

        if type == "field" or type == "object":
            value = unwrapper(value)
        if type == "list":
            value = [unwrapper(v) for v in value]

        try:
            self.set_with_struct(path, value)
            return
        except SeamlessException:
            return False

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

    def _coerce(self, val, coerce, accept_failure=False):
        if coerce is None:
            return val
        try:
            return coerce(val)
        except (ValueError, TypeError):
            if accept_failure:
                return val
            raise SeamlessException("Coerce with '{x}' failed on '{y}' of type '{z}'".format(x=coerce, y=val, z=type(val)))

    def _prune_stack(self, stack):
        while len(stack) > 0:
            context = stack.pMax.Pop()
            todelete = []
            for k, v in context.items():
                if isinstance(v, dict) and len(list(v.keys())) == 0:
                    todelete.append(k)
            for d in todelete:
                del context[d]


class Construct(object):
    def __init__(self, definition, coerce, default_coerce):
        if isinstance(definition, Construct):
            definition = definition._definition

        self._definition = definition
        self._coerce = coerce
        self._default_coerce = default_coerce

    @classmethod
    def merge(cls, target, *args):
        if not isinstance(target, Construct):
            merged = Construct(deepcopy(target), None, None)
        else:
            merged = target

        for source in args:
            if not isinstance(source, Construct):
                source = Construct(source, None, None)

            for field, instructions in source.fields:
                merged.add_field(field, instructions, overwrite=False)

            for obj in source.objects:
                merged.add_object(obj)

            for field, instructions in source.lists:
                merged.add_list(field, instructions, overwrite=False)

            for r in source._definition.get("required", []):
                merged.add_required(r)

            for field, struct in source._definition.get("structs", {}).items():
                merged.add_substruct(field, struct, mode="merge")

        return merged

    @classmethod
    def kwargs(cls, type, dir, instructions):
        # if there are no instructions there are no kwargs
        if instructions is None:
            return {}

        # take a copy of the instructions that we can modify
        kwargs = deepcopy(instructions)

        # remove the known arguments for the field type
        if type == "field":
            if "coerce" in kwargs:
                del kwargs["coerce"]

        elif type == "list":
            if "coerce" in kwargs:
                del kwargs["coerce"]
            if "contains" in kwargs:
                del kwargs["contains"]

        nk = {}
        if dir == "set":
            for k, v in kwargs.items():
                # basically everything is a "set" argument unless explicitly stated to be a "get" argument
                if not k.startswith("get__"):
                    if k.startswith("set__"):    # if it starts with the set__ prefix, remove it
                        k = k[5:]
                    nk[k] = v
        elif dir == "get":
            for k, v in kwargs.items():
                # must start with "get" argument
                if k.startswith("get__"):
                    nk[k[5:]] = v

        return nk

    @property
    def raw(self):
        return self._definition

    @property
    def required(self):
        return self._definition.get("required", [])

    def add_required(self, field):
        if "required" not in self._definition:
            self._definition["required"] = []
        if field not in self._definition["required"]:
            self._definition["required"].append(field)

    @property
    def allowed(self):
        return list(self._definition.get("fields", {}).keys()) + \
                self._definition.get("objects", []) + \
                list(self._definition.get("lists", {}).keys())

    @property
    def objects(self):
        return self._definition.get("objects", [])

    def add_object(self, object_name):
        if "objects" not in self._definition:
            self._definition["objects"] = []
        if object_name not in self._definition["objects"]:
            self._definition["objects"].append(object_name)

    @property
    def substructs(self):
        return self._definition.get("structs", {})

    def substruct(self, field):
        s = self.substructs.get(field)
        if s is None:
            return None
        return Construct(s, self._coerce, self._default_coerce)

    def add_substruct(self, field, struct, mode="merge"):
        if "structs" not in self._definition:
            self._definition["structs"] = {}
        if mode == "overwrite" or field not in self._definition["structs"]:
            self._definition["structs"][field] = deepcopy(struct)
        else:
            # recursively merge
            self._definition["structs"][field] = Construct.merge(self._definition["structs"][field], struct).raw

    @property
    def fields(self):
        return self._definition.get("fields", {}).items()

    def field_instructions(self, field):
        return self._definition.get("fields", {}).get(field)

    def add_field(self, field_name, instructions, overwrite=False):
        if "fields" not in self._definition:
            self._definition["fields"] = {}
        if overwrite or field_name not in self._definition["fields"]:
            self._definition["fields"][field_name] = deepcopy(instructions)

    @property
    def lists(self):
        return self._definition.get("lists", {}).items()

    @property
    def list_names(self):
        return self._definition.get("lists", {}).keys()

    def list_instructions(self, field):
        return self._definition.get("lists", {}).get(field)

    def add_list(self, list_name, instructions, overwrite=False):
        if "lists" not in self._definition:
            self._definition["lists"] = {}
        if overwrite or list_name not in self._definition["lists"]:
            self._definition["lists"][list_name] = deepcopy(instructions)

    def get_coerce(self, instructions):
        coerce_name = instructions.get("coerce", self._default_coerce)
        return coerce_name, self._coerce.get(coerce_name)

    def get(self, elem, default=None):
        if elem in self._definition:
            return self._definition.get(elem)
        else:
            return default

    def lookup(self, path):
        bits = path.split(".")

        # if there's more than one path element, we will need to recurse
        if len(bits) > 1:
            # it has to be an object, in order for the path to still have multiple
            # segments
            if bits[0] not in self.objects:
                return None, None, None
            substruct = self.substruct(bits[0])
            return substruct.lookup(".".join(bits[1:]))
        elif len(bits) == 1:
            # first check the fields
            instructions = self.field_instructions(bits[0])
            if instructions is not None:
                return "field", None, instructions

            # then check the lists
            instructions = self.list_instructions(bits[0])
            if instructions is not None:
                substruct = self.substruct(bits[0])
                return "list", substruct, instructions

            # then check the objects
            if bits[0] in self.objects:
                substruct = self.substruct(bits[0])
                return "struct", substruct, instructions

        return None, None, None

    def construct(self, obj, check_required=True, silent_prune=False, allow_other_fields=False):

        def recurse(obj, struct, context):
            if obj is None:
                return None
            if not isinstance(obj, dict):
                raise SeamlessException("Expected a dict at '{c}' but found something else instead".format(c=context))

            keyset = obj.keys()

            # if we are checking required fields, then check them
            # FIXME: might be sensible to move this out to a separate phase, independent of constructing
            if check_required:
                for r in struct.required:
                    if r not in keyset:
                        raise SeamlessException("Field '{r}' is required but not present at '{c}'".format(r=r, c=context))

            # check that there are no fields that are not allowed
            # Note that since the construct mechanism copies fields explicitly, silent_prune just turns off this
            # check
            if not allow_other_fields and not silent_prune:
                allowed = struct.allowed
                for k in keyset:
                    if k not in allowed:
                        c = context if context != "" else "root"
                        raise SeamlessException("Field '{k}' is not permitted at '{c}'".format(k=k, c=c))

            # make a SeamlessData instance for gathering all the new data
            constructed = SeamlessData(struct=struct)

            # now check all the fields
            for field_name, instructions in struct.fields:
                val = obj.get(field_name)
                if val is None:
                    continue
                typ, substruct, instructions = struct.lookup(field_name)
                if instructions is None:
                    raise SeamlessException("No instruction set defined for field at '{x}'".format(x=context + field_name))
                coerce_name, coerce_fn = struct.get_coerce(instructions)
                if coerce_fn is None:
                    raise SeamlessException("No coerce function defined for type '{x}' at '{c}'".format(x=coerce_name, c=context + field_name))
                kwargs = struct.kwargs(typ, "set", instructions)
                constructed.set_single(field_name, val, coerce=coerce_fn, context=context, **kwargs)

            # next check all the objects (which will involve a recursive call to this function)
            for field_name in struct.objects:
                val = obj.get(field_name)
                if val is None:
                    continue
                if type(val) != dict:
                    raise SeamlessException("Expected dict at '{x}' but found '{y}'".format(x=context + field_name, y=type(val)))

                typ, substruct, instructions = struct.lookup(field_name)

                if substruct is None:
                    # this is the lowest point at which we have instructions, so just accept the data structure as-is
                    # (taking a deep copy to destroy any references)
                    constructed.set_single(field_name, deepcopy(val))
                else:
                    # we need to recurse further down
                    beneath = recurse(val, substruct, context=context + field_name + ".")

                    # what we get back is the correct sub-data structure, which we can then store
                    constructed.set_single(field_name, beneath)

            # now check all the lists
            for field_name, instructions in struct.lists:
                vals = obj.get(field_name)
                if vals is None:
                    continue
                if not isinstance(vals, list):
                    raise SeamlessException("Expecting list at '{x}' but found something else '{y}'".format(x=context + field_name, y=type(val)))

                typ, substruct, instructions = struct.lookup(field_name)
                kwargs = struct.kwargs(typ, "set", instructions)

                contains = instructions.get("contains")
                if contains == "field":
                    # coerce all the values in the list
                    coerce_name, coerce_fn = struct.get_coerce(instructions)
                    if coerce_fn is None:
                        raise SeamlessException("No coerce function defined for type '{x}' at '{c}'".format(x=coerce_name, c=context + field_name))

                    for i in range(len(vals)):
                        val = vals[i]
                        constructed.add_to_list(field_name, val, coerce=coerce_fn, **kwargs)

                elif contains == "object":
                    # for each object in the list, send it for construction
                    for i in range(len(vals)):
                        val = vals[i]

                        if type(val) != dict:
                            print("Expected dict at '{x}[{p}]' but got '{y}'".format(x=context + field_name, y=type(val), p=i))
                            raise SeamlessException("Expected dict at '{x}[{p}]' but got '{y}'".format(x=context + field_name, y=type(val), p=i))

                        substruct = struct.substruct(field_name)
                        if substruct is None:
                            constructed.add_to_list(field_name, deepcopy(val))
                        else:
                            # we need to recurse further down
                            beneath = recurse(val, substruct, context=context + field_name + "[" + str(i) + "].")

                            # what we get back is the correct sub-data structure, which we can then store
                            constructed.add_to_list(field_name, beneath)

                else:
                    raise SeamlessException("Cannot understand structure where list '{x}' elements contain '{y}'".format(x=context + field_name, y=contains))

            # finally, if we allow other fields, make sure that they come across too
            if allow_other_fields:
                known = struct.allowed
                for k, v in obj.items():
                    if k not in known:
                        constructed.set_single(k, v)

            # ensure any external references to the object persist
            obj.clear()
            obj.update(constructed.data)
            return obj

        ready = recurse(obj, self, "[root]")
        return SeamlessData(ready, struct=self)

    def validate(self):

        def recurse(struct, context):
            # check that only the allowed keys are present
            keys = struct.raw.keys()
            for k in keys:
                if k not in ["fields", "objects", "lists", "required", "structs"]:
                    raise SeamlessException("Key '{x}' present in struct at '{y}', but is not permitted".format(x=k, y=context))

            # now go through and make sure the fields are the right shape:
            for field_name, instructions in struct.fields:
                for k,v in instructions.items():
                    if not isinstance(v, list) and not isinstance(v, str) and not isinstance(v, bool):
                        raise SeamlessException("Argument '{a}' in field '{b}' at '{c}' is not a string, list or boolean".format(a=k, b=field_name, c=context))

            # then make sure the objects are ok
            for o in struct.objects:
                if not isinstance(o, str):
                    raise SeamlessException("There is a non-string value in the object list at '{y}'".format(y=context))

            # make sure the lists are correct
            for field_name, instructions in struct.lists:
                contains = instructions.get("contains")
                if contains is None:
                    raise SeamlessException("No 'contains' argument in list definition for field '{x}' at '{y}'".format(x=field_name, y=context))
                if contains not in ["object", "field"]:
                    raise SeamlessException("'contains' argument in list '{x}' at '{y}' contains illegal value '{z}'".format(x=field_name, y=context, z=contains))
                for k,v in instructions.items():
                    if not isinstance(v, list) and not isinstance(v, str) and not isinstance(v, bool):
                        raise SeamlessException("Argument '{a}' in list '{b}' at '{c}' is not a string, list or boolean".format(a=k, b=field_name, c=context))

            # make sure the requireds are correct
            for o in struct.required:
                if not isinstance(o, str):
                    raise SeamlessException("There is a non-string value in the required list at '{y}'".format(y=context))

            # now do the structs, which will involve some recursion
            substructs = struct.substructs

            # first check that there are no previously unknown keys in there
            possibles = struct.objects + list(struct.list_names)
            for s in substructs:
                if s not in possibles:
                    raise SeamlessException("struct contains key '{a}' which is not listed in object or list definitions at '{x}'".format(a=s, x=context))

            # now recurse into each struct
            for k, v in substructs.items():
                nc = context
                if nc == "":
                    nc = k
                else:
                    nc += "." + k
                recurse(Construct(v, None, None), context=nc)

            return True

        recurse(self, "[root]")
