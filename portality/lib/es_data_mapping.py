# -*- coding: UTF-8 -*-
""" Create mappings from models """

from portality.core import app


def create_mapping(dataobj_struct, mapping_opts):
    default_string = app.config['DEFAULT_STRING_MAPPING']

    print default_string
