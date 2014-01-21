from portality.core import app

class Authorise(object):
    @classmethod
    def has_role(cls, role, reference):
        # if we are the super user we can do anything
        if app.config["SUPER_USER_ROLE"] in reference:
            return True
        
        # if the user's role list contains the role explicitly then do it
        if role in reference:
            return True
        
        # later we will want to expand the user's roles to the full set and see if the role is in there
        # as and when that level of functionality is required
        
        # but for now, if we get here we have failed to authorise
        return False
        
        
