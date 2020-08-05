import importlib

# Note that we delay import of app to the functions which need it,
# since we may want to load plugins during app creation too, and otherwise
# we'd get circular import problems

class PluginException(Exception):
    pass

def load_class_raw(classpath):
    modpath = ".".join(classpath.split(".")[:-1])
    classname = classpath.split(".")[-1]
    try:
        mod = importlib.import_module(modpath)
    except ImportError:
        return None
    klazz = getattr(mod, classname, None)
    return klazz

def load_class(classpath, cache_class_ref=True):
    from portality.core import app
    klazz = app.config.get("PLUGIN_CLASS_REFS", {}).get(classpath)
    if klazz is not None:
        return klazz

    klazz = load_class_raw(classpath)
    if klazz is None:
        app.logger.info("Could not load function {x}".format(x=classpath))
        return None

    if cache_class_ref:
        if "PLUGIN_CLASS_REFS" not in app.config:
            app.config["PLUGIN_CLASS_REFS"] = {}
        app.config["PLUGIN_CLASS_REFS"][classpath] = klazz

    return klazz

def load_module(modpath):
    return importlib.import_module(modpath)

def load_function_raw(fnpath):
    modpath = ".".join(fnpath.split(".")[:-1])
    fnname = fnpath.split(".")[-1]
    try:
        mod = importlib.import_module(modpath)
    except ImportError:
        return None
    fn = getattr(mod, fnname, None)
    return fn

def load_function(fnpath, cache_fn_ref=True):
    from portality.core import app
    fn = app.config.get("PLUGIN_FN_REFS", {}).get(fnpath)
    if fn is not None:
        return fn

    fn = load_function_raw(fnpath)
    if fn is None:
        app.logger.info("Could not load function {x}".format(x=fnpath))
        return None

    if cache_fn_ref:
        if "PLUGIN_FN_REFS" not in app.config:
            app.config["PLUGIN_FN_REFS"] = {}
        app.config["PLUGIN_FN_REFS"][fnpath] = fn

    return fn
