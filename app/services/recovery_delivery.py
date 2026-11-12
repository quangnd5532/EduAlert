"""Deliver recovery codes through operator-configured mail and SMS services.

No console/outbox fallback: never report successful delivery without a transport.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlparse

import httpx


class DeliveryError(Exception):
    pass


def available(channel):
    if channel == 'email':
        return bool(os.getenv('EDUALERT_SMTP_HOST') and os.getenv('EDUALERT_MAIL_FROM'))
    return bool(urlparse(os.getenv('EDUALERT_SMS_URL', '')).scheme == 'https'
                and os.getenv('EDUALERT_SMS_TOKEN'))


def send_code(channel, destination, code):
    if not available(channel):
        raise DeliveryError('Recovery transport is not configured')
    message = f'Mã xác minh EduAlert của bạn là {code}. Mã có hiệu lực trong 10 phút. Không chia sẻ mã này với bất kỳ ai.'
    try:
        if channel == 'email':
            mail = EmailMessage()
            mail['Subject'] = 'EduAlert — Mã xác minh khôi phục mật khẩu'
            mail['From'] = os.environ['EDUALERT_MAIL_FROM']
            mail['To'] = destination
            mail.set_content('Xin chào,\n\n' + message + '\n\nNếu bạn không yêu cầu khôi phục mật khẩu, hãy bỏ qua email này.\nEduAlert')
            use_ssl = os.getenv('EDUALERT_SMTP_SSL', 'false').lower() == 'true'
            transport = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
            port = int(os.getenv('EDUALERT_SMTP_PORT', '465' if use_ssl else '587'))
            options = {'context': ssl.create_default_context()} if use_ssl else {}
            with transport(os.environ['EDUALERT_SMTP_HOST'], port, timeout=10, **options) as smtp:
                if not use_ssl:
                    smtp.starttls(context=ssl.create_default_context())
                if os.getenv('EDUALERT_SMTP_USER'):
                    smtp.login(os.environ['EDUALERT_SMTP_USER'], os.environ['EDUALERT_SMTP_PASSWORD'])
                if smtp.send_message(mail):
                    raise DeliveryError('Recipient refused')
        else:
            # The gateway adapts this contract to the institution's SMS provider.
            with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
                response = client.post(os.environ['EDUALERT_SMS_URL'],
                    headers={'Authorization': 'Bearer ' + os.environ['EDUALERT_SMS_TOKEN']},
                    json={'to': destination, 'message': message})
                if not 200 <= response.status_code < 300:
                    raise DeliveryError('SMS gateway refused the request')
    except (OSError, ValueError, KeyError, smtplib.SMTPException, httpx.HTTPError) as exc:
        # Do not expose transport credentials, addresses or codes to the UI/logs.
        raise DeliveryError('Recovery delivery failed') from exc
