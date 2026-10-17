"""Setup for this laptop only. A deployed connection flow needs separate configuration."""
import os
import re
import secrets

from flask import Blueprint, current_app, jsonify, redirect, render_template_string, request, session
from services.music.spotify_auth import SpotifyAuth, SpotifyError
from config import DB_PATH

spotify_bp = Blueprint("spotify", __name__, url_prefix="/api/music/spotify")
auth = SpotifyAuth()


@spotify_bp.before_request
def local_admin_only():
    if (os.environ.get("FLASK_ENV") == "production" or
            request.remote_addr != "127.0.0.1" or request.host != "127.0.0.1:5001"):
        return jsonify(error="Spotify setup is available only at http://127.0.0.1:5001 on this laptop."), 403
    if request.method == "OPTIONS":
        return "", 204
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
    return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
        <title>Reconnect Spotify</title><h1>Connect Spotify again</h1>
        <p>{{ error }}</p><p>Start a fresh connection in this browser and finish within ten minutes.
        Keep the local server running while you approve access.</p>
        <p><a href="/api/music/spotify/connect">Restart Spotify connection</a></p></html>""",
        error=str(error)), 400


@spotify_bp.route("/connect", methods=["GET", "POST"])
def connect():
    def show_form(error="", status_code=200):
        session.setdefault("spotify_form_token", secrets.token_urlsafe(32))
        return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8">
            <title>Connect Spotify</title><h1>Connect Spotify</h1>
            <p>{{ status }}</p><p>Reads your Spotify top tracks over approximately the last six months. No downloaded history file is needed.</p><p>Enter the Client ID from your Spotify app settings. No Client Secret is needed.</p>
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
    browser_id = session.setdefault("spotify_browser_id", secrets.token_urlsafe(32))
    return redirect(auth.begin(client_id, browser_id))


@spotify_bp.get("/callback")
def callback():
    auth.complete(request.args.get("state", ""), session.get("spotify_browser_id", ""),
                  request.args.get("code", ""), denied="error" in request.args)
    return redirect("/api/music/spotify/connected")


@spotify_bp.get("/connected")
def connected():
    return jsonify(connected=auth.connected(), message="Connection saved. Return to the music page and click Update now to load your top tracks.")


@spotify_bp.get("/status")
def sync_status():
    from services.music.spotify_top import status
    session.setdefault("spotify_update_csrf", secrets.token_urlsafe(32))
    return jsonify(connected=auth.connected(), last_job=status(DB_PATH), update_csrf=session["spotify_update_csrf"],
                   ranking_source="Spotify top tracks", time_range="Last six months", refresh_interval_hours=24)



@spotify_bp.post("/refresh")
def refresh_catalog():
    import sqlite3
    from services.music.spotify_top import run
    data = request.get_json(silent=True)
    expected = session.get("spotify_update_csrf", "")
    supplied = data.get("csrf") if isinstance(data, dict) else None
    if not expected or not isinstance(supplied, str) or not secrets.compare_digest(expected.encode(), supplied.encode()):
        return jsonify(status="error", message="Reload the music page and try again."), 400
    try:
        report = run(DB_PATH, force=True)
    except (OSError, ValueError, sqlite3.Error):
        return jsonify(status="error", message="The local update could not start. Check the backend and try again."), 500
    return jsonify(report), {"ok": 200, "busy": 409, "waiting": 429, "error": 502}[report["status"]]
