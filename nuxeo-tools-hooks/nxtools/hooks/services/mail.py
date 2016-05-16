from email.mime.text import MIMEText
from nxtools import ServiceContainer, services
from nxtools.hooks.services.config import Config
from smtplib import SMTP, SMTP_PORT


@ServiceContainer.service
class EmailService(object):

    def __init__(self):
        config = services.get(Config)

        self._smtp = SMTP()
        self._host = config.get(self.config_section, "host", "localhost")
        self._port = config.get(self.config_section, "port", SMTP_PORT)

    @property
    def config_section(self):
        return type(self).__name__

    def sendemail(self, email):
        """
        :type email: nxtools.hooks.entities.mail.Email
        """
        mail = MIMEText(email.body, "plain", "UTF-8")
        mail.add_header("From", email.sender)
        mail.add_header("To", email.to)
        mail.add_header("Reply-To", email.reply_to)
        mail.add_header("Subject", email.subject)

        self._smtp.connect(self._host, self._port)
        self._smtp.sendmail(email.sender, email.to, mail.as_string())
        self._smtp.quit()
