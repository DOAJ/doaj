from portality.core import app

class Authorise(object):
    @classmethod
    def has_role(cls, role, reference):
        ultra = False
        if role.startswith("ultra_"):
            ultra = True

        # if we are the super user we can do anything
        if app.config["SUPER_USER_ROLE"] in reference and not ultra:
            return True
        
        # if the user's role list contains the role explicitly then do it
        if role in reference:
            return True
        
        # get the de-duplicated list of roles that the user has
        full = cls.get_roles(reference)
        if role in full:
            return True

        return False

    @classmethod
    def get_roles(cls, reference):
        role_map = app.config.get("ROLE_MAP", {})
        roles = []
        for r in reference:
            roles += role_map.get(r, [])
        return list(set(roles))

    @classmethod
    def top_level_roles(cls):
        return app.config.get("TOP_LEVEL_ROLES", [])

