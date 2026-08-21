import os
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature
from db import get_db, get_db_connection, USE_POSTGRES, PLACEHOLDER

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SESSION_SECRET = os.getenv("SESSION_SECRET", "standupbot-hackathon-secret-change-in-prod")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/google/callback")
APP_URL = os.getenv("APP_URL", "http://localhost:8081")

PLACEHOLDER = "%s" if USE_POSTGRES else "?"

serializer = URLSafeTimedSerializer(SESSION_SECRET)

COOKIE_NAME = "standupbot_session"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60


def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        user_id = serializer.loads(token, max_age=COOKIE_MAX_AGE)
    except BadSignature:
        return None
    
    conn = get_db_connection()
    
    try:
        user = conn.execute(f"SELECT * FROM users WHERE id = {PLACEHOLDER}", (user_id,)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def require_user(request: Request):
    user = get_current_user(request)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/auth/google")
def google_login():
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
async def google_callback(code: str, request: Request):
    try:
        token_resp = await _exchange_code(code)
        
        if "error" in token_resp:
            return RedirectResponse(url=f"{APP_URL}/?error=oauth_failed")
        
        if "access_token" not in token_resp:
            print(f"Token response: {token_resp}")
            return RedirectResponse(url=f"{APP_URL}/?error=no_access_token")
        
        user_info = await _fetch_user_info(token_resp["access_token"])
    except Exception as e:
        print(f"OAuth error: {e}")
        return RedirectResponse(url=f"{APP_URL}/?error=oauth_exception")

    conn = get_db_connection()
    
    try:
        existing = conn.execute(f"SELECT * FROM users WHERE email = {PLACEHOLDER}", (user_info["email"],)).fetchone()

        if existing:
            user_id = existing["id"]
            conn.execute(
                f"UPDATE users SET name = {PLACEHOLDER}, avatar_url = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
                (user_info.get("name", ""), user_info.get("picture", ""), user_id),
            )
        else:
            if USE_POSTGRES:
                cursor = conn.execute(
                    f"INSERT INTO users (email, name, avatar_url) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) RETURNING id",
                    (user_info["email"], user_info.get("name", ""), user_info.get("picture", "")),
                )
                user_id = cursor.fetchone()["id"]
            else:
                cursor = conn.execute(
                    f"INSERT INTO users (email, name, avatar_url) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                    (user_info["email"], user_info.get("name", ""), user_info.get("picture", "")),
                )
                user_id = cursor.lastrowid

            conn.execute(
                f"UPDATE project_members SET user_id = {PLACEHOLDER} WHERE email = {PLACEHOLDER} AND user_id IS NULL",
                (user_id, user_info["email"]),
            )

        conn.commit()
    finally:
        conn.close()

    token = serializer.dumps(user_id)
    response = RedirectResponse(url=f"{APP_URL}/dashboard")
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        domain=os.getenv("COOKIE_DOMAIN", None),
    )
    return response


@router.get("/auth/demo")
def demo_login():
    """Demo login endpoint — creates a demo user and sets a session cookie."""
    conn = get_db_connection()

    try:
        existing = conn.execute(f"SELECT * FROM users WHERE email = {PLACEHOLDER}", ("demo@standupbot.dev",)).fetchone()
        if existing:
            user_id = existing["id"]
        else:
            if USE_POSTGRES:
                cursor = conn.execute(
                    f"INSERT INTO users (email, name, avatar_url) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}) RETURNING id",
                    ("demo@standupbot.dev", "Demo User", ""),
                )
                user_id = cursor.fetchone()["id"]
            else:
                cursor = conn.execute(
                    f"INSERT INTO users (email, name, avatar_url) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})",
                    ("demo@standupbot.dev", "Demo User", ""),
                )
                user_id = cursor.lastrowid
            conn.commit()
    finally:
        conn.close()

    token = serializer.dumps(user_id)
    response = RedirectResponse(url=f"{APP_URL}/dashboard")
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        domain=os.getenv("COOKIE_DOMAIN", None),
    )
    return response


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        domain=os.getenv("COOKIE_DOMAIN", None),
        httponly=True,
        samesite="lax"
    )
    return {"ok": True}


async def _exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        return resp.json()


async def _fetch_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return resp.json()