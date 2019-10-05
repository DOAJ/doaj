# -*- coding: UTF-8 -*-
""" Create mappings from models """

from portality.lib import plugin


def get_mappings(app):
    """Get the full set of mappings required for the app"""

    # LEGACY DEFAULT MAPPINGS
    mappings = app.config["MAPPINGS"]

    # TYPE SPECIFIC MAPPINGS
    # get the list of classes which carry the type-specific mappings to be loaded
    mapping_daos = app.config.get("ELASTIC_SEARCH_MAPPINGS", [])

    # load each class and execute the "mappings" function to get the mappings that need to be imported
    for cname in mapping_daos:
        klazz = plugin.load_class_raw(cname)
        mappings[klazz.__type__] = klazz().mappings()

    return mappings


def apply_mapping_opts(field_name, path, spec, mapping_opts):
    dot_path = '.'.join(path + (field_name,))
    if dot_path in mapping_opts['exceptions']:
        return mapping_opts['exceptions'][dot_path]
    elif spec['coerce'] in mapping_opts['coerces']:
        return mapping_opts['coerces'][spec['coerce']]
    else:
        # We have found a data type in the struct we don't have a map for to ES type.
        raise Exception("Mapping error - no mapping found for {}".format(spec['coerce']))


def create_mapping(struct, mapping_opts, path=()):
    result = {"properties": {}}

    for field, spec in struct.get("fields", {}).items():
        result["properties"][field] = apply_mapping_opts(field, path, spec, mapping_opts)

    for field, spec in struct.get("lists", {}).items():
        if "coerce" in spec:
            result["properties"][field] = apply_mapping_opts(field, path, spec, mapping_opts)

    for struct_name, struct_body in struct.get("structs", {}).items():
        result["properties"][struct_name] = create_mapping(struct_body, mapping_opts, path + (struct_name,))

    return result
