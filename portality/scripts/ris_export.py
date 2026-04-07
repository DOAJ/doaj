from portality.bll import DOAJ
from portality.core import app
from portality.lib import dates

from portality.tasks import ris_export as asc
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob

from portality.bll.services.export import RISExportReporter

class CLIRISExportReporter(RISExportReporter):
    def processed(self, total_so_far):
        super().processed(total_so_far)
        if self._processed % 10000 == 0:
            self.msg(f"Processed {self._processed} articles so far; {self._loaded} RIS exports generated.")

    def msg(self, message):
        print(dates.now_str() + " " + message)

if __name__ == "__main__":
    start = dates.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true", help="force update of RIS entries")
    parser.add_argument("-id", "--id", help="ID of record to (re)generate")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, enforcing read-only for this script")
        exit()

    svc = DOAJ.exportService()
    if args.id:
        # we are doing a single record
        print("Generating {x}".format(x=args.id))
        svc.ris(args.id)
    else:
        # we are doing all records
        svc.bulk_generate_ris(force_update=args.force, reporter=CLIRISExportReporter())

    end = dates.now()
    print(start, "-", end)
