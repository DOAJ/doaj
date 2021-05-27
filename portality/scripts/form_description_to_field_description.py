import csv
from portality.crosswalks.application_form import ApplicationFormXWalk


def generate(formdoc, output):
    with open(formdoc, "r", encoding="utf-8") as f, open(output, "w", encoding="utf-8") as g:
        reader = csv.reader(f)
        first = True
        for row in reader:
            if first:
                first = False
                continue

            field_name = row[1]
            desc = row[2]

            object_fields = ApplicationFormXWalk.formField2objectFields(field_name)
            for of in object_fields:
                g.write(of + ": " + desc + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--formdoc", help="the generated form documentation file to build our docs from")
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    generate(args.formdoc, args.out)
