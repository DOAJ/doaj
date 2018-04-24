""" Creates a CSV of publisher email addresses """

import os, codecs
import esprit
from portality.core import app
from portality.models import Account, Journal
from portality.clcsv import UnicodeWriter
from portality.lib import dates

source = {
    "host": app.config.get("ELASTIC_SEARCH_HOST"),
    "index": app.config.get("ELASTIC_SEARCH_DB")
}

conn = esprit.raw.Connection(source.get("host"), source.get("index"))

publisher_query = {
    'query': {
        'term': {
            'role.exact': 'publisher'
        }
    }
}


def publishers_with_journals():
    """ Get accounts for all publishers with journals in the DOAJ """
    for acc in esprit.tasks.scroll(conn, 'account', q=publisher_query):
        account = Account(**acc)
        journal_ids = account.journal
        if journal_ids is not None:
            for j in journal_ids:
                journal = Journal.pull(j)
                if journal is not None and journal.is_in_doaj():
                    yield account
                    break


def email(data_dir, archv_name):
    """
    Compress and email the reports to the specified email address.
    :param data_dir: Directory containing the reports
    :param archv_name: Filename for the archive and resulting email attachment
    FIXME: This is identical to email() in tasks/reports.py, which has already been refactored in a different branch.
    """
    import shutil
    from portality import app_email
    from portality.core import app

    email_to = app.config.get('REPORTS_EMAIL_TO', ['feedback@doaj.org'])
    email_from = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    email_sub = app.config.get('SERVICE_NAME', '') + ' - generated {0}'.format(archv_name)
    msg = "Attached: {0}.zip\n".format(archv_name)

    # Create an archive of the reports
    archv = shutil.make_archive(archv_name, "zip", root_dir=data_dir)

    # Read the archive to create an attachment, send it with the app email
    with open(archv) as f:
        dat = f.read()
        attach = [app_email.make_attachment(filename=archv_name, content_type='application/zip', data=dat)]
        app_email.send_mail(to=email_to, fro=email_from, subject=email_sub, msg_body=msg, files=attach)

    # Clean up the archive
    os.remove(archv)


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out",
                        help="Output directory into which reports should be made (will be created if it doesn't exist)",
                        default="publisher_emails_" + dates.today())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    args = parser.parse_args()

    outdir = args.out
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    filename = "publisher_emails_in_doaj_" + dates.today() + ".csv"
    outfile = os.path.join(outdir, filename)
    with codecs.open(outfile, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["Account ID", "Email Address"])
        for p in publishers_with_journals():
            writer.writerow([p.id, p.email])

    if args.email:
        email(outdir, "publisher_emails_in_doaj_" + dates.today())
