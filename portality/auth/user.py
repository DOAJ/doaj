from portality.core import app

def update(obj,user):
    if obj.__type__ == 'account':
        if is_super(user):
            return True
        else:
            return not user.is_anonymous() and user.id == obj.id
    elif obj.__type__ == 'record':
        if is_super(user):
            return True
        else:
            if 'public' in record.data.get('access',[]):
                return True
            elif 'users' in record.get('access',[]) and not user.is_anonymous():
                return True
            elif not user.is_anonymous() and user.id == record.get('author',''):
                return True
            else:
                return False
    else:
        return False

def is_super(user):
    return not user.is_anonymous() and user.id in app.config['SUPER_USER']
