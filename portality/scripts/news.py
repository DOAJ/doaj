from portality.core import app

if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
    print "System is in READ-ONLY mode, script cannot run"
    exit()

from portality import blog
blog.read_feed()