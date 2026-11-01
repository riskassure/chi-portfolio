"""Admin download of the visitor log as a CSV file; reads the access logs, changes nothing."""
from datetime import datetime, timezone
from flask import Blueprint, Response, jsonify, request
from services import visitor_log

visitors_bp = Blueprint('visitors', __name__)


@visitors_bp.get('/api/admin/visitor-log.csv')
def download_visitor_log():
    from app import admin_required, client_address

    @admin_required
    def build():
        path = visitor_log.default_log_path()
        files = visitor_log.log_files(path) if path else []
        if not files:
            return jsonify(success=False, message=f'No access log found at {path}.'), 404
        pages_only = request.args.get('all') != '1'
        try:
            text, counts = visitor_log.build_csv(
                visitor_log.read_lines(files), my_address=client_address(),
                ignore=visitor_log.ignored_addresses(), locate=visitor_log.open_locator(),
                pages_only=pages_only)
        except OSError as error:
            return jsonify(success=False, message=f'Could not read the access log: {error}'), 500
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        name = f"visitors-{'pages' if pages_only else 'all'}-{stamp}.csv"
        response = Response(text, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename="{name}"'
        response.headers['X-Visitor-Log-Counts'] = ', '.join(f'{k}={v}' for k, v in sorted(counts.items()))
        return response
    return build()
