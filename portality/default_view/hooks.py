
# this runs a github web hook endpoint
# see https://help.github.com/articles/post-receive-hooks

import os
from flask import Blueprint
from git import *
from subprocess import call

blueprint = Blueprint('Hooks', __name__)


@blueprint.route('/', methods=['POST'])
def hooks():
    message = request.json.get('payload',{})
    which = message.get('repository',{}).get('name',"")
    
    # now define the actions that should be performed when a particular 
    # repo is updated (identified by which)
    
    # this example just triggers a pull when the message is received
    # then restarts a service via supervisor
    if which == "portality":
        _pull(message)
        call("sudo supervisorctl restart portality", shell=True)
    
    # this example does some index updating based on content of the message
    # this is for use with a pagemanager that writes file content to disk
    if which == "content":
        _pull(message)
        import portality.models as models
        for commit in message.get('commits',[]):
            for add in commit.get('added',[]):
                try:
                    content = open(app.config['REPOS'][which]['path'] + '/' + add,'r').read()
                    path, fn = add.rstrip('/').split('/')
                    p = models.Pages({
                        "url":'/' + add,
                        "title":fn,
                        "content":content
                    })
                    p.save()
                    content.close()
                except:
                    pass
            for remove in commit.get('removed',[]):
                try:
                    p = models.Pages().pull_by_url('/' + remove)
                    if p is not None:
                        pagemanager._sync_delete(p)
                except:
                    pass
            for modify in commit.get('modified',[]):
                try:
                    p = models.Pages().pull_by_url('/' + modify)
                    if p is not None:
                        content = open(app.config['REPOS'][which]['path'] + '/' + modify,'r').read()
                        p.data['content'] = content
                        p.save()
                        content.close()
                except:
                    pass
        
        
# pull from the identified repo when necessary
# just a simple pull that will run if local commit is not equal to latest one
# see http://pythonhosted.org/GitPython/0.3.1/tutorial.html
def _pull(message):
    which = message['repository']['name']
    repo = Repo(app.config['REPOS'][which]['path'])
    assert repo.bare == False
    if repo.heads.master.commit != message['after']:
        repo.remotes.origin.pull()
        # TODO: need a submodule update call









