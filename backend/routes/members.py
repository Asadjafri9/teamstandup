import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import get_db_connection, PLACEHOLDER, USE_POSTGRES
from auth import require_user
from models import MemberInvite, InviteLinkCreate


class JoinByCode(BaseModel):
    code: str

router = APIRouter(prefix="/api/projects/{project_id}", tags=["members"])


@router.post("/members")
def add_member_by_email(project_id: str, data: MemberInvite, user=Depends(require_user)):
    db = get_db_connection()
    try:
        leader = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND role = 'Project Leader'",
            (project_id, user["id"]),
        ).fetchone()
        if not leader:
            raise HTTPException(403, "Only the leader can add members")

        existing_user = db.execute(f"SELECT * FROM users WHERE email = {PLACEHOLDER}", (data.email,)).fetchone()
        if existing_user:
            db.execute(
                f"INSERT INTO project_members (project_id, user_id, email, role, status, invite_type) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                (project_id, existing_user["id"], data.email, data.role, "invited", "email"),
            )
        else:
            db.execute(
                f"INSERT INTO project_members (project_id, email, role, status, invite_type) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                (project_id, data.email, data.role, "invited", "email"),
            )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/invite-links")
def list_invite_links(project_id: str, user=Depends(require_user)):
    db = get_db_connection()
    try:
        leader = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND role = 'Project Leader'",
            (project_id, user["id"]),
        ).fetchone()
        if not leader:
            raise HTTPException(403, "Only the leader can manage invite links")

        links = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND invite_type = 'link' AND status = 'invited'",
            (project_id,),
        ).fetchall()
        return [dict(l) for l in links]
    finally:
        db.close()


# Move these routes outside the project_id prefix
router_global = APIRouter(prefix="/api", tags=["members"])


@router_global.get("/join/{token}")
def preview_invite(token: str):
    db = get_db_connection()
    try:
        invite = db.execute(
            f"SELECT pm.*, p.name as project_name FROM project_members pm JOIN projects p ON pm.project_id = p.id WHERE pm.invite_token = {PLACEHOLDER}",
            (token,),
        ).fetchone()
        if not invite:
            raise HTTPException(404, "Invite not found")
        if invite["status"] != "invited":
            raise HTTPException(410, "This invite link has already been used")
        return {"project_name": invite["project_name"], "role": invite["role"], "is_used": False}
    finally:
        db.close()


@router_global.post("/join/{token}")
def accept_invite(token: str, user=Depends(require_user)):
    db = get_db_connection()
    try:
        invite = db.execute(
            f"SELECT * FROM project_members WHERE invite_token = {PLACEHOLDER} AND status = 'invited'",
            (token,),
        ).fetchone()
        if not invite:
            raise HTTPException(404, "Invite not found or already used")

        db.execute(
            f"UPDATE project_members SET user_id = {PLACEHOLDER}, status = 'active', joined_at = {PLACEHOLDER}, invite_token = NULL WHERE id = {PLACEHOLDER}",
            (user["id"], datetime.utcnow().isoformat(), invite["id"]),
        )
        db.commit()
        return {"ok": True, "project_id": invite["project_id"]}
    finally:
        db.close()


@router_global.post("/join-by-code")
def join_by_code(data: JoinByCode, user=Depends(require_user)):
    db = get_db_connection()
    try:
        project = db.execute(
            f"SELECT * FROM projects WHERE id = {PLACEHOLDER}",
            (data.code.strip(),),
        ).fetchone()
        if not project:
            raise HTTPException(404, "Invalid project code")

        existing = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER}",
            (project["id"], user["id"]),
        ).fetchone()

        if existing:
            if existing["status"] == "active":
                raise HTTPException(400, "You are already a member of this project")
            if existing["status"] == "invited":
                db.execute(
                    f"UPDATE project_members SET status = 'active', joined_at = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
                    (datetime.utcnow().isoformat(), existing["id"]),
                )
                db.commit()
                return {"ok": True, "project_id": project["id"], "project_name": project["name"]}
            raise HTTPException(400, "You cannot join this project")

        db.execute(
            f"INSERT INTO project_members (project_id, user_id, role, status, invite_type, joined_at, is_first_standup) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
            (project["id"], user["id"], "Member", "active", "code", datetime.utcnow().isoformat(), False if USE_POSTGRES else 0),
        )
        db.commit()
        return {"ok": True, "project_id": project["id"], "project_name": project["name"]}
    finally:
        db.close()


@router.post("/invite-links")
def create_invite_link(project_id: str, data: InviteLinkCreate, user=Depends(require_user)):
    db = get_db_connection()
    try:
        leader = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND role = 'Project Leader'",
            (project_id, user["id"]),
        ).fetchone()
        if not leader:
            raise HTTPException(403, "Only the leader can create invite links")

        token = secrets.token_urlsafe(16)
        db.execute(
            f"INSERT INTO project_members (project_id, role, status, invite_token, invite_type) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
            (project_id, data.role, "invited", token, "link"),
        )
        db.commit()
        return {"invite_token": token, "invite_url": f"/join/{token}"}
    finally:
        db.close()


@router.post("/members/{member_id}/accept")
def accept_email_invite(project_id: str, member_id: int, user=Depends(require_user)):
    db = get_db_connection()
    try:
        invite = db.execute(
            f"SELECT * FROM project_members WHERE id = {PLACEHOLDER} AND project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'invited'",
            (member_id, project_id, user["id"]),
        ).fetchone()
        if not invite:
            raise HTTPException(404, "Invite not found")

        db.execute(
            f"UPDATE project_members SET status = 'active', joined_at = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
            (datetime.utcnow().isoformat(), member_id),
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.post("/members/{member_id}/decline")
def decline_email_invite(project_id: str, member_id: int, user=Depends(require_user)):
    db = get_db_connection()
    try:
        invite = db.execute(
            f"SELECT * FROM project_members WHERE id = {PLACEHOLDER} AND project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'invited'",
            (member_id, project_id, user["id"]),
        ).fetchone()
        if not invite:
            raise HTTPException(404, "Invite not found")

        db.execute(
            f"UPDATE project_members SET status = 'declined' WHERE id = {PLACEHOLDER}",
            (member_id,),
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.delete("/members/{member_id}")
def remove_member(project_id: str, member_id: int, user=Depends(require_user)):
    db = get_db_connection()
    try:
        leader = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND role = 'Project Leader'",
            (project_id, user["id"]),
        ).fetchone()
        if not leader:
            raise HTTPException(403, "Only the leader can remove members")

        db.execute(
            f"UPDATE project_members SET status = 'removed' WHERE id = {PLACEHOLDER} AND project_id = {PLACEHOLDER}",
            (member_id, project_id),
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()
