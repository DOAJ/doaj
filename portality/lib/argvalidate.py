from portality.core import app

def argvalidate(caller_name, args_and_rules, exception):
    for anr in args_and_rules:
        arg = anr.get("arg")
        arg_name = anr.get("arg_name")
        inst = anr.get("instance")
        allow_none = anr.get("allow_none", True)

        if not allow_none:
            if arg is None:
                raise exception(caller_name + " expected '" + arg_name + "' not to be None")

        if inst is not None and arg is not None:
            if not isinstance(arg, inst):
                raise exception(caller_name + " expected '" + arg_name + "' to be " + inst.__name__ + " but got " + type(arg).__name__)
