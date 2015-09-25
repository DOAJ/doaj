from portality.models import Account
from portality.core import app

def input_password():
    password = None
    while password is None:
        password = request_password()
    return password

def request_password():
    password = getpass.getpass()
    confirm = getpass.getpass("Confirm Password:")
    if password != confirm:
        print "passwords do not match - try again!"
        return None
    return password

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse, getpass
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-u", "--username", help="username of user.  Use an existing username to update the password or other details")
    parser.add_argument("-e", "--email", help="email address of user")
    parser.add_argument("-p", "--password", help="password for the new or existing user.  If omitted, you will be prompted for one on the next line")
    parser.add_argument("-r", "--role", help="comma separated list of roles to be held by this account")
    
    args = parser.parse_args()
    
    if not args.username:
        print "Please specify a username with the -u option"
        exit()
    
    if not args.role:
        print "WARNING: no role specified, so this user won't be able to do anything"
    
    username = args.username
    email = args.email
    password = None
    roles = [r.strip() for r in args.role.split(",")] if args.role is not None else []

    if 'api' not in roles:
        print 'WARNING: \'api\' role omitted. New users are generally given an API Key'
    
    if args.password:
        password = args.password
    else:
        password = input_password()
    
    acc = Account.pull(username)
    if not acc:
        acc = Account(id=username, email=email)
    acc.set_role(roles)
    acc.set_password(password)
    acc.save()
