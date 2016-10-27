from portality import reporting
from portality.lib import dates
import os


def reports(fr, to, outdir):
    print "Saving reports to " + outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    reporting.provenance_reports(fr, to, outdir)
    reporting.content_reports(fr, to, outdir)


def email(data_dir, archv_name):
    """
    Compress and email the reports to the specified email address.
    :param data_dir: Directory containing the reports
    :param archv_name: Filename for the archive and resulting email attachment
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

    parser.add_argument("-f", "--from_date",
                        help="Start date for reporting period (YYYY-MM-DDTHH:MM:SSZ)",
                        default="1970-01-01T00:00:00Z")
    parser.add_argument("-t", "--to_date",
                        help="End date for reporting period (YYYY-MM-DDTHH:MM:SSZ)",
                        default=dates.now())
    parser.add_argument("-o", "--out",
                        help="Output directory into which reports should be made (will be created if it doesn't exist)",
                        default="report_" + dates.now())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    args = parser.parse_args()

    reports(args.from_date, args.to_date, args.out)

    if args.email:
        archive_name = "reports_" + args.from_date + "_to_" + args.to_date
        email(args.out, archive_name)
