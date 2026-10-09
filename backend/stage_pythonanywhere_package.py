"""Upload a reviewed ZIP to private staging; never extract, apply or reload it."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener
import uuid
import zipfile

from pythonanywhere_api import HOST, SETTINGS, NoRedirects, validate

MAX_BYTES = 50 * 1024 * 1024


def read_package(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    return validate_package(data)


def validate_package(data):
    if len(data) > MAX_BYTES:
        raise ValueError('Package exceeds the 50 MB staging limit.')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if not members or sum(m.file_size for m in members) > MAX_BYTES:
                raise ValueError('Package is empty or exceeds 50 MB when expanded.')
            names = set()
            for member in members:
                name = member.orig_filename
                parts = PurePosixPath(name).parts
                if (not parts or name.startswith('/') or '\\' in name or ':' in name or '\x00' in name
                        or '..' in parts or any(p.startswith('.') for p in parts)
                        or name.casefold() in names
                        or stat.S_ISLNK(member.external_attr >> 16)
                        or member.flag_bits & 1):
                    raise ValueError('Package contains unsafe, duplicate or encrypted paths.')
                names.add(name.casefold())
                if (Path(name).suffix.lower() in ('.db', '.sqlite', '.sqlite3', '.pem', '.key')
                        or parts[-1].lower() in ('hosting.json', 'pythonanywhere-api.json')):
                    raise ValueError('Do not stage databases or private settings in update packages.')
            if archive.testzip() is not None:
                raise ValueError('Package checksum validation failed.')
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError):
        raise ValueError('A valid, unencrypted ZIP package is required.') from None
    return data


def stage(settings, package):
    validate(settings)
    data = read_package(package)
    digest = hashlib.sha256(data).hexdigest()
    remote = f"/home/{settings['username']}/chi-portfolio-staging/{uuid.uuid4().hex}/package.zip"
    url = f"{HOST}/api/v0/user/{settings['username']}/files/path{remote}"
    headers = {'Authorization': 'Token ' + settings['token']}
    opener = build_opener(NoRedirects())
    posted = False
    try:
        # The API overwrites existing paths: refuse a collision before posting.
        try:
            with opener.open(Request(url, headers=headers), timeout=30):
                raise ValueError('Staging destination already exists. Nothing uploaded.')
        except HTTPError as error:
            if error.code != 404:
                raise
        boundary = uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="content"; '
                'filename="package.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()
        body += data + f'\r\n--{boundary}--\r\n'.encode()
        upload_headers = dict(headers, **{'Content-Type': f'multipart/form-data; boundary={boundary}'})
        posted = True
        with opener.open(Request(url, data=body, headers=upload_headers, method='POST'), timeout=120) as response:
            if response.status != 201:
                raise RuntimeError('Upload did not report creation of a new file.')
        with opener.open(Request(url, headers=headers), timeout=120) as response:
            received = response.read(MAX_BYTES + 1)
        if hashlib.sha256(received).hexdigest() != digest:
            raise RuntimeError('Uploaded package verification failed.')
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError):
        state = 'An unverified upload may remain at' if posted else 'No upload was attempted at'
        raise RuntimeError(f'Staging failed. {state} {remote}. The live site was not changed.') from None
    return remote, digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path, help='ZIP package whose contents you have reviewed')
    args = parser.parse_args()
    try:
        settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
        remote, digest = stage(settings, args.package)
        print('Uploaded and verified package:', remote)
        print('SHA-256:', digest)
        print('Staging only. Nothing extracted or applied; the live website and database are unchanged.')
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error))
    except OSError:
        raise SystemExit('Unable to read the package or private API settings. Check paths and permissions.')
