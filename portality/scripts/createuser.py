from portality.models import Account
import csv


def create_users(source):
    with open(source, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            username = row[0]
            email = row[1]
            password = row[2] if row[2] != "" else None
            roles = [r.strip() for r in row[3].split(",")]
            create_user(username, email, password, roles)


def create_user(username, email, password, roles):
    if password is None:
        password = input_password(username)

    prefix = "Modified existing user: "
    acc = Account.pull(username)
    if not acc:
        prefix = "Created new user: "
        acc = Account(id=username, email=email)
    acc.set_email(email)
    acc.set_role(roles)
    acc.set_password(password)
    acc.save()

    print(prefix + username)


def input_password(username):
    password = None
    while password is None:
        password = request_password(username)
    return password


def request_password(username):
    password = getpass.getpass()
    confirm = getpass.getpass("Confirm Password for " + username + ":")
    if password != confirm:
        print("passwords do not match - try again!")
        return None
    return password


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse, getpass
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-u", "--username", help="username of user.  Use an existing username to update the password or other details")
    parser.add_argument("-e", "--email", help="email address of user")
    parser.add_argument("-p", "--password", help="password for the new or existing user.  If omitted, you will be prompted for one on the next line")
    parser.add_argument("-r", "--role", help="comma separated list of roles to be held by this account")
    parser.add_argument("-c", "--csv", help="csv of users, emails, roles and passwords to be created/updated")
    
    args = parser.parse_args()
    
    if not args.username and not args.csv:
        print("Please specify a username with the -u option or a CSV of users with the -c option")
        exit()
    
    if not args.role and not args.csv:
        print("WARNING: no role specified, so this user won't be able to do anything")

    if args.username:
        username = args.username
        email = args.email
        roles = [r.strip() for r in args.role.split(",")] if args.role is not None else []

        password = None
        if args.password:
            password = args.password

        create_user(username, email, password, roles)

    elif args.csv:
        create_users(args.csv)


