
import json
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Request, Depends
from pydantic import BaseModel
import httpx
from models import Work, User, Notification, WorkComment, WorkLike, WorkCommentLike, Report
from security import get_current_user
from peewee import fn

router = APIRouter()

class WorkSubmission(BaseModel):
    work_id: int
    bcm_url: str

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

class ReportCreate(BaseModel):
    reason: str

@router.get("/works")
def get_works(skip: int = 0, limit: int = 20):
    # Fetch from DB (Join with User to get uploader info)
    works_query = (Work.select(Work, User)
                   .join(User)
                   .order_by(Work.created_at.desc())
                   .offset(skip)
                   .limit(limit))
    
    db_works = []
    for w in works_query:
        # Use original author info if available and user is system/imported
        if w.original_author_id:
             display_nickname = w.original_author_name or "Original Developer"
             display_avatar = w.original_author_avatar
             display_user_id = w.original_author_id
        else:
             display_nickname = w.user.username
             display_avatar = w.user.avatar_url
             display_user_id = w.user.codemao_id

        db_works.append({
            "work_id": w.work_id,
            "work_name": w.name,
            "preview_url": w.cover_url,
            "description": w.description,
            "bcm_url": w.bcm_url,
            "likes_count": w.likes,
            "views_count": w.views,
            "avatar_url": display_avatar,
            "nickname": display_nickname,
            "user_id": display_user_id,
            "internal_user_id": w.user.id
        })
    
    return db_works

def get_work_details(work_id: int, current_user_id: Optional[int] = None):
    # 1. Try DB
    try:
        w = Work.select(Work, User).join(User).where(Work.work_id == work_id).get()
        
        # Get Comments
        comments = (WorkComment.select(WorkComment, User)
                   .join(User)
                   .where((WorkComment.work == w) & (WorkComment.is_deleted == False))
                   .order_by(WorkComment.created_at.desc()))
                   
        comments_data = []
        for c in comments:
            is_liked = False
            if current_user_id:
                is_liked = WorkCommentLike.select().where((WorkCommentLike.user_id == current_user_id) & (WorkCommentLike.comment == c)).exists()
                
            comments_data.append({
                "id": c.id,
                "user": {
                    "username": c.user.username,
                    "avatar_url": c.user.avatar_url,
                    "id": c.user.id
                },
                "content": c.content,
                "parent_id": c.parent.id if c.parent else None,
                "likes": c.likes,
                "is_liked": is_liked,
                "created_at": c.created_at
            })
        
        if w.original_author_id:
            display_nickname = w.original_author_name or "Original Developer"
            display_avatar = w.original_author_avatar
            display_user_id = w.original_author_id
        else:
            display_nickname = w.user.username
            display_avatar = w.user.avatar_url
            display_user_id = w.user.codemao_id
            
        is_work_liked = False
        if current_user_id:
            is_work_liked = WorkLike.select().where((WorkLike.user_id == current_user_id) & (WorkLike.work == w)).exists()

        return {
            "work_id": w.work_id,
            "work_name": w.name,
            "preview_url": w.cover_url,
            "description": w.description,
            "bcm_url": w.bcm_url,
            "likes_count": w.likes,
            "is_liked": is_work_liked,
            "views_count": w.views,
            "avatar_url": display_avatar,
            "nickname": display_nickname,
            "user_id": display_user_id,
            "comments": comments_data,
            "comment_count": len(comments_data),
            "internal_user_id": w.user.id
        }
    except Work.DoesNotExist:
        return None


@router.get("/works/user-codemao-works")
async def get_user_codemao_works(request: Request, current_user: User = Depends(get_current_user)):
    # Fetch recent works from Codemao API
    api_url = f"https://api.codemao.cn/creation-tools/v2/user/center/work-list"
    params = {
        "type": "newest",
        "user_id": current_user.codemao_id,
        "offset": 0,
        "limit": 20
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api_url, params=params)
            if resp.status_code != 200:
                print(f"Codemao API Error: {resp.status_code} {resp.text}")
                return {"items": []} # Return empty list on error
            return resp.json()
        except Exception as e:
            print(f"Fetch User Works Error: {e}")
            return {"items": []}

@router.get("/works/search")
def search_works(q: str = Query(..., min_length=1)):
    # Search in DB
    db_query = (Work.select(Work, User)
                .join(User)
                .where(Work.name.contains(q)))
    
    db_results = []
    for w in db_query:
        if w.original_author_id:
             display_nickname = w.original_author_name or "Original Developer"
             display_avatar = w.original_author_avatar
             display_user_id = w.original_author_id
        else:
             display_nickname = w.user.username
             display_avatar = w.user.avatar_url
             display_user_id = w.user.codemao_id

        db_results.append({
            "work_id": w.work_id,
            "work_name": w.name,
            "preview_url": w.cover_url,
            "description": w.description,
            "bcm_url": w.bcm_url,
            "likes_count": w.likes,
            "views_count": w.views,
            "avatar_url": display_avatar,
            "nickname": display_nickname,
            "user_id": display_user_id 
        })
    
    return db_results[:50]

import nh3

@router.get("/works/{work_id}")
async def get_work_info(work_id: int, current_user: Optional[User] = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    info = get_work_details(work_id, user_id)
    if not info:
        # Fallback: Fetch from live Codemao API
        try:
            api_url = f"https://api.codemao.cn/creation-tools/v1/works/{work_id}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    # Convert Codemao API format to our internal format
                    result = {
                        "work_id": data.get("id"),
                        "work_name": data.get("work_name"),
                        "preview_url": data.get("preview"),
                        "description": data.get("description"),
                        "bcm_url": None, # Live works don't have bcm_url unless in our DB
                        "likes_count": data.get("praise_times", 0),
                        "views_count": data.get("view_times", 0),
                        "collect_times": data.get("collect_times", 0),
                        "share_times": data.get("share_times", 0),
                        "comment_times": data.get("comment_times", 0),
                        "publish_time": data.get("publish_time"),
                        "avatar_url": data.get("user_info", {}).get("avatar"),
                        "nickname": data.get("user_info", {}).get("nickname"),
                        "user_id": str(data.get("user_info", {}).get("id")),
                        "player_url": data.get("player_url", "").strip(),
                        "share_url": data.get("share_url", "").strip(),
                        "comments": [], # Live works don't have our internal comments
                        "comment_count": 0,
                        "is_live": True, # Flag to indicate this is fetched live
                        "is_liked": False
                    }
                    
                    # Try to find if this Codemao user exists in our DB
                    internal_user = User.get_or_none(User.codemao_id == result["user_id"])
                    if internal_user:
                        result["internal_user_id"] = internal_user.id
                        
                    return result
        except Exception as e:
            print(f"Live fetch error: {e}")
            
        raise HTTPException(status_code=404, detail="Work not found")
    return info

@router.get("/works/{work_id}/codemao_comments")
async def get_codemao_comments(work_id: int, limit: int = 20, offset: int = 0):
    """
    Fetch comments from Codemao official work page
    """
    url = f"https://api.codemao.cn/creation-tools/v1/works/{work_id}/comments"
    params = {
        "limit": limit,
        "offset": offset
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            items = data.get("items", [])
            
            comments = []
            for item in items:
                user_data = item.get("user", {})
                content = item.get("content", "")
                # Sanitize content
                safe_content = nh3.clean(content, tags={'b', 'i', 'u', 'em', 'strong'})
                
                comments.append({
                    "id": str(item.get("id")),
                    "content": safe_content,
                    "user": {
                        "id": str(user_data.get("id")),
                        "nickname": user_data.get("nickname"),
                        "avatar_url": user_data.get("avatar_url")
                    },
                    "created_at": item.get("created_at")
                })
            return comments
        except Exception as e:
            print(f"Error fetching Codemao work comments: {e}")
            return []

@router.post("/works/{work_id}/comments")
async def create_work_comment(work_id: int, comment: CommentCreate, request: Request, current_user: User = Depends(get_current_user)):
    # First, try to find the work in our DB
    try:
        work = Work.get(Work.work_id == work_id)
    except Work.DoesNotExist:
        # Auto-claim logic (Same as before)
        try:
            api_url = f"https://api.codemao.cn/creation-tools/v1/works/{work_id}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(api_url)
                if resp.status_code != 200:
                    raise HTTPException(status_code=404, detail="Work not found on Codemao or private. Cannot enable comments.")
                
                data = resp.json()
                work_owner_id = str(data.get("user_info", {}).get("id"))
                work_owner_nickname = data.get("user_info", {}).get("nickname", "Unknown Developer")
                work_owner_avatar = data.get("user_info", {}).get("avatar", "")
                
                internal_owner = User.get_or_none(User.codemao_id == work_owner_id)
                
                if not internal_owner:
                    system_user, _ = User.get_or_create(
                        codemao_id="0", 
                        defaults={"username": "Codemao System", "password_hash": "sys", "avatar_url": ""}
                    )
                    internal_owner = system_user

                work = Work.create(
                    work_id=work_id,
                    name=data["work_name"],
                    cover_url=data["preview"],
                    description=data["description"],
                    bcm_url="", 
                    user=internal_owner,
                    original_author_id=work_owner_id,
                    original_author_name=work_owner_nickname,
                    original_author_avatar=work_owner_avatar,
                    likes=data["praise_times"],
                    views=data["view_times"]
                )
                
        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"Auto-claim failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize comment section for this work due to internal error.")

    # Verify parent if exists
    parent = None
    if comment.parent_id:
        try:
            parent = WorkComment.get(WorkComment.id == comment.parent_id)
            if parent.work != work:
                 raise HTTPException(status_code=400, detail="Parent comment does not belong to this work")
        except WorkComment.DoesNotExist:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    new_comment = WorkComment.create(
        user=current_user,
        work=work,
        content=comment.content,
        parent=parent,
        likes=0,
        is_deleted=False
    )
    
    # Notify Owner or Parent Commenter
    if parent and parent.user.id != current_user.id:
        Notification.create(
            recipient=parent.user,
            sender=current_user,
            type="reply",
            message=f"replied to your comment on: {work.name}",
            target_id=work.work_id,
            target_type="work"
        )
    elif work.user.id != current_user.id and work.user.codemao_id != "0":
        Notification.create(
            recipient=work.user,
            sender=current_user,
            type="comment",
            message=f"commented on your work: {work.name}",
            target_id=work.work_id,
            target_type="work"
        )
        
    return {
        "id": new_comment.id,
        "user": {
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "id": current_user.id
        },
        "content": new_comment.content,
        "parent_id": new_comment.parent.id if new_comment.parent else None,
        "created_at": new_comment.created_at,
        "likes": 0,
        "is_liked": False
    }

@router.post("/works/{work_id}/like")
async def like_work(work_id: int, current_user: User = Depends(get_current_user)):
    try:
        work = Work.get(Work.work_id == work_id)
    except Work.DoesNotExist:
        # Auto-claim logic could be here too, but for now let's assume work exists or user must visit page first (which claims it)
        raise HTTPException(status_code=404, detail="Work not found in local DB. Please visit the work page first to initialize it.")

    existing_like = WorkLike.get_or_none(WorkLike.user == current_user, WorkLike.work == work)
    
    if existing_like:
        existing_like.delete_instance()
        work.likes = max(0, work.likes - 1)
        work.save()
        return {"status": "unliked", "likes": work.likes}
    else:
        WorkLike.create(user=current_user, work=work)
        work.likes += 1
        work.save()
        
        # Notify owner
        if work.user.id != current_user.id and work.user.codemao_id != "0":
             Notification.create(
                recipient=work.user,
                sender=current_user,
                type="like",
                message=f"liked your work: {work.name}",
                target_id=work.work_id,
                target_type="work"
            )
        
        return {"status": "liked", "likes": work.likes}

@router.post("/works/comments/{comment_id}/like")
async def like_work_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    try:
        comment = WorkComment.get(WorkComment.id == comment_id)
    except WorkComment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")

    existing_like = WorkCommentLike.get_or_none(WorkCommentLike.user == current_user, WorkCommentLike.comment == comment)
    
    if existing_like:
        existing_like.delete_instance()
        comment.likes = max(0, comment.likes - 1)
        comment.save()
        return {"status": "unliked", "likes": comment.likes}
    else:
        WorkCommentLike.create(user=current_user, comment=comment)
        comment.likes += 1
        comment.save()
        return {"status": "liked", "likes": comment.likes}

@router.delete("/works/comments/{comment_id}")
async def delete_work_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    try:
        comment = WorkComment.get(WorkComment.id == comment_id)
    except WorkComment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    if comment.user.id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
    # Soft delete
    comment.is_deleted = True
    comment.content = "[This comment has been deleted]"
    comment.save()
    
    return {"status": "deleted"}

@router.post("/works/comments/{comment_id}/report")
async def report_work_comment(comment_id: int, report: ReportCreate, current_user: User = Depends(get_current_user)):
    try:
        comment = WorkComment.get(WorkComment.id == comment_id)
    except WorkComment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    Report.create(
        reporter=current_user,
        target_type="work_comment",
        target_id=str(comment.id),
        reason=report.reason
    )
    
    return {"status": "reported"}

@router.get("/works/{work_id}/source")
async def get_source_code(work_id: int):
    # Fetch source code info from Codemao Player API
    api_url = f"https://api-creation.codemao.cn/kitten/r2/work/player/load/{work_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(api_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="Work source not found or private")
            
            data = resp.json()
            source_urls = data.get("source_urls", [])
            
            if not source_urls:
                raise HTTPException(status_code=404, detail="No source code available for this work")
                
            return {
                "work_id": work_id,
                "name": data.get("name"),
                "preview": data.get("preview"),
                "source_urls": source_urls,
                "version": data.get("version"),
                "updated_time": data.get("updated_time")
            }
        except httpx.RequestError as e:
            print(f"Source fetch error: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to Codemao API")
        except Exception as e:
            print(f"Source fetch error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/works/submit")
async def submit_work(submission: WorkSubmission, request: Request, current_user: User = Depends(get_current_user)):
    # 1. Fetch Work Info from Codemao
    api_url = f"https://api.codemao.cn/creation-tools/v1/works/{submission.work_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(api_url)
        if resp.status_code != 200:
             raise HTTPException(status_code=400, detail="Invalid Work ID or Codemao API error")
        data = resp.json()
    
    # 2. Verify Ownership
    work_owner_id = str(data.get("user_info", {}).get("id"))
    
    if work_owner_id != current_user.codemao_id:
        raise HTTPException(status_code=403, detail=f"You are not the owner of this work. Please log in with the correct account.")

    # 3. Save to DB
    try:
        work = Work.get(Work.work_id == submission.work_id)
        # Update existing
        work.name = data["work_name"]
        work.cover_url = data["preview"]
        work.description = data["description"]
        work.bcm_url = submission.bcm_url
        work.likes = data["praise_times"]
        work.views = data["view_times"]
        work.created_at = datetime.utcnow()
        work.save()
        return {"message": "Work updated successfully", "work_id": work.work_id}
    except Work.DoesNotExist:
        # Create new
        Work.create(
            work_id=submission.work_id,
            name=data["work_name"],
            cover_url=data["preview"],
            description=data["description"],
            bcm_url=submission.bcm_url,
            user=current_user,
            likes=data["praise_times"],
            views=data["view_times"]
        )
        return {"message": "Work submitted successfully", "work_id": submission.work_id}
