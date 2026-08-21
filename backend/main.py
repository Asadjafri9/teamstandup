from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import RedirectResponse
from db import init_db, get_db_connection, PLACEHOLDER
from auth import router as auth_router
from routes.projects import router as projects_router
from routes.members import router as members_router, router_global as members_global_router
from routes.standups import router as standups_router
from routes.briefs import router as briefs_router
import os

app = FastAPI(title="StandupBot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8080",
        "http://localhost:8081",
        os.getenv("APP_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(members_router)
app.include_router(members_global_router)
app.include_router(standups_router)
app.include_router(briefs_router)


@app.get("/api/pending-invites")
def get_pending_invites(request: Request):
    from auth import get_current_user
    user = get_current_user(request)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from db import get_db_connection
    db = get_db_connection()
    try:
        invites = db.execute(
            f"""
            SELECT pm.*, p.name as project_name 
            FROM project_members pm 
            JOIN projects p ON pm.project_id = p.id 
            WHERE pm.user_id = {PLACEHOLDER} AND pm.status = 'invited'
            """,
            (user["id"],),
        ).fetchall()
        return [dict(i) for i in invites]
    finally:
        db.close()


@app.get("/api/me")
def get_me(request: Request):
    from auth import get_current_user
    user = get_current_user(request)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.get("/api/health")
def health():
    return {"ok": True}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve static assets (logo, favicon, etc.)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))


@app.get("/app.js")
def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))


@app.get("/logo.png")
def serve_logo():
    return FileResponse(os.path.join(FRONTEND_DIR, "logo.png"))


@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/new")
def new_project():
    return FileResponse(os.path.join(FRONTEND_DIR, "new.html"))


@app.get("/project/{project_id}")
def project_page(project_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "project.html"))


@app.get("/standup/{project_id}")
def standup_page(project_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "standup.html"))


@app.get("/brief/{project_id}")
def brief_page(project_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "brief.html"))


@app.get("/members/{project_id}")
def members_page(project_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "members.html"))


@app.get("/invite-links/{project_id}")
def invite_links_page(project_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "invite-links.html"))


@app.get("/join/{token}")
def join_page(token: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "join.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)