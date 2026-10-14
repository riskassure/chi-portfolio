"""Reload a verified account webapp and perform an unauthenticated HTTP check."""
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from pythonanywhere_api import HOST, NoRedirects, get_account_info, validate


def domains(settings):
    apps = get_account_info(settings, 'webapps')
    if not isinstance(apps, list):
        raise ValueError('Unexpected webapp list.')
    return sorted({app['domain_name'] for app in apps if isinstance(app, dict)
                   and isinstance(app.get('domain_name'), str)
                   and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}', app['domain_name'])})


def reload_site(settings, domain):
    validate(settings)
    if domain not in domains(settings):
        raise ValueError('Selected website is not in this PythonAnywhere account.')
    request = Request(f"{HOST}/api/v0/user/{settings['username']}/webapps/{domain}/reload/",
                      data=b'', headers={'Authorization': 'Token '+settings['token']}, method='POST')
    try:
        with build_opener(NoRedirects()).open(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError('Reload was not acknowledged.')
    except (HTTPError, URLError, TimeoutError, OSError):
        raise RuntimeError('Reload result is unconfirmed. Files are uploaded; check PythonAnywhere before retrying.') from None


def verify_site(domain):
    if not isinstance(domain, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}', domain):
        raise ValueError('Invalid website domain.')
    # No account token, cookies or private settings are sent to the public site.
    request = Request('https://'+domain+'/', headers={'Cache-Control': 'no-cache'}, method='GET')
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            if response.status != 200 or not response.read(1024):
                raise RuntimeError('Public homepage verification failed.')
    except (HTTPError, URLError, TimeoutError, OSError):
        raise RuntimeError('Public homepage verification failed. Keep the backup and inspect the website/error log.') from None
