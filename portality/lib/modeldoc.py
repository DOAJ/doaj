from portality.lib import dataobj, dates, plugin
from datetime import datetime
import json, codecs

DO_TYPE_TO_JSON_TYPE = {
    "str": "string",
    "utcdatetime": "timestamp",
    "integer": 0,
    "bool": True,
    "float": 0.0,
    "isolang": "string",
    "url": "string",
    "isolang_2letter": "string",
    "bigenddate" : "datestamp"
}

DO_TYPE_TO_DATATYPE = {
    "str": "str",
    "utcdatetime": "str",
    "integer": "int",
    "bool": "bool",
    "float": "float",
    "isolang": "str",
    "url": "str",
    "isolang_2letter": "str",
    "bigenddate" : "str"
}

DO_TYPE_TO_FORMAT = {
    "str": "",
    "utcdatetime": "UTC ISO formatted date: YYYY-MM-DDTHH:MM:SSZ",
    "integer": "",
    "bool": "",
    "float": "",
    "isolang": "3 letter ISO language code",
    "url": "URL",
    "isolang_2letter": "2 letter ISO language code",
    "bigenddate" : "Date, year first: YYYY-MM-DD"
}

def format(klazz, example, fields):
    title = "# " + klazz.__name__

    intro = "The JSON structure of the model is as follows:"

    struct = "```json\n" + json.dumps(example, indent=4, sort_keys=True) + "\n```"

    table_intro = "Each of the fields is defined as laid out in the table below.  All fields are optional unless otherwise specified:"

    table = "| Field | Description | Datatype | Format | Allowed Values |\n"
    table += "| ----- | ----------- | -------- | ------ | -------------- |\n"

    keys = list(fields.keys())
    keys.sort()

    for k in keys:
        desc, datatype, format, values = fields.get(k)
        table += "| {field} | {desc} | {datatype} | {format} | {values} |\n".format(field=k, desc=desc, datatype=datatype, format=format, values=values)

    return title + "\n\n" + intro + "\n\n" + struct + "\n\n" + table_intro + "\n\n" + table

def document(klazz, field_descriptions):
    inst = klazz()
    base_struct = inst.get_struct()

    fields = {}

    def do_document(path, struct, fields):
        example = {}

        # first do all the fields at this level
        for simple_field, instructions in struct.get('fields', {}).items():
            example[simple_field] = type_map(instructions.get("coerce"))
            fields[path + simple_field] = (field_descriptions.get(path + simple_field, ""), datatype(instructions.get("coerce")), form(instructions.get("coerce")), values_or_range(instructions.get("allowed_values"), instructions.get("allowed_range")))

        # now do all the objects at this level
        for obj in struct.get('objects', []):
            newpath = obj + "." if not path else path + obj + "."
            instructions = struct.get('structs', {}).get(obj, {})
            example[obj] = do_document(newpath, instructions, fields)

        # finally do all the lists at this level
        for l, instructions in struct.get('lists', {}).items():
            if instructions['contains'] == 'field':
                example[l] = [type_map(instructions.get("coerce"))]
                fields[path + l] = (field_descriptions.get(path + l, ""), datatype(instructions.get("coerce")), form(instructions.get("coerce")), values_or_range(instructions.get("allowed_values"), instructions.get("allowed_range")))

            elif instructions['contains'] == 'object':
                newpath = l + "." if not path else path + l + "."
                inst = struct.get('structs', {}).get(l, {})
                example[l] = [do_document(newpath, inst, fields)]

        return example

    example = do_document("", base_struct, fields)

    return example, fields

def type_map(t):
    type = DO_TYPE_TO_JSON_TYPE.get(t, "string")
    if type == "timestamp":
        return dates.now()
    elif type == "datestamp":
        return dates.format(datetime.utcnow(), "%Y-%m-%d")
    return type

def datatype(t):
    return DO_TYPE_TO_DATATYPE.get(t, "str")

def form(t):
    return DO_TYPE_TO_FORMAT.get(t, "")

def values_or_range(vals, range):
    if vals is not None:
        return ", ".join(vals)
    if range is not None:
        lower, upper = range
        if lower is not None and upper is not None:
            return lower + " to " + upper
        elif lower is not None and upper is None:
            return "less than " + lower
        elif lower is None and upper is not None:
            return "greater than " + upper
    return ""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--klazz", help="class to document")
    parser.add_argument("-o", "--out", help="output file")
    parser.add_argument("-f", "--fields", help="field descriptions table")
    args = parser.parse_args()

    descriptions = {}
    if args.fields:
        with codecs.open(args.fields) as f:
            fds = f.read()
        lines = fds.split("\n")
        for line in lines:
            sep = line.find(":")
            descriptions[line[:sep]] = line[sep + 1:].strip()

    k = plugin.load_class_raw(args.klazz)
    example, fields = document(k, descriptions)
    doc = format(k, example, fields)

    with codecs.open(args.out, "wb") as f:
        f.write(doc)
