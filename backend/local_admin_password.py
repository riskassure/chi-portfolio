"""Store the local admin password with Windows current-user DPAPI encryption."""
import ctypes
from ctypes import wintypes
import getpass
import os
from pathlib import Path
import uuid

PASSWORD_FILE = Path.home()/'.config'/'chi-portfolio'/'local-admin-password.dpapi'


def crypt(data, decrypt=False):
    if os.name != 'nt':
        raise ValueError('Saved local passwords require Windows. Use --session-password instead.')

    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = Blob()
    library = ctypes.WinDLL('crypt32', use_last_error=True)
    function = library.CryptUnprotectData if decrypt else library.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    # Current user scope; no machine-wide flag and no interactive Windows prompts.
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise ValueError('Windows could not unlock/save the local password. Use --reset-password to choose a new one.')
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        if result.data:
            ctypes.memset(result.data, 0, result.size)
            kernel.LocalFree(result.data)


def choose_password():
    password = getpass.getpass('Choose your local admin password (16+ characters): ')
    if len(password) < 16:
        raise ValueError('Use at least 16 characters. No password was changed.')
    if password != getpass.getpass('Confirm local password: '):
        raise ValueError('Passwords did not match. No password was changed.')
    return password


def get_password(*, reset=False, session=False, path=None):
    path = PASSWORD_FILE if path is None else Path(path)
    if session:
        return choose_password()
    if os.name != 'nt':
        raise ValueError('Saved local passwords require Windows. Use --session-password instead.')
    if path.exists() and not reset:
        try:
            password = crypt(path.read_bytes(), decrypt=True).decode('utf-8')
        except (UnicodeError, OSError):
            raise ValueError('Cannot read saved local password. Use --reset-password.') from None
        if len(password) < 16:
            raise ValueError('Invalid saved password. Use --reset-password.')
        print('Using your saved local admin password.')
        return password
    password = choose_password()
    encrypted = crypt(password.encode('utf-8'))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(encrypted)
        if reset:
            temporary.replace(path)
        else:
            # Windows rename refuses overwrite if another setup won the race.
            temporary.rename(path)
    finally:
        temporary.unlink(missing_ok=True)
    print('Local admin password saved with Windows account encryption.')
    return password
