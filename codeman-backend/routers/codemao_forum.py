from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import httpx
import nh3
from pydantic import BaseModel
from models import BcmComment, User
from security import get_current_user
from datetime import datetime

router = APIRouter()

# Models for BCM Forum
class BCMUser(BaseModel):
    id: str
    nickname: str
    avatar_url: str

class BcmCommentCreate(BaseModel):
    content: str

# ... (existing classes)

# ... (existing sanitize_content)

# ... (existing get_bcm_posts)

# ... (existing get_bcm_post_detail)

# ... (existing get_bcm_post_replies)

@router.get("/bcm/posts/{post_id}/codeman_comments")
def get_codeman_comments(post_id: str):
    """
    Get CodeMan community comments for a BCM post
    """
    comments = (BcmComment.select(BcmComment, User)
                .join(User)
                .where(BcmComment.bcm_post_id == post_id)
                .order_by(BcmComment.created_at.desc()))
                
    return [{
        "id": c.id,
        "content": c.content,
        "created_at": c.created_at,
        "user": {
            "id": c.user.id,
            "username": c.user.username,
            "avatar_url": c.user.avatar_url
        }
    } for c in comments]

@router.post("/bcm/posts/{post_id}/codeman_comments")
def create_codeman_comment(post_id: str, comment: BcmCommentCreate, current_user: User = Depends(get_current_user)):
    """
    Create a CodeMan community comment on a BCM post
    """
    new_comment = BcmComment.create(
        bcm_post_id=post_id,
        content=comment.content,
        user=current_user
    )
    
    return {
        "id": new_comment.id,
        "content": new_comment.content,
        "created_at": new_comment.created_at,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url
        }
    }

class BCMPost(BaseModel):
    id: str
    title: str
    content: str
    board_id: Optional[str] = None
    board_name: Optional[str] = None
    user: Optional[BCMUser] = None
    created_at: int
    updated_at: Optional[int] = None
    n_views: int
    n_replies: int
    n_comments: int
    is_hot: bool = False
    is_top: bool = False

# Sanitization settings
def sanitize_content(html: str) -> str:
    # Allow safe tags and attributes
    # Enhanced for Codemao rich text
    return nh3.clean(
        html,
        tags={
            'p', 'br', 'b', 'i', 'u', 'em', 'strong', 'a', 'img', 'span', 'div', 
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre', 
            'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr',
            'font', 'center', 'strike', 's', 'del' # Legacy tags used in Codemao
        },
        attributes={
            'a': {'href', 'title', 'target'},
            'img': {'src', 'alt', 'title', 'width', 'height', 'align'},
            'font': {'color', 'size', 'face'},
            '*': {'class', 'style', 'align', 'color'} # Allow style/class globally
        },
        url_schemes={'http', 'https', 'mailto', 'data'} # Allow data URIs for images if needed
    )

@router.get("/bcm/boards")
async def get_bcm_boards():
    """
    Get list of all Codemao forum boards
    """
    url = "https://api.codemao.cn/web/forums/boards/simples/all"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"Error fetching boards: {e}")
            return []

@router.get("/bcm/posts")
async def get_bcm_posts(
    limit: int = 20, 
    offset: int = 0,
    board_id: Optional[str] = None
):
    """
    Fetch posts from Codemao forum.
    If board_id is provided, fetches from specific board.
    Otherwise fetches latest posts.
    """
    # Note: The official API structure for "latest posts" isn't explicitly detailed in the provided snippet
    # but we can infer from search or board details. 
    # Let's try to fetch from a popular board if no ID, or use a "latest" endpoint if known.
    # Based on common Codemao API patterns: /web/forums/boards/{id}/posts
    
    target_board_id = board_id if board_id else "2" # Default to 'Help' or 'Chat' board if none specified. 2 is often 'Chat'
    
    # Calculate correct offset for Codemao API
    # The frontend passes limit and offset based on simple pagination (page * limit)
    # Codemao API uses offset as number of items to skip
    
    # Ensure params are integers
    limit = int(limit)
    offset = int(offset)

    url = f"https://api.codemao.cn/web/forums/boards/{target_board_id}/posts"
    params = {
        "limit": limit,
        "offset": offset,
        "order": "-created_at" 
    }
    
    # Debug print
    print(f"Fetching BCM posts: {url} with params {params}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                print(f"BCM API Error: {resp.status_code} - {resp.text}")
                return []
            
            data = resp.json()
            items = data.get("items", [])
            
            # Debug print
            print(f"Fetched {len(items)} items from BCM")

            posts = []
            for item in items:
                # Map BCM item to our model
                user_data = item.get("user", {})
                
                # Sanitize content strictly using nh3
                # We allow minimal tags for preview
                raw_content = item.get("content", "")
                safe_content = nh3.clean(raw_content, tags={'b', 'i', 'u', 'em', 'strong'})
                
                posts.append({
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "content": safe_content, 
                    "user": {
                        "id": str(user_data.get("id")),
                        "nickname": user_data.get("nickname"),
                        "avatar_url": user_data.get("avatar_url")
                    },
                    "created_at": item.get("created_at"),
                    "n_views": item.get("n_views", 0),
                    "n_replies": item.get("n_replies", 0),
                    "n_comments": item.get("n_comments", 0),
                    "is_hot": item.get("is_hotted", False),
                    "is_top": item.get("is_pinned", False)
                })
            return posts
        except Exception as e:
            print(f"Error fetching BCM posts: {e}")
            return []

@router.get("/bcm/posts/{post_id}")
async def get_bcm_post_detail(post_id: str):
    """
    Get detailed content of a BCM post
    """
    url = f"https://api.codemao.cn/web/forums/posts/{post_id}/details"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Post not found on Codemao")
            
            data = resp.json()
            
            # Fetch User info separately if not in details
            user_info = data.get("user", {})
            if not user_info and "user_id" in data:
                try:
                    user_url = f"https://api.codemao.cn/web/users/details"
                    u_resp = await client.get(user_url, params={"id": data["user_id"]})
                    if u_resp.status_code == 200:
                        user_info = u_resp.json()
                except Exception as e:
                    print(f"Failed to fetch user info: {e}")
            
            # Placeholder if still missing
            if not user_info:
                user_info = {
                    "id": "0",
                    "nickname": "Unknown User",
                    "avatar_url": "https://static.codemao.cn/codemao-logo.png"
                }

            # Sanitize content strictly
            safe_content = sanitize_content(data.get("content", ""))
            
            return {
                "id": str(data.get("id")),
                "title": data.get("title"),
                "content": safe_content,
                "board_name": data.get("board_name"),
                "created_at": data.get("created_at"),
                "n_views": data.get("n_views", 0),
                "n_replies": data.get("n_replies", 0),
                "user": user_info
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/bcm/search")
async def search_bcm_posts(
    title: str = Query(..., min_length=1),
    page: int = 1,
    limit: int = 5
):
    """
    Search posts on Codemao forum
    """
    url = "https://api.codemao.cn/web/forums/posts/search"
    params = {
        "title": title,
        "page": page,
        "limit": limit
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                print(f"BCM Search Error: {resp.status_code} - {resp.text}")
                return []
            
            data = resp.json()
            items = data.get("items", [])
            
            posts = []
            for item in items:
                # Map BCM item to our model
                user_data = item.get("user", {})
                
                # Sanitize content strict
                raw_content = item.get("content", "")
                safe_content = nh3.clean(raw_content, tags={'b', 'i', 'u', 'em', 'strong'})
                
                posts.append({
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "content": safe_content, 
                    "user": {
                        "id": str(user_data.get("id")),
                        "nickname": user_data.get("nickname"),
                        "avatar_url": user_data.get("avatar_url")
                    },
                    "created_at": item.get("created_at"),
                    "n_views": item.get("n_views", 0),
                    "n_replies": item.get("n_replies", 0),
                    "board_name": "Codemao" 
                })
            return posts
        except Exception as e:
            print(f"Error searching BCM posts: {e}")
            return []

@router.get("/bcm/posts/{post_id}/replies")
async def get_bcm_post_replies(
    post_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    Get replies for a BCM post
    """
    url = f"https://api.codemao.cn/web/forums/posts/{post_id}/replies"
    params = {
        "limit": limit,
        "offset": offset,
        "order": "created_at"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            items = data.get("items", [])
            
            replies = []
            for item in items:
                user_data = item.get("user", {})
                safe_content = sanitize_content(item.get("content", ""))
                
                replies.append({
                    "id": str(item.get("id")),
                    "content": safe_content,
                    "user": {
                        "id": str(user_data.get("id")),
                        "nickname": user_data.get("nickname"),
                        "avatar_url": user_data.get("avatar_url")
                    },
                    "created_at": item.get("created_at")
                })
            return replies
        except Exception as e:
            print(f"Error fetching BCM replies: {e}")
            return []
