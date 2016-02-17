# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
from api_dashboard.celery import app
import logging

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from api_dashboard.settings import EMAIL_SMTP_SERVER, EMAIL_NOTIFY_NAME, DEFAULT_EMAIL_NOTIFY_SUBJECT

logger = logging.getLogger(__name__)


@app.task
def send_mail_by_postfix(mail_to, content_type, content,
                         subject=DEFAULT_EMAIL_NOTIFY_SUBJECT,
                         mail_from=EMAIL_NOTIFY_NAME,
                         server=EMAIL_SMTP_SERVER):
    """
    使用 Postfix 作为 SMTP Server 来发送邮件
    """
    logger.debug('run send_mail_by_postfix')
    if type(mail_to) != list:
        raise TypeError('mail_to is not a list')

    if content_type not in ('plain', 'html'):
        raise ValueError('content_type is not plain or html')

    msg = MIMEMultipart()
    msg['From'] = mail_from
    msg['To'] = COMMASPACE.join(mail_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(content, _subtype=content_type, _charset='utf-8'))

    smtp = smtplib.SMTP(server)
    smtp.sendmail(mail_from, mail_to, msg.as_string())
    smtp.close()
    logger.info('邮件发送成功')
