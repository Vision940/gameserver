from flask import (
    render_template
)

from server import config
from server import db

from server.api.auth import validate_api_req
from server.api.handlers.registry import handles
from server.api.requests.admin import (
    AdminApproveReq,
    AdminRejectReq,
    AdminBanReq,
    AdminQueryReq,
    AdminRequestsReq,
    AdminInfoReq
)
from server.api.responses.admin import (
    AdminUpdateResp,
    AdminRequestsResp,
    AdminQueryResp,
    AdminInfoResp
)


@handles(AdminApproveReq)
def approve(req: AdminApproveReq) -> ApiResp:
    resp = validate_api_req(req, admin_check=True)
    if resp: return resp

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
            "approval_id": req.id,
            "approved_by": req.userId
        }
    )
    if not row:
        return AdminUpdateResp(valid=False, code=400)

    row["approver"] = req.user
    return AdminUpdateResp(updated=row)


@handles(AdminRejectReq)
def reject(req: AdminRejectReq) -> ApiResp:
    resp = validate_api_req(req, admin_check=True)
    if resp: return resp

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
            "rejection_id": req.id,
            "rejected_by": req.userId,
            "rejected_reason": req.reason
        }
    )
    if not row:
        return AdminUpdateResp(valid=False, code=400)

    row["rejector"] = req.user
    return AdminUpdateResp(updated=row)


@handles(AdminBanReq)
def ban(req: AdminBanReq) -> ApiResp:
    resp = validate_api_req(req, admin_check=True)
    if resp: return resp

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
            "banned_id": req.id,
            "banned_by": req.userId,
            "banned_reason": req.reason
        }
    )
    if not row:
        return AdminUpdateResp(valid=False, code=400)

    row["banner"] = req.user
    return AdminUpdateResp(updated=row)


@handles(AdminQueryReq)
def is_admin(req: AdminQueryReq) -> ApiResp:
    """
    Route to render admin function to user at runtime
    Takes username and renders appropriate template based on admin status
    """

    resp = validate_api_req(req)
    if resp: return resp

    script = render_template(
        "client/functions/admin",
        admins=config.SERVER_CONFIG.admins,
        user=req.user
    )

    return AdminQueryResp(text=script)


@handles(AdminRequestsReq)
def requests(req: AdminRequestsReq) -> ApiResp:
    resp = validate_api_req(req, admin_check=True)
    if resp: return resp

    rows = db.fetch_rows(
        """
        SELECT *
        FROM users
        WHERE status = 'requested'
        """
    )

    return AdminRequestsResp(requests=rows)


@handles(AdminInfoReq)
def info(req: AdminInfoReq) -> ApiResp:
    resp = validate_api_req(req)
    if resp: return resp

    return AdminInfoResp(admins=config.SERVER_CONFIG.admins)

