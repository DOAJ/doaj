from portality import reporting
from portality.lib import dates
import os


def reports(fr, to, outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    reporting.provenance_reports(fr, to, outdir)
    reporting.content_reports(fr, to, outdir)

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--from_date", help="Start date for reporting period (YYYY-MM-DDTHH:MM:SSZ)", default="1970-01-01T00:00:00Z")
    parser.add_argument("-t", "--to_date", help="End date for reporting period (YYYY-MM-DDTHH:MM:SSZ)", default=dates.now())
    parser.add_argument("-o", "--out", help="output directory into which reports should be made (will be created if it doesn't exist)", default="report_" + dates.now())

    args = parser.parse_args()

    reports(args.from_date, args.to_date, args.out)