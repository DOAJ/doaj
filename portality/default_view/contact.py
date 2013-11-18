'''
A contact-form backend mailer endpoint
'''

from flask import Blueprint, request, abort, render_template, flash

from portality.core import app
import portality.util as util


blueprint = Blueprint('contact', __name__)


# catch mailer requests and send them on
@blueprint.route('/', methods=['GET','POST'])
def mailer():
    if request.method == 'POST':
        try:
            if request.values.get('message',False) and not request.values.get('not',False):
                util.send_mail(
                    [app.config['ADMIN_NAME'] + ' <' + app.config['ADMIN_EMAIL'] + '>'],
                    request.values.get('email',app.config['ADMIN_NAME'] + ' <' + app.config['ADMIN_EMAIL'] + '>'),
                    'website enquiry',
                    request.values['message']
                )
                flash('Thank you very much for you enquiry. We will get back to you as soon as possible.', 'success')
            else:
                flash('Sorry. Your message could not be delivered. Please try again.', 'error')
        except:
            if app.config.get('DEBUG',False):
                flash('Sorry, Your message failed. Probably because debug.', 'error')
            else:
                flash('Sorry. Your message failed. Please try again', 'error')

    return render_template('contact/index.html') 

