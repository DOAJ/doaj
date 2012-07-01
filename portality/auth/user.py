from portality.core import current_user, app

def update(account, user):
    allowed = not account.is_anonymous() and user.id == account.id
    if not account.is_anonymous():
        if account.id in app.config['super_user']:
            allowed = True
    return allowed

def is_super(account):
    return not account.is_anonymous() and account.id in app.config['super_user']
