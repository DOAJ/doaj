import logging
import logging.handlers
import sys


# just use GMail
class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.
 
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            import string # for tls add this line
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            self.toaddrs + ",",
                            self.getSubject(record),
                            formatdate(), msg)
            if self.username:
                smtp.ehlo() # for tls add this line
                smtp.starttls() # for tls add this line
                smtp.ehlo() # for tls add this line
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def setup_error_logging(app):
    # Custom logging WILL BE IGNORED by Flask if app.debug == True -
    # even if you remove the condition below.
    if app.debug:
        return

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    send_to = app.config.get('ERROR_LOGGING_EMAIL', app.config.get('ADMIN_EMAIL'))
    if send_to and not app.config.get('SUPPRESS_ERROR_EMAILS'):
        if 'ERROR_MAIL_USERNAME' in app.config and 'ERROR_MAIL_PASSWORD' in app.config and 'ERROR_MAIL_HOSTNAME' in app.config:
            import platform
            hostname = platform.uname()[1]

            # We have to duplicate our email config here as we can't import app_email at this point
            mail_handler = TlsSMTPHandler(
                (app.config['ERROR_MAIL_HOSTNAME'], 587),
                'server-error@' + hostname,
                send_to,
                'DOAJ Flask Error',
                credentials=(app.config['ERROR_MAIL_USERNAME'], app.config['ERROR_MAIL_PASSWORD'])
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(formatter)
            app.logger.addHandler(mail_handler)

    # send errors to stderr, supervisord will capture them in the app's
    # error log
    send_errors_to_supervisor = logging.StreamHandler(sys.stderr)
    send_errors_to_supervisor.setLevel(logging.ERROR)
    send_errors_to_supervisor.setFormatter(formatter)
    app.logger.addHandler(send_errors_to_supervisor)
