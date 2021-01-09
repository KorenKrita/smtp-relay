import time
import asyncio
import smtplib
from aiosmtpd.controller import Controller

class MailProxyHandler:

    async def handle_DATA(self, server, session, envelope):
        try:
            refused = self._deliver(envelope)
        except smtplib.SMTPRecipientsRefused as e:
            return "553 Recipients refused {}".format(' '.join(refused.keys()))
        except smtplib.SMTPResponseException as e:
            return "{} {}".format(e.smtp_code, e.smtp_error)
        else:
            return '250 OK'

    def authenticator(self,mechanism, login, password):
        if login and password:
            self.login = login.decode()
            self.password = password.decode()
            return True
        return False

    def _deliver(self, envelope):
        refused = {}
        try:
            s = smtplib.SMTP_SSL('smtp.gmail.com')
            s.connect('smtp.gmail.com', 465)
            s.login(self.login, self.password)
            try:
                refused = s.sendmail(
                    envelope.mail_from,
                    envelope.rcpt_tos,
                    envelope.original_content
                )
            finally:
                s.quit()
        except (OSError, smtplib.SMTPException) as e:
            errcode = getattr(e, 'smtp_code', 554)
            errmsg = getattr(e, 'smtp_error', e.__class__)
            raise smtplib.SMTPResponseException(errcode, errmsg.decode())


proxy = MailProxyHandler()

controller = Controller(
    proxy,
    hostname='0.0.0.0',
    port='2525',
    server_kwargs=dict(auth_require_tls=False,auth_required=True,auth_callback=proxy.authenticator)
)

controller.start()
while controller.loop.is_running():
    time.sleep(0.2)