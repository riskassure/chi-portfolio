import os
from flask import Flask, jsonify, request, session
from functools import wraps

app = Flask(__name__)

# ==========================================================================
# 🛠️ DYNAMIC ENVIRONMENT & COOKIE SECURITY CONFIGURATION
# ==========================================================================
# Automatically detects if it's running live on a production website.
# On your local machine, this defaults to False.
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"

# Fallback string key used locally; will use an environment variable on the live host.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "classical_music_portfolio_secret_key_pass")

# SAFE: Relaxed locally so unencrypted HTTP cookies work. 
# SMART: Automatically hardens to True/None when deployed to a live HTTPS server!
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if IS_PRODUCTION else 'Lax'

# Master password configuration (Easy to move to database/hashes later)
ADMIN_PASSWORD = "SuperSecretPassword123"


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
    allowed_origins = ["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5000"]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    return response


# ==========================================================================
# 🔑 CORE AUTHENTICATION ROUTING ENDPOINTS
# ==========================================================================
@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_admin():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    data = request.get_json() or {}
    if data.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return jsonify({"success": True, "message": "Welcome Admin."})
    return jsonify({"success": False, "message": "Invalid credentials."}), 401

@app.route("/api/logout", methods=["POST"])
def logout_admin():
    session.pop("is_admin", None)
    return jsonify({"success": True, "message": "Logged out safely."})

@app.route("/api/session-check", methods=["GET"])
def check_session_status():
    return jsonify({"is_admin": session.get("is_admin", False)})


# ==========================================================================
# 🔌 PLUG-IN MODULE REGISTER MAP (BLUEPRINTS)
# ==========================================================================
from routes.admin_music import music_bp
from routes.admin_photography import photography_bp

app.register_blueprint(music_bp)
app.register_blueprint(photography_bp)


# ==========================================================================
# 🚀 APPLICATION LAUNCH ENGINE
# ==========================================================================
if __name__ == "__main__":
    print("\nStarting Unified Local Web App Gateway Server...")
    # debug=True allows hot-reloading when editing backend route structures
    app.run(host="127.0.0.1", port=5000, debug=True)