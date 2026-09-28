"""Import this application from PythonAnywhere's Web-tab WSGI file."""
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
settings_path = Path.home() / '.config' / 'chi-portfolio' / 'hosting.json'
settings = json.loads(settings_path.read_text(encoding='utf-8'))
for key in ('PUBLIC_ORIGIN', 'FLASK_SECRET_KEY', 'ADMIN_PASSWORD'):
    value = settings.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError('Missing hosting setting: ' + key)
    os.environ[key] = value
os.environ['FLASK_ENV'] = 'production'
os.environ['PORTFOLIO_DB_PATH'] = str(root / 'portfolio.db')
os.environ['MATH_DIAGRAM_DIR'] = str(root / 'data' / 'math' / 'diagrams')
sys.path.insert(0, str(root))
from serve import app as application, validate_database
validate_database()
