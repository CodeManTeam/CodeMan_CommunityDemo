
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional
from models import Announcement, User, SystemSetting, db, fn
from security import get_current_user
from datetime import datetime

router = APIRouter()

# Dependency to check if user is admin
def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# --- User Management ---
class UserBan(BaseModel):
    user_id: int
    reason: str
    is_banned: bool = True

class UserAdminToggle(BaseModel):
    user_id: int
    is_admin: bool

class SettingUpdate(BaseModel):
    key: str
    value: str

class UserListResponse(BaseModel):
    total: int
    items: List[dict]

@router.get("/admin/users", response_model=UserListResponse)
def get_users(q: Optional[str] = None, page: int = 1, limit: int = 20, admin: User = Depends(get_current_admin)):
    # Only show users who have actually logged in (have a login_identity)
    query = User.select().where(User.login_identity.is_null(False))
    
    if q:
        query = query.where(User.username.contains(q) | User.codemao_id.contains(q))
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).paginate(page, limit)
    
    items = [
        {
            "id": u.id,
            "username": u.username,
            "codemao_id": u.codemao_id,
            "is_admin": u.is_admin,
            "is_banned": u.is_banned,
            "ban_reason": u.ban_reason,
            "created_at": u.created_at,
            "last_login": u.last_login
        } for u in users
    ]
    
    return {"total": total, "items": items}

@router.post("/admin/users/ban")
def ban_user(ban_data: UserBan, admin: User = Depends(get_current_admin)):
    try:
        u = User.get_by_id(ban_data.user_id)
        if u.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot ban yourself")
        
        u.is_banned = ban_data.is_banned
        u.ban_reason = ban_data.reason if ban_data.is_banned else None
        u.save()
        return {"status": "success", "is_banned": u.is_banned}
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/admin/users/toggle_admin")
def toggle_user_admin(data: UserAdminToggle, admin: User = Depends(get_current_admin)):
    # Only Site Owner (ID 1) can manage admins
    if admin.id != 1:
        raise HTTPException(status_code=403, detail="Only the Site Owner can appoint or remove administrators")

    try:
        u = User.get_by_id(data.user_id)
        if u.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot change your own admin status")
            
        u.is_admin = data.is_admin
        u.save()
        return {"status": "success", "is_admin": u.is_admin}
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

# --- System Settings (Ban Screen) ---
@router.get("/admin/settings/ban_screen")
def get_ban_screen(admin: User = Depends(get_current_admin)):
    setting = SystemSetting.get_or_none(SystemSetting.key == "ban_screen_html")
    return {"html": setting.value if setting else "<h1>Account Suspended</h1><p>Your account has been banned for violating community rules.</p>"}

@router.post("/admin/settings/ban_screen")
def set_ban_screen(data: SettingUpdate, admin: User = Depends(get_current_admin)):
    setting, created = SystemSetting.get_or_create(key="ban_screen_html", defaults={"value": ""})
    setting.value = data.value
    setting.save()
    return {"status": "success"}

# --- Announcements ---
class AnnouncementCreate(BaseModel):
    content: str
    type: str = "banner" # banner, modal, toast
    active: bool = True

class AnnouncementRead(BaseModel):
    id: int
    content: str
    type: str
    active: bool
    created_at: datetime
    created_by: str

@router.get("/announcements", response_model=List[AnnouncementRead])
def get_announcements(active_only: bool = True):
    query = Announcement.select(Announcement, User).join(User).order_by(Announcement.created_at.desc())
    if active_only:
        query = query.where(Announcement.active == True)
    
    return [
        {
            "id": a.id,
            "content": a.content,
            "type": a.type,
            "active": a.active,
            "created_at": a.created_at,
            "created_by": a.created_by.username
        } for a in query
    ]

@router.post("/admin/announcements", response_model=AnnouncementRead)
def create_announcement(announcement: AnnouncementCreate, admin: User = Depends(get_current_admin)):
    new_announcement = Announcement.create(
        content=announcement.content,
        type=announcement.type,
        active=announcement.active,
        created_by=admin
    )
    
    return {
        "id": new_announcement.id,
        "content": new_announcement.content,
        "type": new_announcement.type,
        "active": new_announcement.active,
        "created_at": new_announcement.created_at,
        "created_by": admin.username
    }

@router.put("/admin/announcements/{id}", response_model=AnnouncementRead)
def update_announcement(id: int, announcement: AnnouncementCreate, admin: User = Depends(get_current_admin)):
    try:
        a = Announcement.get_by_id(id)
        a.content = announcement.content
        a.type = announcement.type
        a.active = announcement.active
        a.save()
        
        return {
            "id": a.id,
            "content": a.content,
            "type": a.type,
            "active": a.active,
            "created_at": a.created_at,
            "created_by": a.created_by.username
        }
    except Announcement.DoesNotExist:
        raise HTTPException(status_code=404, detail="Announcement not found")

@router.delete("/admin/announcements/{id}")
def delete_announcement(id: int, admin: User = Depends(get_current_admin)):
    try:
        a = Announcement.get_by_id(id)
        a.delete_instance()
        return {"status": "success"}
    except Announcement.DoesNotExist:
        raise HTTPException(status_code=404, detail="Announcement not found")
