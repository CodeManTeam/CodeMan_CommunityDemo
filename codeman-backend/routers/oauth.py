
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from pydantic import BaseModel
from models import OAuthApplication, OAuthCode, User
from security import get_current_user, create_access_token
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter()

# --- Schemas ---
class AppCreate(BaseModel):
    name: str
    description: Optional[str] = None
    redirect_uris: str

class AppRead(BaseModel):
    client_id: str
    client_secret: str # Only shown once or to owner
    name: str
    redirect_uris: str
    description: Optional[str] = None

class TokenRequest(BaseModel):
    grant_type: str
    code: str
    client_id: str
    client_secret: str
    redirect_uri: str

# --- Endpoints ---

@router.post("/oauth/apps", response_model=AppRead)
def register_app(app: AppCreate, current_user: User = Depends(get_current_user)):
    # Generate keys
    client_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
    client_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
    
    new_app = OAuthApplication.create(
        name=app.name,
        description=app.description,
        redirect_uris=app.redirect_uris,
        client_id=client_id,
        client_secret=client_secret,
        owner=current_user
    )
    
    return {
        "client_id": new_app.client_id,
        "client_secret": new_app.client_secret,
        "name": new_app.name,
        "redirect_uris": new_app.redirect_uris,
        "description": new_app.description
    }

@router.get("/oauth/authorize")
def authorize_page(client_id: str, redirect_uri: str, response_type: str = "code", state: Optional[str] = None):
    # This endpoint checks if client is valid and returns info for the frontend consent page
    try:
        app = OAuthApplication.get(OAuthApplication.client_id == client_id)
    except OAuthApplication.DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    # Check redirect uri
    allowed_uris = app.redirect_uris.split(",")
    if redirect_uri not in [u.strip() for u in allowed_uris]:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")
        
    return {
        "app_name": app.name,
        "app_description": app.description,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state
    }

@router.post("/oauth/authorize")
def authorize_confirm(
    client_id: str = Form(...), 
    redirect_uri: str = Form(...), 
    response_type: str = Form("code"), 
    state: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    # User clicked "Allow"
    try:
        app = OAuthApplication.get(OAuthApplication.client_id == client_id)
    except OAuthApplication.DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # Verify URI again
    allowed_uris = app.redirect_uris.split(",")
    if redirect_uri not in [u.strip() for u in allowed_uris]:
         raise HTTPException(status_code=400, detail="Redirect URI mismatch")

    # Generate Authorization Code
    code_val = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    OAuthCode.create(
        code=code_val,
        client_id=client_id,
        user=current_user,
        redirect_uri=redirect_uri,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    # Return the redirect URL
    sep = "&" if "?" in redirect_uri else "?"
    target = f"{redirect_uri}{sep}code={code_val}"
    if state:
        target += f"&state={state}"
        
    return {"redirect_to": target}

@router.post("/oauth/token")
def exchange_token(req: TokenRequest):
    if req.grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
        
    try:
        auth_code = OAuthCode.get(OAuthCode.code == req.code)
    except OAuthCode.DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid code")
        
    if auth_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")
        
    if auth_code.client_id != req.client_id:
        raise HTTPException(status_code=400, detail="Client ID mismatch")
        
    # Verify Client Secret
    try:
        app = OAuthApplication.get(OAuthApplication.client_id == req.client_id)
        if app.client_secret != req.client_secret:
             raise HTTPException(status_code=401, detail="Invalid client_secret")
    except OAuthApplication.DoesNotExist:
         raise HTTPException(status_code=400, detail="Invalid client_id")

    if auth_code.redirect_uri != req.redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")
        
    # Generate Access Token
    # In a real system, we might issue a special OAuth token with scopes.
    # Here we just issue a standard user token for simplicity, 
    # OR we issue a special token that identifies the app.
    
    # Let's issue a standard token but maybe we should track it.
    access_token = create_access_token(data={"sub": str(auth_code.user.id), "azp": req.client_id})
    
    # Delete code (single use)
    auth_code.delete_instance()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600 # 1 hour default from security.py
    }

@router.get("/oauth/apps/me", response_model=List[AppRead])
def get_my_apps(current_user: User = Depends(get_current_user)):
    apps = OAuthApplication.select().where(OAuthApplication.owner == current_user)
    return [
        {
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "name": app.name,
            "redirect_uris": app.redirect_uris,
            "description": app.description
        } for app in apps
    ]

@router.get("/oauth/userinfo")
def user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "codemao_id": current_user.codemao_id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
        "description": current_user.description
    }
