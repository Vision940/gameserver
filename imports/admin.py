from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    Response
)

from imports.auth import validate_api_req # api validation
from imports import config # server config loader
from imports import db # db connection handling
from imports import users # public user functions


## Globals ##
bp = Blueprint("admin", __name__, url_prefix="/admin")


## Routes ##
@bp.route('/', methods=['POST'])
def admin():
    """
    Route to render admin function to user at runtime
    Takes username and renders appropriate template based on admin status
    """

    data, resp = validate_api_req(request)
    if resp: return resp

    username = data.get('user')

    script = render_template(
        "client/functions/admin",
        admins=config.SERVER_CONFIG.admins,
        user=username
    )

    return Response(script, mimetype="text/plain")


@bp.route('/requests', methods=['POST'])
def requests():
    _, resp = validate_api_req(request, admin_check=True)
    if resp: return resp

    rows = db.fetch_rows(
        """
        SELECT *
        FROM users
        WHERE status = 'requested'
        """
    )

    return jsonify(valid=True, requests=rows), 200


@bp.route('/approve', methods=['POST'])
def approve():
    data, resp = validate_api_req(request, admin_check=True)
    if resp: return resp

    approval_id = data.get("id")
    approver = data.get("user")
    approver_id = users.user_id_from_username(approver)

    row = db.fetch_row(
        """
        UPDATE users
        SET status = 'approved',
            approved_by = %(approved_by)s,
            approved_at = now(),
            updated_at = now()
        WHERE status = 'requested'
          AND id = %(approval_id)s
        RETURNING id, username, status, approved_at
        """,
        {
            "approval_id": approval_id,
            "approved_by": approver_id
        }
    )
    if not row:
        return jsonify(valid=False), 400

    row["approver"] = approver
    return jsonify(valid=True, updated=row), 200


@bp.route('/reject', methods=['POST'])
def reject():
    data, resp = validate_api_req(request, admin_check=True)
    if resp: return resp

    rejection_id = data.get("id")
    rejector = data.get("user")
    rejected_reason = data.get("reason", "Just cause, I guess...") # Reason should always be passed in
    rejector_id = users.user_id_from_username(rejector)

    row = db.fetch_row(
        """
        UPDATE users
        SET status = 'rejected',
            rejected_by = %(rejected_by)s,
            rejected_at = now(),
            rejected_reason = %(rejected_reason)s,
            updated_at = now()
        WHERE status = 'requested'
          AND id = %(rejection_id)s
        RETURNING id, username, status, rejected_reason, rejected_at
        """,
        {
            "rejection_id": rejection_id,
            "rejected_by": rejector_id,
            "rejected_reason": rejected_reason
        }
    )
    if not row:
        return jsonify(valid=False), 400

    row["rejector"] = rejector
    return jsonify(valid=True, updated=row), 200


@bp.route('/ban', methods=['POST'])
def ban():
    data, resp = validate_api_req(request, admin_check=True)
    if resp: return resp

    banned_id = data.get("id")
    banner = data.get("user")
    banned_reason = data.get("reason", "Just cause, I guess...") # Reason should always be passed in
    banner_id = users.user_id_from_username(banner)

    row = db.fetch_row(
        """
        UPDATE users
        SET status = 'banned',
            banned_by = %(banned_by)s,
            banned_at = now(),
            banned_reason = %(banned_reason)s,
            updated_at = now()
        WHERE id = %(banned_id)s and status = 'approved'
        RETURNING id, username, status, banned_reason, banned_at
        """,
        {
            "banned_id": banned_id,
            "banned_by": banner_id,
            "banned_reason": banned_reason
        }
    )
    if not row:
        return jsonify(valid=False), 400

    row["banner"] = banner
    return jsonify(valid=True, updated=row), 200

@bp.route('/info', methods=['POST'])
def info():
    _, resp = validate_api_req(request)
    if resp: return resp

    return jsonify(valid=True, admins=config.SERVER_CONFIG.admins), 200

