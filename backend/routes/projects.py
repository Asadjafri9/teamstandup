import string
import random
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from db import get_db_connection, PLACEHOLDER, USE_POSTGRES
from auth import require_user
from models import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _gen_slug(length=6):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, user=Depends(require_user)):
    db = get_db_connection()
    try:
        slug = _gen_slug()
        cursor = db.execute(
            f"INSERT INTO projects (id, name, description, deadline, standup_closes_at, leader_id) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
            (slug, data.name, data.description, data.deadline, data.standup_closes_at or "21:00", user["id"]),
        )
        db.execute(
            f"INSERT INTO project_members (project_id, user_id, role, status, invite_type, joined_at, is_first_standup) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
            (slug, user["id"], "Project Leader", "active", "email", datetime.utcnow().isoformat(), False if USE_POSTGRES else 0),
        )
        db.commit()
        project = db.execute(f"SELECT * FROM projects WHERE id = {PLACEHOLDER}", (slug,)).fetchone()
        return {**dict(project), "role": "Project Leader", "status": "active", "today_status": "standup_due"}
    finally:
        db.close()


@router.get("")
def list_projects(user=Depends(require_user)):
    db = get_db_connection()
    try:
        rows = db.execute(
            f"""
            SELECT p.*, pm.role, pm.status,
                CASE WHEN s.id IS NOT NULL THEN 'submitted'
                     WHEN b.id IS NOT NULL THEN 'brief_ready'
                     ELSE 'standup_due' END AS today_status
            FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            LEFT JOIN standups s ON s.project_id = p.id AND s.member_id = pm.id AND s.date = {PLACEHOLDER}
            LEFT JOIN briefs b ON b.project_id = p.id AND b.date = {PLACEHOLDER}
            WHERE pm.user_id = {PLACEHOLDER} AND pm.status = 'active'
            ORDER BY p.created_at DESC
        """,
            (date.today(), date.today(), user["id"]),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.get("/{project_id}")
def get_project(project_id: str, user=Depends(require_user)):
    db = get_db_connection()
    try:
        project = db.execute(f"SELECT * FROM projects WHERE id = {PLACEHOLDER}", (project_id,)).fetchone()
        if not project:
            raise HTTPException(404, "Project not found")
        member = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'active'",
            (project_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(403, "You don't have access to this project")
        members = db.execute(
            f"SELECT pm.*, u.name, u.email, u.avatar_url FROM project_members pm LEFT JOIN users u ON pm.user_id = u.id WHERE pm.project_id = {PLACEHOLDER} AND pm.status != 'removed'",
            (project_id,),
        ).fetchall()
        return {**dict(project), "members": [dict(m) for m in members], "current_member": dict(member)}
    finally:
        db.close()