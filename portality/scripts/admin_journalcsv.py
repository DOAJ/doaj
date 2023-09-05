# ~~AdminJournalCSV:CLI~~
from portality.core import app
from portality.bll import DOAJ


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file for admin csv", required=True)
    parser.add_argument("-a", "--do_not_obscure_accs", help="set this flag if the accounts should not be obscured", action='store_false')
    parser.add_argument("-s", "--sensitive", help="Add sensitive account info (name and email address)", action='store_true')
    args = parser.parse_args()

    if args.sensitive and args.do_not_obscure_accs:
        print("Can't obscure the account info if you're adding the extra sensitive fields, try with both -s and -a")
        exit(1)

    # ~~-> Journal:Service~~
    journalService = DOAJ.journalService()
    journalService.admin_csv(file_path=args.out,
                             obscure_accounts=args.do_not_obscure_accs,
                             add_sensitive_account_info=args.sensitive)
