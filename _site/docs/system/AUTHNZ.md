# Authorisation and Authentication

## Creating a new user

To create a new user for the DOAJ use the createuser.py script in the first instance:

    python portality/scripts/createuser.py -u username -r admin -p password -e email

This will create a new user with the "admin" role.

If you want to update the user account at any point via the command line, use the same command again.  Any user that already exists and is identified by the argument to the -u option will be modified/overwritten

To edit the user via the web interface, login to the DOAJ application and go to

    /account/<username>

Once you have created the initial administrator, new users can be created when logged in as that administrator via:

    /account/register

## Role-based authorisation

The DOAJ user area uses role-based authorisation.

When implementing a feature, that feature should be given a role name.

For example, if implementing a "Create new Administrator" feature, a new role should be defined with the name "create_administrator".  Any actions which pertain to the creation of a new administrator should be authorised with a call to the current user's has_role method:

    if current_user.has_role("create_administrator"):
        # do some create administrator stuff
    else:
        # unauthorised

There are two high-level roles which the DOAJ implements

* admin - for the DOAJ administrators, who will have complete super-user priviledges
* publisher - for publisher users of the DOAJ, who will be administering their own content

At this early stage of development, user accounts will only need to be assigned one of those roles.  The "admin" role is a super user so any calls to has_role for any role on an administrator's user object will result in success (i.e. has_role("create_administrator") on a user with role "admin" will return True).

At a later stage, and when it becomes necessary, we will implement mappings of the high level roles to more granular roles.


## Authentication

When developing authenticated areas of the DOAJ site, there are two things you should do.

The blueprint should have a "before_request" method which rejects anonymous users or users who do not have the correct role.  For example:

    # restrict everything in admin to logged in users with the "publsiher" role
    @blueprint.before_request
    def restrict():
        if current_user.is_anonymous or not current_user.has_role("publisher"):
            abort(401)

The restricted method should be annotated with flask.ext.login's login_required:

    from flask_login import login_required
    
    @blueprint.route("/")
    @login_required
    def index():
        # some restricted method
