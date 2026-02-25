from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import httpx
from models import Banner, User
from security import get_current_user
from datetime import datetime

router = APIRouter()

class BannerCreate(BaseModel):
    title: str
    image_url: str
    link_url: str

@router.get("/banners")
async def get_banners():
    """
    Get all active banners (Custom + Codemao Official)
    """
    # 1. Get Custom Banners from DB
    custom_banners = []
    try:
        db_banners = Banner.select().where(Banner.active == True).order_by(Banner.created_at.desc())
        for b in db_banners:
            custom_banners.append({
                "id": f"custom_{b.id}",
                "title": b.title,
                "background_url": b.image_url,
                "small_background_url": b.image_url, # Fallback
                "target_url": b.link_url,
                "is_custom": True
            })
    except Exception as e:
        print(f"DB Banner Error: {e}")

    # 2. Get Codemao Official Banners
    official_banners = []
    url = "https://api.codemao.cn/web/banners/all?type=OFFICIAL"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                official_banners = response.json().get("items", [])
        except Exception as e:
            print(f"Error fetching official banners: {e}")
            
    # Combine: Custom first, then Official
    return custom_banners + official_banners

@router.post("/banners")
def create_banner(banner: BannerCreate, current_user: User = Depends(get_current_user)):
    # Simple admin check (in real app use a role field)
    if not current_user.is_admin and current_user.username != "admin": 
        raise HTTPException(status_code=403, detail="Admin privileges required")

    new_banner = Banner.create(
        title=banner.title,
        image_url=banner.image_url,
        link_url=banner.link_url
    )
    return {"status": "success", "id": new_banner.id}

@router.delete("/banners/{banner_id}")
def delete_banner(banner_id: int, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    try:
        banner = Banner.get_by_id(banner_id)
        banner.delete_instance()
        return {"status": "success"}
    except Banner.DoesNotExist:
        raise HTTPException(status_code=404, detail="Banner not found")
