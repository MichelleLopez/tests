# coding=utf-8
import os

# Django imports
import subprocess

import django
import re

import sys

from mail_sender.sender import is_email

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webserver.settings')
django.setup()

from common.models import Target

# Other imports
import hashlib
import sqlite3
from email.utils import parseaddr
from os.path import join, dirname

import click
from dotenv import load_dotenv

from easy_log import log
from mail_sender import sender

# Global variables
dry_run = False


@click.group()
@click.option('--dry', is_flag=True, help="Makes a dry run of the command.")
def cli(dry):
    """
    Manages the phishing project for administrating targets and launching the webserver handler.
    """
    if dry:
        global dry_run
        dry_run = True

    return


@click.command()
@click.argument('input_file', type=click.File('rb'))
def add_emails(input_file):
    """
    Adds the specified emails in the list of targets.
    """
    global dry_run

    # Statistics
    invalid_emails = 0
    added_emails = 0
    duplicate_emails = 0

    # Read emails from input and add them to the database without duplicates
    for line in input_file:
        email = line.decode('ASCII').strip()

        # Validate email
        if not is_email(email):
            log.error("Couldn't parse email: %s" % email)
            invalid_emails += 1
            continue

        # Check for duplicate
        if Target.objects.filter(email=email).exists():
            log.warning('Email already in database: %s' % email)
            duplicate_emails += 1
            continue

        # Create hash
        hasher = hashlib.md5()
        hasher.update(email.encode('ASCII'))
        hash = hasher.hexdigest()

        # Make target
        new_target = Target()
        new_target.email = email
        new_target.user_id = hash
        added_emails += 1

        if not dry_run:
            new_target.save()

    # Print statistics
    txt_dry = '[DRY] ' if dry_run else ''
    log.info('%sAdded emails: %d' % (txt_dry, added_emails))
    log.info('%sDuplicate emails: %d' % (txt_dry, duplicate_emails))
    log.info('%sInvalid emails: %d' % (txt_dry, invalid_emails))


def abort_if_false(ctx, param, value):
    """
    Aborts the current execution.
    :param ctx:
    :param param:
    :param value:
    :return:
    """
    if not value:
        ctx.abort()


@click.command()
@click.option('--yes', is_flag=True, expose_value=False,
              callback=abort_if_false,
              help="Won't prompt for confirmation.",
              prompt='Are you sure you want to delete the emails?')
@click.option('--delete-list', '-d', type=click.File('rb'), help='File with list of emails to delete')
@click.option('--regex', '-r', type=str, help='Deletes emails that match the given regular expression')
@click.option('--verbose', '-v', is_flag=True, default=False)
def delete_emails(delete_list, regex, verbose):
    """
    Clears all emails in the database. If a list is given then only the emails on the list are deleted.
    """
    global dry_run
    txt_dry = '[DRY] ' if dry_run else ''

    # Get emails from list
    delete_list_set = set()
    if delete_list:
        for line in delete_list:
            email = line.decode('ASCII').strip()
            try:
                t = Target.objects.get(email=email)
                delete_list_set.add(t.pk)
            except Target.DoesNotExist:
                continue
    else:
        delete_list_set.update([t.pk for t in Target.objects.all()])

    # Get emails from regex
    regex_set = set()
    if regex:
        regex_set.update([t.pk for t in Target.objects.filter(email__regex=regex)])
    else:
        regex_set.update([t.pk for t in Target.objects.all()])

    # Gets final set to delete
    id_to_delete = delete_list_set & regex_set

    if verbose:
        for id in id_to_delete:
            to_delete = Target.objects.get(pk=id)
            log.info('%sDeleted email: %s' % (txt_dry, to_delete.email))
            if not dry_run:
                to_delete.delete()
    else:
        if not dry_run:
            Target.objects.filter(pk__in=id_to_delete).delete()

    # Prints results
    log.info('%sDeleted %d email(s)' % (txt_dry, len(id_to_delete)))


@click.command()
@click.option('--hash', is_flag=True, default=False)
def show_emails(hash):
    """
    Prints all the emails in the database. If --hash is specified then email,hash tuples are returned.
    """
    targets = Target.objects.all()
    for t in targets:
        if hash:
            click.echo('%s,%s' % (t.email, t.user_id))
        else:
            click.echo(t.email)


@click.command()
@click.option('--email-server', '-m', help='Default email server to use.')
@click.option('--port', '-p', help='Select port for mail server.', default=25)
@click.option('--regex', '-r', help='Sends the message only to the targets that match the regular expression.')
@click.option('--use-sendgrid', help='Uses SENDGRID instead of default mail client.', is_flag=True)
@click.option('--wait', help='Sets wait time in seconds between emails.', type=int)
@click.option('--bitly', help='Uses bitly to mask IP addresses', is_flag=True)
@click.option('--tls', help='Put the SMTP connection in TLS (Transport Layer Security) mode.', is_flag=True)
@click.argument('from_email', type=str)
@click.argument('subject', type=str)
@click.argument('content', type=click.File('rb'))

def send_emails(email_server, port, regex, use_sendgrid, wait, bitly, tls, from_email, subject, content):
    """
    Sends the given email to the complete list. If --test is set then the email is only sent to the given user.
    """
    global dry_run

    # Read message content
    message = ""
    for line in content:
        message += line.decode('UTF-8')

    # Select the emails
    if regex:
        targets = list(Target.objects.filter(email__regex=regex))
    else:
        targets = list(Target.objects.all())

    if len(targets) == 0:
        log.error("There are no available targets for email sending. Use add_emails first.")
        return

    # Retrieve domains from the emails
    domains = sender.get_domains_from_list([t.email for t in targets])
    selected_domain = 0
    if len(domains) > 1:
        # Select destination domain
        click.echo('There are multiple available domains:')
        for i in range(len(domains)):
            click.echo('\t[%d] %s' % (i, domains[i]))
        selected_domain = click.prompt('Select the target domain', type=click.IntRange(0, len(domains) - 1))
    log.info('Selected domain %s' % domains[selected_domain])

    # Select a mail server for the domain
    selected_server = 0
    if email_server:
        available_mail_servers = [email_server]
    elif use_sendgrid:
        available_mail_servers = ['sendgrid']
    else:
        available_mail_servers = sender.get_mail_servers_for_domain(domains[selected_domain])

        if len(available_mail_servers) == 0:
            log.error('There is no email server for domain %s' % domains[selected_domain])
            if not click.confirm('Continue anyway using the domain as mail server address?'):
                exit(-1)
            else:
                available_mail_servers.append(domains[selected_domain])

        elif len(available_mail_servers) == 1:
            log.info('Using mail server: %s' % available_mail_servers[selected_server])

        elif len(available_mail_servers) > 1:
            # Select resolver for mail sending
            click.echo('There are multiple available mail servers for the domain:')
            for i in range(len(available_mail_servers)):
                click.echo('\t[%d] %s' % (i, available_mail_servers[i]))
            selected_server = click.prompt('Select the target server:',
                                           type=click.IntRange(0, len(available_mail_servers) - 1))

    log.info('Selected server %s' % available_mail_servers[selected_server])

    # Select only the emails that match the domain
    target_email_list = [t.email for t in targets if t.email.endswith(domains[selected_domain])]

    # Send the emails
    sender.send_emails(available_mail_servers[selected_server].rstrip('.'),
                       port,
                       from_email,
                       target_email_list,
                       message,
                       subject,
                       dry_run,
                       use_sendgrid,
                       bitly,
                       tls,
                       wait)

@click.command()
@click.option('--address', '-s', type=str, help="Server address to use for django.", default='127.0.0.1')
@click.option('--port', '-p', type=str, help="Server port for django.", default='8000')
def start_server(address, port):
    """
    Start django server with the provided parameters.
    """
    server = "%s:%s" % (address, port)
    if sys.platform == 'win32':
        # Windows start
        subprocess.Popen(["python", "manage.py", "runserver", server], shell=True)
    else:
        # Gunicorn start
        subprocess.Popen(["gunicorn", "webserver.wsgi", server], shell=True)


if __name__ == '__main__':
    # Load environment variables
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # Add log
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log.add_logfile(join(LOG_DIR, 'main.log'), erase=False)

    cli.add_command(add_emails)
    cli.add_command(delete_emails)
    cli.add_command(show_emails)
    cli.add_command(send_emails)
    cli.add_command(start_server)

    cli()
