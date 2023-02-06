#!/usr/bin/env python
import os
import sys
from os.path import join, dirname

from dotenv import load_dotenv

from easy_log import log

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webserver.settings")

    # Load environment variables
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # Load logging capabilities
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log.add_logfile(join(LOG_DIR, 'server.log'), erase=False)

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
