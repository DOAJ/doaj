from portality.models import Account
from portality.core import app


def delete_user(username):

    prefix = "Delete existing user: "
    acc = Account.pull(username)
    try:
        acc.delete()
    except:
        print("no such user:" + username)
        return

    print(prefix + username + "deleted")


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse, getpass

    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username",
                        help="username of user.  Use an existing username to update the password or other details")

    args = parser.parse_args()

    if not args.username and not args.csv:
        print("Please specify a username with the -u option")
        exit()

    if args.username:
        username = args.username


        delete_user(username)