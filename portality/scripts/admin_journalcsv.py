# ~~AdminJournalCSV:CLI~~
from portality.core import app
from portality.bll import DOAJ


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file for admin csv")
    args = parser.parse_args()

    # ~~-> Journal:Service~~
    journalService = DOAJ.journalService()
    journalService.admin_csv(args.out)








