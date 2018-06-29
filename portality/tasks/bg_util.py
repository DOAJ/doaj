"""Functionality shared between background tasks"""


def email(data_dir, archv_name):
    """
    Compress and email the reports to the specified email address.
    :param data_dir: Directory containing the reports
    :param archv_name: Filename for the archive and resulting email attachment
    """
    import shutil, os
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
