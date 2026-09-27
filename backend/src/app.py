import os
from flask import Flask, jsonify, request, session, send_from_directory, abort
from functools import wraps
from pathlib import Path
import secrets
import time
from collections import defaultdict, deque
from threading import Lock
from datetime import timedelta
from urllib.parse import urlsplit

app = Flask(__name__, static_folder=None)
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"
PUBLIC_ORIGIN = os.environ.get("PUBLIC_ORIGIN", "").rstrip("/")
secret = os.environ.get("FLASK_SECRET_KEY", "")
password = os.environ.get("ADMIN_PASSWORD", "")
if IS_PRODUCTION:
    origin = urlsplit(PUBLIC_ORIGIN)
    if origin.scheme != "https" or not origin.netloc or origin.path or origin.query or origin.fragment or origin.username:
        raise RuntimeError("PUBLIC_ORIGIN must be the HTTPS origin, without a path.")
    if len(secret) < 32 or len(password) < 16:
        raise RuntimeError("Production requires FLASK_SECRET_KEY (32+ characters) and ADMIN_PASSWORD (16+ characters).")
# Missing local credentials disable login; no published fallback password or secret.
app.secret_key = secret or secrets.token_urlsafe(48)
app.config.update(ADMIN_PASSWORD=password or secrets.token_urlsafe(48),
    SESSION_COOKIE_SECURE=IS_PRODUCTION, SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024)
if not password and not IS_PRODUCTION:
    app.logger.warning("Admin login disabled until ADMIN_PASSWORD is set in the environment.")
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
login_attempts = defaultdict(deque)
login_lock = Lock()

@app.before_request
def protect_requests():
    if request.path == "/api/photography/rotate" and request.method == "POST" and not session.get("is_admin"):
        return jsonify(error="Administrator login required."), 403
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("Origin")
        allowed = {PUBLIC_ORIGIN} if IS_PRODUCTION else {
            "http://127.0.0.1:5000", "http://localhost:5000",
            "http://127.0.0.1:5500", "http://localhost:5500"}
        # Browsers supply Origin for state-changing requests. In production fail closed.
        if (IS_PRODUCTION and not origin) or (origin and origin not in allowed):
            return jsonify(error="Request origin rejected."), 403
    if request.method == "POST" and request.path in {
            "/api/login", "/api/music/spotify/login", "/api/photography/google/login"}:
        # One-process limiter. The documented Waitress deployment uses one process.
        # Do not trust arbitrary X-Forwarded-For headers; the proxy also needs rate limits.
        key = request.remote_addr or "unknown"
        now = time.monotonic()
        with login_lock:
            for old_key in list(login_attempts):
                while login_attempts[old_key] and login_attempts[old_key][0] <= now - 60:
                    login_attempts[old_key].popleft()
                if not login_attempts[old_key]: del login_attempts[old_key]
            attempts = login_attempts[key]
            if len(attempts) >= 5:
                return jsonify(error="Too many login attempts. Try again in one minute."), 429
            attempts.append(now)

@app.route("/")
@app.route("/<path:filename>")
def frontend_file(filename="index.html"):
    if filename.startswith(("api/", "auth/")) or any(part.startswith(".") for part in filename.split("/")):
        abort(404)
    if filename.endswith("/"): filename += "index.html"
    return send_from_directory(FRONTEND, filename)

# ==========================================================================
# 🛡️ REUSABLE SECURITY GATE DECORATOR
# ==========================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin", False):
            return jsonify({"success": False, "message": "Unauthorized access rejected."}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================================
# 🌐 DYNAMIC CORS INTERCEPTOR (CROSS-PORT ROUTING GATE)
# ==========================================================================
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    # Whitelist your local development frontend server ports
    allowed_origins = [] if IS_PRODUCTION else ["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5000", "http://localhost:5000"]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if origin in allowed_origins:
        response.vary.add("Origin")
    return response


# ==========================================================================
# 🔑 CORE AUTHENTICATION ROUTING ENDPOINTS
# ==========================================================================
@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_admin():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    data = request.get_json() or {}
    if isinstance(data, dict) and isinstance(data.get("password"), str) and secrets.compare_digest(data["password"].encode(), app.config["ADMIN_PASSWORD"].encode()):
        session.clear()
        session.permanent = True
        session["is_admin"] = True
        return jsonify({"success": True, "message": "Welcome Admin."})
    return jsonify({"success": False, "message": "Invalid credentials."}), 401

@app.route("/api/logout", methods=["POST"])
def logout_admin():
    session.clear()
    return jsonify({"success": True, "message": "Logged out safely."})

@app.route("/api/session-check", methods=["GET"])
def check_session_status():
    return jsonify({"is_admin": session.get("is_admin", False)})


# ==========================================================================
# 🔌 PLUG-IN MODULE REGISTER MAP (BLUEPRINTS)
# ==========================================================================
from routes.admin_music import music_bp
from routes.admin_photography import photography_bp
from routes.admin_math import math_bp
from routes.music_spotify import spotify_bp
from routes.google_photos import google_photos_bp

app.register_blueprint(music_bp)
app.register_blueprint(photography_bp)
app.register_blueprint(math_bp)
app.register_blueprint(spotify_bp)
app.register_blueprint(google_photos_bp)


# ==========================================================================
# 🚀 APPLICATION LAUNCH ENGINE
# ==========================================================================
if __name__ == "__main__":
    print("\nStarting Unified Local Web App Gateway Server...")
    # debug=True allows hot-reloading when editing backend route structures
    if IS_PRODUCTION:
        raise RuntimeError("Use the production WSGI server, not app.py.")
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
