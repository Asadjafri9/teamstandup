from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "dist", "client")


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


# Serve frontend static files (assets, favicon, etc.)
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Catch-all: serve index.html for SPA routing (must be after all API routes)
from fastapi.responses import FileResponse

@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    # Try to serve a specific static file first
    file_path = os.path.join(frontend_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    # Fall back to index.html for SPA routing
    index = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)