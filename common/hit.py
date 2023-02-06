import hashlib
import json

import httpagentparser
from django.core.serializers.json import DjangoJSONEncoder

from common.models import Hit
from easy_log import log


def get_client_ip(request):
    """
    Retrieves the IP address from the request.
    :param request:
    :return:
    """
    return request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get(
        'REMOTE_ADDR')


def make_hit(request, user=None, save=False):
    """
    Creates a hit object
    :param request:
    :param user:
    :param save:
    :return:
    """
    # Retrieves all HTTP headers
    headers = dict()
    for key, value in request.META.items():
        if key.startswith('HTTP'):
            headers[key] = value

    # Gets user from parameter, or creates one
    if user is None:
        user = '##UNKNOWN##'

    # Gets the ip address
    ip = get_client_ip(request)

    # Retrieves the request path
    request_path = request.get_full_path()

    # Creates the hit object
    hit = Hit()
    hit.user_agent = headers.get('HTTP_USER_AGENT', 'Not specified')
    hit.user_id = user
    hit.ip_address = ip
    hit.request_path = request_path
    hit.http_headers = json.dumps(headers, default=DjangoJSONEncoder)

    # Retrieves the OS and browser from the user agent
    try:
        hit.user_os, hit.user_browser = httpagentparser.simple_detect(hit.user_agent)
    except:
        log.exception('Error while parsing user agent.')
        hit.user_os = None
        hit.user_browser = None

    # Saves the hit object
    if save:
        hit.save()

    return hit
