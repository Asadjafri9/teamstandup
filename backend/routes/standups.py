from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from db import get_db_connection, PLACEHOLDER, USE_POSTGRES
from auth import require_user
from models import StandupSubmit

router = APIRouter(prefix="/api/projects/{project_id}", tags=["standups"])


@router.get("/standup/today")
def get_today_standup(project_id: str, user=Depends(require_user)):
    db = get_db_connection()
    try:
        member = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'active'",
            (project_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(403, "Not a member of this project")

        standup = db.execute(
            f"SELECT * FROM standups WHERE project_id = {PLACEHOLDER} AND member_id = {PLACEHOLDER} AND date = {PLACEHOLDER}",
            (project_id, member["id"], date.today()),
        ).fetchone()

        brief_exists = db.execute(
            f"SELECT id FROM briefs WHERE project_id = {PLACEHOLDER} AND date = {PLACEHOLDER}",
            (project_id, date.today()),
        ).fetchone()

        if brief_exists and not standup:
            return {"standup_closed": True, "message": "Today's standup is closed. The brief is already out."}

        if not standup:
            return {"submitted": False, "member_id": member["id"], "is_first_standup": bool(member["is_first_standup"])}

        return {
            "submitted": True,
            "standup": dict(standup),
            "is_first_standup": bool(member["is_first_standup"]),
        }
    finally:
        db.close()


@router.post("/standup")
def submit_standup(project_id: str, data: StandupSubmit, user=Depends(require_user)):
    db = get_db_connection()
    try:
        member = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'active'",
            (project_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(403, "Not a member of this project")

        brief_exists = db.execute(
            f"SELECT id FROM briefs WHERE project_id = {PLACEHOLDER} AND date = {PLACEHOLDER}",
            (project_id, date.today()),
        ).fetchone()
        if brief_exists:
            raise HTTPException(400, "Today's standup is closed. The brief has already been generated.")

        existing = db.execute(
            f"SELECT * FROM standups WHERE project_id = {PLACEHOLDER} AND member_id = {PLACEHOLDER} AND date = {PLACEHOLDER}",
            (project_id, member["id"], date.today()),
        ).fetchone()

        if existing:
            db.execute(
                f"UPDATE standups SET did = {PLACEHOLDER}, will_do = {PLACEHOLDER}, blocker = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
                (data.did, data.will_do, data.blocker, existing["id"]),
            )
        else:
            db.execute(
                f"INSERT INTO standups (project_id, member_id, date, did, will_do, blocker) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                (project_id, member["id"], date.today(), data.did, data.will_do, data.blocker),
            )
            if member["is_first_standup"]:
                db.execute(
                    f"UPDATE project_members SET is_first_standup = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
                    (False if USE_POSTGRES else 0, member["id"]),
                )

        db.commit()

        total = db.execute(
            f"SELECT COUNT(*) as c FROM project_members WHERE project_id = {PLACEHOLDER} AND status = 'active'",
            (project_id,),
        ).fetchone()["c"]
        submitted = db.execute(
            f"SELECT COUNT(*) as c FROM standups WHERE project_id = {PLACEHOLDER} AND date = {PLACEHOLDER}",
            (project_id, date.today()),
        ).fetchone()["c"]

        return {"ok": True, "submitted_count": submitted, "total_active_members": total}
    finally:
        db.close()


@router.get("/standups/status")
def standup_status(project_id: str, user=Depends(require_user)):
    db = get_db_connection()
    try:
        member = db.execute(
            f"SELECT * FROM project_members WHERE project_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER} AND status = 'active'",
            (project_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(403, "Not a member of this project")

        members = db.execute(
            f"""
            SELECT pm.id, u.name, pm.role,
                CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS submitted
            FROM project_members pm
            LEFT JOIN users u ON pm.user_id = u.id
            LEFT JOIN standups s ON s.member_id = pm.id AND s.project_id = {PLACEHOLDER} AND s.date = {PLACEHOLDER}
            WHERE pm.project_id = {PLACEHOLDER} AND pm.status = 'active'
        """,
            (project_id, date.today(), project_id),
        ).fetchall()

        return [{"name": m["name"], "role": m["role"], "submitted": bool(m["submitted"])} for m in members]
    finally:
        db.close()
