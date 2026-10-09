"""Private token setup and read-only PythonAnywhere API connection check."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, build_opener

SETTINGS = Path.home()/'.config'/'chi-portfolio'/'pythonanywhere-api.json'
HOST = 'https://www.pythonanywhere.com'


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the account token to a redirected destination.


def validate(settings):
    if not isinstance(settings,dict):
        raise ValueError('Invalid API settings.')
    if not re.fullmatch(r'[A-Za-z0-9_]+',settings.get('username','')):
        raise ValueError('Invalid account username.')
    token=settings.get('token')
    if not isinstance(token,str) or not token or any(c.isspace() for c in token):
        raise ValueError('Invalid API token. Run setup again with the token from PythonAnywhere.')
    return settings


def get_account_info(settings, endpoint):
    validate(settings)
    if endpoint not in ('cpu','webapps'):
        raise ValueError('This connection checker only supports read-only account checks.')
    url=f"{HOST}/api/v0/user/{settings['username']}/{endpoint}/"
    request=Request(url,headers={'Authorization':'Token '+settings['token'],'Accept':'application/json'},method='GET')
    try:
        with build_opener(NoRedirects()).open(request,timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        messages={401:'Authentication failed. Check or regenerate your API token.',
                  403:'Access denied. Check the account username and API token.',
                  429:'API rate limit reached. Wait a minute before retrying.'}
        raise RuntimeError(messages.get(error.code,f'API returned HTTP {error.code}. No changes were made.')) from None
    except (URLError,TimeoutError,OSError):
        raise RuntimeError('Could not connect to PythonAnywhere. Check your network and try again.') from None
    except (ValueError,UnicodeError):
        raise RuntimeError('PythonAnywhere returned an unexpected response.') from None


def setup():
    if SETTINGS.exists():
        raise ValueError('API settings already exist. Use check, or move the old private settings file before setting up again.')
    print('Use your PythonAnywhere API token, not either of your passwords.')
    username=input('PythonAnywhere username [cwoo]: ').strip() or 'cwoo'
    token=getpass.getpass('Paste API token (hidden): ').strip()
    settings=validate(dict(username=username,token=token))
    # Verify before saving; only GET requests are used.
    get_account_info(settings,'cpu')
    SETTINGS.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(SETTINGS,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:
        json.dump(settings,stream)
    print('Connection verified. Token saved privately outside the repository:')
    print(SETTINGS)
    print('The token is stored as plaintext in this private user file. Do not share it.')


def check():
    if not SETTINGS.is_file():
        raise ValueError('No API settings found. Run this program with setup first.')
    settings=validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
    cpu=get_account_info(settings,'cpu')
    apps=get_account_info(settings,'webapps')
    if not isinstance(cpu,dict) or not isinstance(apps,list):
        raise ValueError('Unexpected account response. No changes were made.')
    print('API connection successful for account:',settings['username'])
    print('Daily CPU allowance:',cpu.get('daily_cpu_limit_seconds','unknown'),'seconds')
    print('Websites:')
    for app in apps:
        if isinstance(app,dict): print(' -',app.get('domain_name','(unnamed)'))
    print('Read-only check complete. No files or website settings were changed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['setup','check'])
    args=parser.parse_args()
    try:
        setup() if args.action=='setup' else check()
    except (ValueError,RuntimeError,OSError):
        # Never print raw settings, server bodies or request headers.
        import sys
        error=sys.exc_info()[1]
        if isinstance(error,(ValueError,RuntimeError)):
            raise SystemExit(str(error))
        raise SystemExit('Unable to read or save private API settings. Check file permissions.')
