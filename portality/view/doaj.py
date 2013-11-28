from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort
from flask.ext.login import current_user

from portality import models as models
from portality.core import app
from portality import settings

from StringIO import StringIO
import csv
from datetime import datetime

blueprint = Blueprint('doaj', __name__)

@blueprint.route("/")
def home():
    heading_title = 'Heading Title - 100 word example'
    heading_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent arcu tortor, hendrerit eget sapien quis, ultricies commodo diam. Nunc semper magna id urna sollicitudin aliquam. Vivamus in nisi sed tellus blandit varius. Fusce quis lectus turpis. Ut et condimentum libero. Donec orci risus, cursus vel dui a, rhoncus aliquet tellus. Sed dui lacus, convallis ut congue eu, gravida nec leo. Duis vel massa at enim mattis ullamcorper sed varius nulla. Nullam eget leo vel est consequat suscipit. Nulla porttitor dapibus nulla at vulputate. Sed cursus, augue quis rutrum adipiscing, lectus arcu tincidunt arcu, sit amet convallis urna nunc luctus nisi.'
    return render_template('doaj/index.html', heading_title=heading_title, heading_text=heading_text)

@blueprint.route("/search")
def search():
    return ''

@blueprint.route("/about")
def about():
    return render_template('doaj/about.html')

@blueprint.route("/csv")
def csv_data():
    def get_csv_string(csv_row):
        '''
        csv.writer only writes to files - it'd be a lot easier if it
        could give us the string it generates, but it can't. This
        function uses StringIO to capture every CSV row that csv.writer
        produces and returns it.

        :param csv_row: A list of strings, each representing a CSV cell.
            This is the format required by csv.writer .
        '''
        csvstream = StringIO()
        csvwriter = csv.writer(csvstream, quoting=csv.QUOTE_ALL)
        csvwriter.writerow(csv_row)
        csvstring = csvstream.getvalue()
        csvstream.close()
        return csvstring

    journals = models.Journal.query()
    def generate():
        '''Return the CSV header and then all the journals one by one.'''

        '''
        The header will only be generated once. This is because once the
        generator yields a value for the first time, it remembers what
        state its local variables were in. The next time yield is
        called, it can simply resume where it left off. In this
        function, this means that once we get into the loop iterating
        over all the journals, we stay there until we run out of
        journals. So the code before the loop only ever gets executed
        once - the first time the generator returns a value.
        '''
        yield get_csv_string(models.Journal.CSV_HEADER)

        for j in journals:
            jm = models.Journal(**j['_source'])
            yield get_csv_string(jm.csv())

    if journals['hits']['total'] > 0:
        journals = journals['hits']['hits']
    else:
        return 'Cannot find any journals in the DOAJ index. Please report this problem to ' + settings.ADMIN_EMAIL, 500

    attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '.csv'
    r = Response(generate(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=' + attachment_name})
    return r
