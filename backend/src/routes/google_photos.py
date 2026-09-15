"""Google Photos connection for the local portfolio administrator."""
import os
import secrets
import re
import sqlite3
from urllib.parse import quote, urlparse

from flask import Blueprint, current_app, jsonify, redirect, render_template_string, render_template, request, session, send_file
from services.photography import google_photos_import as importer
from services.photography.google_photos_auth import GooglePhotosAuth, GooglePhotosError, credentials

google_photos_bp = Blueprint("google_photos", __name__)
auth = GooglePhotosAuth()
BASE = "/api/photography/google"


@google_photos_bp.errorhandler(OSError)
@google_photos_bp.errorhandler(sqlite3.Error)
def storage_failed(error):
    return jsonify(error="Could not save or read the photos. Check local folder permissions and available disk space, then retry."), 500


@google_photos_bp.before_request
def local_admin_only():
    if (os.environ.get("FLASK_ENV") == "production" or
            request.remote_addr != "127.0.0.1" or request.host != "127.0.0.1:5000"):
        return "Google Photos setup is available only on this laptop at 127.0.0.1:5000.", 403
    if request.method == "OPTIONS":
        return "", 204
    if not session.get("is_admin") and request.endpoint != "google_photos.login":
        if request.endpoint in ("google_photos.connect", "google_photos.manage"):
            return redirect(BASE + "/login")
        return "Sign in to the portfolio and restart the Google Photos connection.", 403


@google_photos_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; form-action 'self' https://accounts.google.com; frame-ancestors 'none'"
    return response


@google_photos_bp.errorhandler(GooglePhotosError)
def failed(error):
    if request.path.startswith(BASE + "/picker") or request.path.startswith(BASE + "/drafts"):
        return jsonify(error=str(error)), 400
    return render_template_string("<h1>Google Photos connection</h1><p>{{ error }}</p><a href='{{ url }}'>Try again</a>", error=str(error), url=BASE + "/connect"), 400


def csrf_valid():
    expected = session.get("google_photos_csrf", "")
    return bool(expected) and secrets.compare_digest(expected.encode(), request.form.get("csrf", "").encode())


@google_photos_bp.route(BASE + "/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(BASE + "/connect")
    error = ""
    if request.method == "POST":
        if not csrf_valid():
            error = "The form expired. Try again."
        elif not secrets.compare_digest(request.form.get("password", "").encode(), current_app.config["ADMIN_PASSWORD"].encode()):
            error = "Invalid admin password."
        else:
            session.clear()
            session["is_admin"] = True
            return redirect(BASE + "/connect", code=303)
    session.setdefault("google_photos_csrf", secrets.token_urlsafe(32))
    return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
        <title>Portfolio admin login</title><h1>Connect Google Photos</h1>
        <p>Sign in with your portfolio admin password.</p><p role="alert">{{ error }}</p>
        <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
        <label>Password <input type="password" name="password" autocomplete="current-password" required></label>
        <button>Sign in</button></form></html>""", error=error, csrf=session["google_photos_csrf"]), 400 if error else 200


@google_photos_bp.route(BASE + "/connect", methods=["GET", "POST"])
def connect():
    if request.method == "POST":
        if not csrf_valid():
            raise GooglePhotosError("The form expired. Please try again.")
        browser = secrets.token_urlsafe(32)
        session["google_photos_browser"] = browser
        return redirect(auth.begin(credentials()["client_id"], browser), code=303)
    credentials()
    session.setdefault("google_photos_csrf", secrets.token_urlsafe(32))
    return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
        <title>Connect Google Photos</title><h1>Connect Google Photos</h1>
        <p>{{ status }}</p><p>Authorize access to photos you explicitly select in Google Photos.</p>
        <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
        <button>Continue to Google</button></form></html>""",
        status="A connection is saved. You can reconnect here." if auth.connected() else "Ready to connect your account.",
        csrf=session["google_photos_csrf"])


@google_photos_bp.get("/auth/google/callback")
def callback():
    auth.complete(request.args.get("state", ""), session.pop("google_photos_browser", ""),
                  request.args.get("code", ""), denied="error" in request.args)
    return redirect(BASE + "/connected")


@google_photos_bp.get(BASE + "/connected")
def connected():
    return redirect(BASE + "/manage")


@google_photos_bp.get(BASE + "/status")
def status():
    return jsonify(connected=auth.connected())


@google_photos_bp.get(BASE + "/manage")
def manage():
    session.setdefault("google_photos_csrf", secrets.token_urlsafe(32))
    return render_template("photography/google_photos.html", csrf=session["google_photos_csrf"])


def require_csrf():
    if not csrf_valid():
        raise GooglePhotosError("Your admin session expired. Reload this page.")


def picker_id():
    sid = session.get("google_picker_id")
    if not sid:
        raise GooglePhotosError("Start a new photo selection.")
    return sid


@google_photos_bp.post(BASE + "/picker")
def start_picker():
    require_csrf()
    token = auth.access_token()
    old = session.pop("google_picker_id", None)
    if old:
        try:
            importer.api('sessions/' + quote(old, safe=''), token, 'DELETE')
        except GooglePhotosError:
            pass
    data = importer.api('sessions', token, 'POST', {})
    uri = data.get('pickerUri', '')
    if urlparse(uri).scheme != 'https' or urlparse(uri).hostname != 'photos.google.com' or not data.get('id'):
        raise GooglePhotosError('Google returned an invalid selection session.')
    session['google_picker_id'] = data['id']
    return jsonify(pickerUri=uri.rstrip('/') + '/autoclose', pollingConfig=data.get('pollingConfig', {}))


@google_photos_bp.get(BASE + "/picker")
def poll_picker():
    data = importer.api('sessions/' + quote(picker_id(), safe=''), auth.access_token())
    return jsonify(ready=bool(data.get('mediaItemsSet')), pollingConfig=data.get('pollingConfig', {}))


@google_photos_bp.get(BASE + "/picker/items")
def list_picked():
    items = importer.picked_items(picker_id(), auth.access_token())
    return jsonify(items=[{'id': item['id'], 'name': item.get('mediaFile', {}).get('filename', 'Photo')} for item in items])


@google_photos_bp.post(BASE + "/picker/import")
def import_picked():
    require_csrf()
    token = auth.access_token()
    items = importer.picked_items(picker_id(), token)
    item = next((item for item in items if item['id'] == request.form.get('id')), None)
    if not item:
        raise GooglePhotosError('This photo is not in your Google selection.')
    return jsonify(importer.import_item(item, token))


@google_photos_bp.post(BASE + "/picker/finish")
def finish_picker():
    require_csrf()
    importer.api('sessions/' + quote(picker_id(), safe=''), auth.access_token(), 'DELETE')
    session.pop('google_picker_id', None)
    return jsonify(success=True)


@google_photos_bp.get(BASE + "/drafts")
def list_drafts():
    return jsonify(items=importer.drafts())


@google_photos_bp.get(BASE + "/drafts/<digest>/image")
def draft_image(digest):
    if not re.fullmatch('[a-f0-9]{64}', digest):
        return '', 404
    path = importer.draft_dir() / (digest + '.webp')
    if not path.is_file():
        return '', 404
    return send_file(path, mimetype='image/webp')


@google_photos_bp.post(BASE + "/drafts/<digest>/publish")
def publish_draft(digest):
    require_csrf()
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise GooglePhotosError('Invalid photo.')
    image_id = importer.publish(digest, request.form.get('title', '').strip(), request.form.get('location', '').strip())
    return jsonify(success=True, image_id=image_id)
