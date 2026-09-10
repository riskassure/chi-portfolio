"""Setup for this laptop only. A deployed connection flow needs separate configuration."""
import os
import re
import secrets

from flask import Blueprint, current_app, jsonify, redirect, render_template_string, request, session
from services.music.spotify_auth import SpotifyAuth, SpotifyError

spotify_bp = Blueprint("spotify", __name__, url_prefix="/api/music/spotify")
auth = SpotifyAuth()


@spotify_bp.before_request
def local_admin_only():
    if (os.environ.get("FLASK_ENV") == "production" or
            request.remote_addr != "127.0.0.1" or request.host != "127.0.0.1:5000"):
        return jsonify(error="Spotify setup is available only at http://127.0.0.1:5000 on this laptop."), 403
    if not session.get("is_admin") and request.endpoint != "spotify.login":
        if request.endpoint == "spotify.connect" and request.method == "GET":
            return redirect("/api/music/spotify/login")
        return "Your admin session is missing. Open /api/music/spotify/connect to sign in and restart the connection.", 403


@spotify_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect("/api/music/spotify/connect")
    error = ""
    status = 200
    if request.method == "POST":
        expected = session.get("spotify_login_csrf", "")
        if not expected or not secrets.compare_digest(expected, request.form.get("csrf", "")):
            error = "Your login form expired or cookies are unavailable. Please try again with cookies enabled."
            status = 400
        elif not secrets.compare_digest(request.form.get("password", "").encode(),
                                        current_app.config["ADMIN_PASSWORD"].encode()):
            error = "Invalid admin password."
            status = 401
        else:
            session.clear()
            session["is_admin"] = True
            return redirect("/api/music/spotify/connect", code=303)
    session.setdefault("spotify_login_csrf", secrets.token_urlsafe(32))
    return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
        <title>Admin login</title><h1>Admin login</h1>
        <p>Sign in with your portfolio admin password to connect Spotify.</p>
        <p>{{ error }}</p><form method="post">
        <input type="hidden" name="csrf" value="{{ csrf }}">
        <label>Admin password <input type="password" name="password" autocomplete="current-password" required></label>
        <button type="submit">Sign in</button></form></html>""",
        csrf=session["spotify_login_csrf"], error=error), status


@spotify_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; form-action 'self' https://accounts.spotify.com; frame-ancestors 'none'"
    return response


@spotify_bp.errorhandler(SpotifyError)
def connection_error(error):
    return str(error), 400


@spotify_bp.route("/connect", methods=["GET", "POST"])
def connect():
    def show_form(error="", status_code=200):
        session.setdefault("spotify_form_token", secrets.token_urlsafe(32))
        return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
            <title>Connect Spotify</title><h1>Connect Spotify</h1>
            <p>{{ status }}</p><p>Enter the Client ID from your Spotify app settings. No Client Secret is needed.</p>
            <p role="alert">{{ error }}</p>
            <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
            <label>Client ID <input name="client_id" value="{{ client_id }}" required pattern="[a-fA-F0-9]{32}" size="36"></label>
            <button type="submit">Continue to Spotify</button></form></html>""",
            error=error, client_id=request.form.get("client_id", ""),
            csrf=session["spotify_form_token"],
            status="A Spotify connection is saved. You can reconnect below." if auth.connected() else "Spotify is not connected yet."), status_code
    if request.method == "GET":
        return show_form()
    expected = session.get("spotify_form_token", "")
    if not expected or not secrets.compare_digest(expected, request.form.get("csrf", "")):
        return show_form("Your form was out of date. Please click Continue to Spotify again.", 400)
    client_id = request.form.get("client_id", "").strip()
    if not re.fullmatch(r"[a-fA-F0-9]{32}", client_id):
        return show_form("Enter the 32-character Client ID from your Spotify app settings.", 400)
    browser_id = secrets.token_urlsafe(32)
    session["spotify_browser_id"] = browser_id
    return redirect(auth.begin(client_id, browser_id))


@spotify_bp.get("/callback")
def callback():
    auth.complete(request.args.get("state", ""), session.pop("spotify_browser_id", ""),
                  request.args.get("code", ""), denied="error" in request.args)
    return redirect("/api/music/spotify/connected")


@spotify_bp.get("/connected")
def connected():
    return jsonify(connected=auth.connected(), message="Connection saved locally. Open /api/music/spotify/status for refresh status.")


@spotify_bp.get("/status")
def sync_status():
    from contextlib import closing
    import json
    import sqlite3
    from services.music.spotify_auth import token_path
    path = token_path().parent / "spotify-history.db"
    report = None
    if path.exists():
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='sync_state'").fetchone():
                row = db.execute("SELECT value FROM sync_state WHERE key='job_status'").fetchone()
                report = json.loads(row[0]) if row else None
    return jsonify(connected=auth.connected(), last_job=report,
                   counting_rule="Only export records with at least 30 seconds count. Recent API events await duration verification.")
