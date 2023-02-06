import base64
import hashlib
import imghdr
import os
import queue
import re
import smtplib
import socket
import string
import sys
import time
from collections import deque
from email.mime.image import MIMEImage
from html.parser import HTMLParser
from random import choice

import requests
from contextlib import contextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from os.path import join
from string import Template

import dns.resolver
import pytz
import sendgrid
from sendgrid import Email
from sendgrid.helpers.mail import Content, Attachment
from sendgrid.helpers.mail import Mail

from easy_log import log


@contextmanager
def sender(server_addr, port, use_tls):
    """
    Creates a sender object attached to a given SMTP server.
    :param server_addr:
    :param port:
    :return: Yields a smtp object.
    """
    try:
        log.info('Starting server connection to {}, port {}... Please wait.'.format(server_addr, port))

        # Connecting to SERVER
        smtp = smtplib.SMTP(server_addr, port)

        # TLS mode connection to SERVER
        if use_tls:
            log.info('Trying TLS connection.')
            smtp.starttls()

        log.info('Connection succesful.')
        yield smtp
    except socket.timeout:
        log.critical('Timeout occurred while connecting to the server.')
    except smtplib.SMTPConnectError:
        log.critical('Connection to server error. Aborting.')
    except smtplib.SMTPServerDisconnected:
        log.critical('The connection has been terminated unexpectedly. Server disconnected.')
    except smtplib.SMTPResponseException:
        log.critical(smtplib.SMTPResponseException.smtp_code + ' - ' + smtplib.SMTPResponseException.smtp_error)
    except smtplib.SMTPException as err:
        log.critical('SMTP Exception. - ' + str(err))
    except Exception as err:
        log.critical(
            'You messed it up, check the code. (Hint, probably server and port are not written correctly) - ' + str(
                err))
    finally:
        # Once finished, close connection and quit gracefully.
        try:
            q = smtp.quit()
            print('Connection succesfully terminated.', q)
            log.info('Connection succesfully terminated. - ' + str(q))
        except UnboundLocalError as err:
            print('"smtp" variable is empty, exception raised.', err)
            log.error('"smtp" variable is empty, exception raised. - ' + str(err))


def send_single_email(smtp, from_email, target, mime_message):
    """
    Sends a single email with the SMTP server
    :param smtp:
    :param from_email:
    :param target:
    :param mime_message:
    :return:
    """
    # Try sending the email
    try:
        # Sending email
        smtp.sendmail(from_email, [target], mime_message.as_string())
        log.info(target[:-1] + ' sent succesfully.')

    except smtplib.SMTPHeloError:
        log.critical(target + ' not sent. The server did not reply properly to the HELO greeting.')
    except smtplib.SMTPRecipientsRefused:
        log.critical('The recipient ' + str(
            target).rstrip() + ' was refused. Nobody got the target.')
    except smtplib.SMTPSenderRefused:
        log.critical(target + ' not sent. The server did not accept the from_addr.')
    except:
        log.error(target + ' not sent. Unexpected error: ' + str(sys.exc_info()[0]))
        raise


def send_emails(smtp_server_addr, smtp_port, from_email, target_emails, message, subject, dry_run, use_sendgrid,
                use_bitly, use_tls, wait=0):
    """
    Sends an email to the complete list
    :param smtp_server_addr:
    :param smtp_port:
    :param from_email:
    :param target_emails:
    :param message:
    :param subject:
    :param dry_run:
    :return:
    """

    try:
        if dry_run:
            for target in target_emails:
                email_message = make_mime_email_message(target, subject, from_email, message, use_bitly)
                log_directory = os.environ.get('LOG_DIR', 'logs')
                message_name = 'Message - %s - %s.txt' % (datetime.now(tz=pytz.utc).strftime('%Y%m%d %H%M'), target)
                with open(join(log_directory, message_name), 'w') as output:
                    output.write(email_message.as_string())

                time.sleep(wait)

                log.info('[DRY] Message sent to: %s' % target)
        elif use_sendgrid:
            for target in target_emails:
                email_message = make_sendgrid_email_message(target, subject, from_email, message, use_bitly)
                sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

                response = sg.client.mail.send.post(request_body=email_message.get())
                if response.status_code == 202:
                    log.info('Message sent to: %s' % target)
                else:
                    log.info('Message not sent to: %s (%s)' % (target, response.body))

                time.sleep(wait)
        else:
            # Make queue with target emails
            target_queue = deque(target_emails)
            max_errors = 10
            current_errors = 0

            while len(target_queue) > 0 and current_errors < max_errors:
                try:
                    with sender(smtp_server_addr, smtp_port, use_tls) as smtp:
                        while len(target_queue) > 0:
                            target = target_queue.pop()
                            email_message = make_mime_email_message(target, subject, from_email, message, use_bitly)
                            send_single_email(smtp, from_email, target, email_message)
                            log.info('Message sent to: %s' % target)

                            time.sleep(5 + wait)
                            current_errors = 0
                except Exception as e:
                    current_errors += 1
                    log.critical('Error while sending email (%s)' % (str(e)))


    except RuntimeError as err:
        print('Unexpected error: ', err)
        log.error('Unexpected error: ' + str(err))


def make_email_message(target, subject, message, use_bitly):
    """
    Creates an email message from the template
    :param target:
    :param subject:
    :param message:
    :return:
    """
    # Calculates the MD5 of the email
    hasher = hashlib.md5()
    hasher.update(target.encode('UTF-8'))
    hash = hasher.hexdigest()

    # Mail setup, variable replace
    user = target[0:target.index('@')]

    # Replace data in the message
    template = Template(message)
    final_message = template.safe_substitute(email=target, user=user, hash=hash, subject=subject)

    # Retrieve URLs
    if use_bitly:
        token = os.environ.get('BITLY_API_KEY')
        expression = re.compile('" *(http://.*/h/.*?) *"')
        for match in expression.finditer(final_message):
            url = match.group(1)

            bitly = requests.get('https://api-ssl.bitly.com/v3/shorten',
                                 params={'access_token': token, 'longUrl': url})
            data = bitly.json()
            new_url = data['data']['url']
            # print('%s : %s' % (url, data['data']['url']))
            log.info('Convert address: %s -> %s' % (url, new_url))

            final_message = final_message.replace(url, new_url)

    return final_message


def make_mime_email_message(target, subject, from_email, message, use_bitly):
    """
    Creates a new mime email message with the given data.
    :param target:
    :param subject:
    :param from_email:
    :param message:
    :return:
    """

    # Construct the email with MIME
    final_message = make_email_message(target, subject, message, use_bitly)

    mime_message = MIMEMultipart('alternative')
    body_html = MIMEText(final_message, 'html')
    mime_message['Subject'] = subject
    mime_message['From'] = from_email
    mime_message['To'] = target
    mime_message.attach(body_html)

    return mime_message


def make_sendgrid_email_message(target, subject, from_email, message, use_bitly):
    """
    Creates a new mime email message with the given data.
    :param target:
    :param subject:
    :param from_email:
    :param message:
    :return:
    """

    # Create message
    final_message = make_email_message(target, subject, message, use_bitly)

    # Create sendgrid message
    mail = Mail(
        Email(from_email),
        subject,
        Email(target),
        Content('text/html', final_message)
    )

    return mail


def get_domains_from_list(email_list):
    """
    Retrieves al unique domains from a list of emails
    :param email_list:
    :return:
    """

    domains = set()
    for email in email_list:
        domains.add(email.split('@')[1])

    return sorted(list(domains))


def get_mail_servers_for_domain(domain_name):
    """
    Returns the available resolvers for a domain.
    :param domain_name:
    :return:
    """
    try:
        resolvers = dns.resolver.query(domain_name, 'MX')
        mail_servers = [str(rdata.exchange) for rdata in resolvers]
    except dns.resolver.NoAnswer:
        mail_servers = list()

    return mail_servers


def is_email(email):
    """
    Returns if a parameter is a valid email address or not
    :param email:
    :return:
    """
    # Validate email
    email_parts = parseaddr(email)
    if email_parts[1] == '' or '@' not in email_parts[1]:
        # Email address is invalid
        return False
    else:
        return True
