'''
A contact-form backend mailer endpoint
'''

from flask import Blueprint, request, abort

from portality.core import app
import portality.util as util


blueprint = Blueprint('contact', __name__)


# catch mailer requests and send them on
@blueprint.route('/', methods=['GET','POST'])
def mailer():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        try:
            if request.values.get('message',False) and not request.values.get('not',False):
                util.send_mail(
                    [app.config['ADMIN_NAME'] + ' <' + app.config['ADMIN_EMAIL'] + '>'],
                    request.values.get('email',app.config['ADMIN_NAME'] + ' <' + app.config['ADMIN_EMAIL'] + '>'),
                    'website enquiry',
                    request.values['message']
                )
                return ''
            else:
                abort(403)
        except:
            abort(500)

 

