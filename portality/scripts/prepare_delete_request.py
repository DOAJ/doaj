import sys, os, json, urllib.request, urllib.parse, urllib.error, argparse

TEST_SOURCE = "{%22query%22:{%22filtered%22:{%22query%22:{%22query_string%22:{%22query%22:%221893-3211%22,%22default_field%22:%22index.issn.exact%22,%22default_operator%22:%22AND%22}},%22filter%22:{%22bool%22:{%22must%22:%5B{%22term%22:{%22_type%22:%22article%22}}%5D}}}}}"


def clean_list(l):
    '''Clean up a list coming from an HTML form. Returns a list.
    Returns an empty list if given an empty list.

    Example: you have a list of tags. This is coming in from the form
    as a single string: e.g. "tag1, tag2, ".
    You do tag_list = request.values.get("tags",'').split(",")
    Now you have the following list: ["tag1"," tag2", ""]
    You want to both trim the whitespace from list[1] and remove the empty
    element - list[2]. This func will do it.

    What it does:
    1. Trim whitespace on both ends of individual strings
    2. Remove empty strings
    3. Only check for empty strings AFTER splitting and trimming the
    individual strings (in order to remove empty list elements).
    '''
    return [clean_item for clean_item in [item.strip() for item in l] if clean_item]


def load(filename):
    with open(filename, 'rb') as i:
        content = i.read()
    return content


def save(filename, content):
    with open(filename, 'wb') as o:
        o.write(content)


def load_lines(filename):
    content = load(filename)
    lines = content.splitlines()
    return clean_list(lines)


def convert_from_file_to_dir(i, o):
    """Read in sources from a file and output a query as .json for each source into a directory."""
    sources = load_lines(i)
    for index, s in enumerate(sources):
        save(os.path.join(o, str(index) + '.json'), json.dumps(source2json(s), indent=3))


def source2json(s):
    parsed = urllib.parse.unquote(s)
    return json.loads(parsed)


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("querystring", nargs='?', help="Pass just one query string to the script to get the result immediately on STDOUT, no files needed. Or you can pass an input file and output dir only.")
    parser.add_argument("-t", "--test", help="Runs and shows you a built-in test for what this script does.", action="store_true")
    parser.add_argument("-i", "--input", help="Input file containing all the query strings you want to decode separated by newlines.")
    parser.add_argument("-o", "--outputdir", help="If you've specified an input file, you must specify an output directory where the .json files will be stored. 1 for each query found in your input file.")

    args = parser.parse_args()

    if args.querystring:
        print(json.dumps(source2json(args.querystring), indent=3))
        sys.exit(0)

    if args.test:
        print('Test encoded source (e.g. from a url with a source= argument in it)')
        print(TEST_SOURCE)
        print('  Result:')
        print(json.dumps(source2json(TEST_SOURCE), indent=3))
        sys.exit(0)

    if not args.input and not args.outputdir:
        # no args at all
        parser.print_help()
        sys.exit(1)
    
    if (args.input and not args.outputdir) or (args.outputdir and not args.input):
        print('If you specify an input file, you must also specify the output dir. And vice versa.')
        sys.exit(1)

    convert_from_file_to_dir(args.input, args.outputdir)


if __name__ == '__main__':
    main()
