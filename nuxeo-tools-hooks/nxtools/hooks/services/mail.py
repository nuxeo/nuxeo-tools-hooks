from email.mime.text import MIMEText

from smtplib import SMTP, SMTP_PORT


class EmailService(object):

    def __init__(self, host, port=SMTP_PORT):
        self._smtp = SMTP()
        self._host = host
        self._port = port

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
