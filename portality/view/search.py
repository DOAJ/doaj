'''
A search page that renders a template that includes a facetview search
'''

from flask import Blueprint, render_template

from portality.core import app
import portality.util as util


blueprint = Blueprint('search', __name__)


# catch mailer requests and send them on
@blueprint.route('/')
def search():
    return render_template('search.html')
 

