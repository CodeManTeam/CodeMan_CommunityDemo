
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel as PydanticBaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import markdown
import base64
import bleach
from cryptography.hazmat.primitives.asymmetric import padding
import httpx
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from models import db, User, Post, Category, Comment, Work, Notification, Follow, SystemSetting, Report, create_tables, PostLike, CommentLike
from contextlib import asynccontextmanager
from codemao_api import codemao_api

from security import (
    create_access_token, 
    get_current_user, 
    pem_public_key, 
    private_key
)
from crypto_utils import encrypt_data
from config import BLOCKED_USER_AGENTS, SECRET_KEY, ALGORITHM
import jwt

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

# --- Pydantic Models ---

class UserRead(PydanticBaseModel):
    id: int
    codemao_id: str
    username: str
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    is_following: Optional[bool] = False # For current user context
    is_admin: bool = False

    class Config:
        from_attributes = True

class PostBase(PydanticBaseModel):
    title: str
    content: str
    category_id: Optional[int] = None

class PostCreate(PostBase):
    pass

class CommentBase(PydanticBaseModel):
    content: str

class CommentCreate(CommentBase):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[int] = None

class CommentRead(CommentBase):
    id: int
    created_at: datetime
    user: UserRead
    likes: int = 0
    is_liked: bool = False
    parent_id: Optional[int] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True

class NotificationRead(PydanticBaseModel):
    id: int
    sender: UserRead
    type: str
    message: str
    target_id: Optional[int]
    target_type: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostRead(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    views: int
    likes: int
    is_liked: bool = False
    is_pinned: bool = False # Added field
    user: UserRead 
    # Note: In Peewee, accessing post.user triggers a query. 
    # We'll need to handle this carefully or use join.

    class Config:
        from_attributes = True

class ReportCreate(PydanticBaseModel):
    target_type: str = Field(..., pattern="^(post|comment|work|user)$")
    target_id: str
    reason: str = Field(..., min_length=5, max_length=500)

class ReportRead(PydanticBaseModel):
    id: int
    reporter: UserRead
    target_type: str
    target_id: str
    reason: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CategoryRead(PydanticBaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True

class LoginRequest(PydanticBaseModel):
    identity: str
    password: str

class AuthResponse(PydanticBaseModel):
    token: str
    user: UserRead

class SearchResult(PydanticBaseModel):
    type: str  # 'post', 'user', 'work'
    id: str
    title: str
    subtitle: Optional[str] = None
    url: str
    image_url: Optional[str] = None

# --- Security Helpers ---
# Imported from security.py

# --- DB & Lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    if db.is_closed():
        db.connect()
    create_tables()
    
    # Set user with ID 1 as admin
    try:
        user_1 = User.get_or_none(User.id == 1)
        if user_1 and not user_1.is_admin:
            user_1.is_admin = True
            user_1.save()
            print(f"Set user ID 1 ({user_1.username}) as admin")
    except Exception as e:
        print(f"Could not set user ID 1 as admin: {e}")
    
    # Init Categories
    if Category.select().count() == 0:
        categories = [
            {"name": "General Discussion", "slug": "general"},
            {"name": "Help & Support", "slug": "help"},
            {"name": "Showcase", "slug": "showcase"},
            {"name": "Tutorials", "slug": "tutorials"}
        ]
        for cat in categories:
            Category.create(**cat)
            
    yield
    if not db.is_closed():
        db.close()

app = FastAPI(lifespan=lifespan, title="CodeMan API")

# Print routes for debugging
@app.on_event("startup")
async def startup_event():
    print("--- Registered Routes ---")
    for route in app.routes:
        print(f"{route.path} [{route.name}]")
    print("-------------------------")

# --- Rate Limit Setup ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 1. Allow OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    # 2. Allow Public Paths
    # Root, Docs, OpenAPI
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Auth endpoints
    if request.url.path.startswith("/api/auth/"):
        return await call_next(request)

    # 3. Check Authentication for all other /api paths
    if request.url.path.startswith("/api"):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Verify token signature
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
            except Exception as e:
                print(f"Auth Middleware Error: {e}")
                return JSONResponse(status_code=401, content={"detail": "Authentication failed"})
        # Note: If no token, we proceed. Routes that require auth will fail in their dependencies.


    # 4. Anti-Scraping Logic (Existing)
    # Move existing anti-scraping logic here or keep it as separate middleware?
    # The existing anti-scraping middleware is separate.
    # We should let the request proceed to the next middleware.
    
    response = await call_next(request)
    return response

# --- Anti-Scraping Middleware ---
@app.middleware("http")
async def anti_scraping_middleware(request: Request, call_next):
    # 1. User-Agent Check
    ua = request.headers.get("user-agent", "").lower()
    if any(agent in ua for agent in BLOCKED_USER_AGENTS):
        return JSONResponse(status_code=403, content={"detail": "Access Denied: Automated access restricted"})

    # 2. Referer Check for Write Operations (POST, PUT, DELETE)
    if request.method in ["POST", "PUT", "DELETE"]:
        referer = request.headers.get("referer", "")
        origin = request.headers.get("origin", "")
        # Allow localhost for dev, but in prod verify domain
        # Also allow 192.168.x.x for LAN access
        allowed_hosts = ["localhost", "127.0.0.1", "codeman.community", "192.168.", "your-domain.com", "your-domain.com"]
        
        # Skip check if no referer/origin (could be mobile app, but here we are strict web)
        # If strict:
        if not referer and not origin:
             # Let's be lenient for now to avoid breaking too much, but log it
             pass 
        else:
            is_valid = False
            for host in allowed_hosts:
                if (referer and host in referer) or (origin and host in origin):
                    is_valid = True
                    break
            if not is_valid:
                print(f"Access Denied: Referer: {referer}, Origin: {origin}", flush=True)
                return JSONResponse(status_code=403, content={"detail": f"Access Denied: Invalid Origin. Referer: {referer}, Origin: {origin}"})

    response = await call_next(request)
    return response

from routers import works, banners, codemao_forum, oauth, admin
app.include_router(works.router, prefix="/api", tags=["works"])
app.include_router(banners.router, prefix="/api", tags=["banners"])
app.include_router(codemao_forum.router, prefix="/api", tags=["codemao-forum"])
app.include_router(oauth.router, prefix="/api", tags=["oauth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"], # Allow all for local dev access from mobile
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

# --- Routes ---

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeMan API (Connected to Codemao)"}

# --- Auth ---

@app.get("/api/search/global", response_model=List[SearchResult])
@limiter.limit("20/minute")
async def global_search(request: Request, q: str = Query(..., min_length=1)):
    results = []
    
    # 1. Search Posts
    posts = (Post.select()
             .where((Post.title.contains(q)) | (Post.content.contains(q)))
             .order_by(Post.created_at.desc())
             .limit(5))
             
    for p in posts:
        # Create a subtitle from content snippet
        snippet = p.content[:100].replace('\n', ' ') + "..." if len(p.content) > 100 else p.content
        results.append(SearchResult(
            type="post",
            id=str(p.id),
            title=p.title,
            subtitle=snippet,
            url=f"/forum/{p.id}",
            image_url=None
        ))
        
    # 2. Search Users
    users = (User.select()
             .where((User.username.contains(q)) | (User.description.contains(q)))
             .limit(5))
             
    for u in users:
        results.append(SearchResult(
            type="user",
            id=str(u.id),
            title=u.username,
            subtitle=u.description or "No description",
            url=f"/user/{u.id}",
            image_url=u.avatar_url
        ))
        
    # 3. Search Works (DB)
    works_list = (Work.select(Work, User)
             .join(User)
             .where(Work.name.contains(q))
             .limit(5))
             
    for w in works_list:
        results.append(SearchResult(
            type="work",
            id=str(w.work_id),
            title=w.name,
            subtitle=f"by {w.user.username}",
            url=f"https://shequ.codemao.cn/work/{w.work_id}",
            image_url=w.cover_url
        ))

    # 4. Search BCM Posts (Codemao Forum)
    try:
        url = "https://api.codemao.cn/web/forums/posts/search"
        params = {"title": q, "page": 1, "limit": 5}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                
                for item in items:
                    # Clean content for subtitle
                    raw_content = item.get("content", "")
                    clean_text = bleach.clean(raw_content, tags=[], strip=True)
                    snippet = clean_text[:100].replace('\n', ' ') + "..." if len(clean_text) > 100 else clean_text
                    
                    results.append(SearchResult(
                        type="post",
                        id=str(item.get("id")),
                        title=f"[BCM] {item.get('title')}",
                        subtitle=snippet,
                        url=f"/forum/bcm/{item.get('id')}",
                        image_url=None
                    ))
    except Exception as e:
        print(f"BCM Search Error: {e}")
        
    return results

@app.get("/api/auth/public-key")
def get_public_key():
    return {"public_key": pem_public_key}

@app.post("/api/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(data: LoginRequest, request: Request):
    # 1. Decrypt Password (RSA)
    try:
        encrypted_bytes = base64.b64decode(data.password)
        decrypted_password = private_key.decrypt(
            encrypted_bytes,
            padding.PKCS1v15()
        ).decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid password encryption")

    try:
        # 2. Login to Codemao
        res = await codemao_api.login(data.identity, decrypted_password)
        
        # 3. Extract Token (Codemao Token - kept for reference if needed, but we issue our own)
        codemao_token = res.get("auth", {}).get("token") or res.get("token")
        
        if not codemao_token:
             if "ticket" in res:
                 codemao_token = res["ticket"]
             else:
                print(f"Login response unexpected: {res}")
                raise HTTPException(status_code=400, detail="Could not retrieve token from Codemao")

        # 4. Get User Info
        user_data = res.get("user_info", {})
        
        if not user_data:
            user_data = await codemao_api.get_user_info(codemao_token)

        # 5. Map to DB
        c_id = str(user_data.get("id", ""))
        c_name = user_data.get("nickname", data.identity)
        c_avatar = user_data.get("avatar_url", "")
        c_desc = user_data.get("description", "")

        if not c_id:
            raise HTTPException(status_code=400, detail="Could not retrieve User ID")

        user, created = User.get_or_create(
            codemao_id=c_id,
            defaults={
                "username": c_name,
                "avatar_url": c_avatar,
                "description": c_desc,
                "last_login": datetime.utcnow()
            }
        )

        # Check if banned
        if user.is_banned:
             ban_screen = SystemSetting.get_or_none(SystemSetting.key == "ban_screen_html")
             screen_html = ban_screen.value if ban_screen else "<h1>Account Suspended</h1><p>Your account has been banned.</p>"
             return JSONResponse(status_code=403, content={
                 "detail": "Account Banned", 
                 "ban_reason": user.ban_reason,
                 "ban_screen": screen_html
             })
        
        if not created:
            user.username = c_name
            user.avatar_url = c_avatar
            user.last_login = datetime.utcnow()
            # Update token
            user.codemao_token = codemao_token
            # Update encrypted credentials
            user.login_identity = data.identity
            user.encrypted_password = encrypt_data(decrypted_password)
            user.save()
        else:
            # New user, save token
            user.codemao_token = codemao_token
            # Save encrypted credentials
            user.login_identity = data.identity
            user.encrypted_password = encrypt_data(decrypted_password)
            user.save()

        # 6. Issue Application JWT
        # We ignore Codemao token for client-side auth, and use our own JWT
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "token": access_token,
            "user": {
                "id": user.id,
                "codemao_id": user.codemao_id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "description": user.description,
                "is_admin": user.is_admin
            }
        }

    except Exception as e:
        print(f"Login Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/me", response_model=UserRead)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/api/users/{user_id}", response_model=UserRead)
@limiter.limit("60/minute")
def read_user(user_id: int, request: Request):
    try:
        user = User.get_by_id(user_id)
        
        # Counts
        followers = Follow.select().where(Follow.followed == user).count()
        following = Follow.select().where(Follow.follower == user).count()
        
        # Check if current user is following this user
        is_following = False
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                # Manually verify token to get current user ID
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                current_user_id = int(payload.get("sub"))
                
                # Check follow status
                is_following = Follow.select().where(
                    (Follow.follower_id == current_user_id) & 
                    (Follow.followed_id == user.id)
                ).exists()
            except Exception as e:
                # Token invalid or expired, treat as not logged in
                pass
        
        return {
            "id": user.id,
            "codemao_id": user.codemao_id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "description": user.description,
            "followers_count": followers,
            "following_count": following,
            "is_following": is_following,
            "is_admin": user.is_admin
        }
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/{user_id}/follow")
@limiter.limit("10/minute")
def follow_user(user_id: int, request: Request, current_user: User = Depends(get_current_user)):
    try:
        target_user = User.get_by_id(user_id)
        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
            
        follow, created = Follow.get_or_create(follower=current_user, followed=target_user)
        
        if created:
            # Create notification
            Notification.create(
                recipient=target_user,
                sender=current_user,
                type="follow",
                message=f"started following you",
                target_id=current_user.id,
                target_type="user"
            )
            
        return {"status": "success", "following": True}
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@app.delete("/api/users/{user_id}/follow")
@limiter.limit("10/minute")
def unfollow_user(user_id: int, request: Request, current_user: User = Depends(get_current_user)):
    try:
        target_user = User.get_by_id(user_id)
        query = Follow.delete().where((Follow.follower == current_user) & (Follow.followed == target_user))
        rows = query.execute()
        return {"status": "success", "following": False}
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/users/{user_id}/followers", response_model=List[UserRead])
@limiter.limit("20/minute")
def read_user_followers(user_id: int, request: Request):
    try:
        user = User.get_by_id(user_id)
        # Select followers (User joined via Follow.follower)
        followers = (User.select()
                     .join(Follow, on=(Follow.follower == User.id))
                     .where(Follow.followed == user))
        
        return [
            {
                "id": u.id,
                "codemao_id": u.codemao_id,
                "username": u.username,
                "avatar_url": u.avatar_url,
                "description": u.description,
                "is_admin": u.is_admin
            }
            for u in followers
        ]
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/users/{user_id}/following", response_model=List[UserRead])
@limiter.limit("20/minute")
def read_user_following(user_id: int, request: Request):
    try:
        user = User.get_by_id(user_id)
        # Select following (User joined via Follow.followed)
        following = (User.select()
                     .join(Follow, on=(Follow.followed == User.id))
                     .where(Follow.follower == user))
        
        return [
            {
                "id": u.id,
                "codemao_id": u.codemao_id,
                "username": u.username,
                "avatar_url": u.avatar_url,
                "description": u.description,
                "is_admin": u.is_admin
            }
            for u in following
        ]
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/users/{user_id}/posts", response_model=List[PostRead])
@limiter.limit("30/minute")
def read_user_posts(user_id: int, request: Request):
    # Verify user exists first
    try:
        u = User.get_by_id(user_id)
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
        
    posts = (Post.select(Post, User)
             .join(User)
             .where(Post.user == u)
             .order_by(Post.created_at.desc()))
             
    # Reuse the serialization logic from read_posts
    return [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category_id": p.category_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "views": p.views,
            "likes": p.likes,
            "is_pinned": p.is_pinned,
            "user": u 
        }
        for p in posts
    ]

@app.get("/api/notifications", response_model=List[NotificationRead])
def get_notifications(request: Request, current_user: User = Depends(get_current_user)):
    return list(Notification.select(Notification, User)
                .join(User, on=(Notification.sender == User.id))
                .where(Notification.recipient == current_user)
                .order_by(Notification.created_at.desc())
                .limit(50))

@app.post("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, request: Request, current_user: User = Depends(get_current_user)):
    try:
        n = Notification.get_by_id(notification_id)
        if n.recipient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your notification")
        n.is_read = True
        n.save()
        return {"status": "success"}
    except Notification.DoesNotExist:
        raise HTTPException(status_code=404, detail="Notification not found")

@app.post("/api/notifications/read-all")
def mark_all_read(request: Request, current_user: User = Depends(get_current_user)):
    query = Notification.update(is_read=True).where((Notification.recipient == current_user) & (Notification.is_read == False))
    query.execute()
    return {"status": "success"}

# --- Posts ---

@app.get("/api/posts", response_model=List[PostRead])
@limiter.limit("60/minute")
def read_posts(request: Request, skip: int = 0, limit: int = 100, category_id: Optional[int] = None):
    query = Post.select(Post, User).join(User)
    
    if category_id:
        query = query.where(Post.category_id == category_id)
        
    # Order by is_pinned desc, then created_at desc
    posts = list(query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset(skip).limit(limit))
    
    # Determine current user for is_liked
    current_user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = int(payload.get("sub"))
        except:
            pass

    # Peewee objects need to be converted to dicts compatible with Pydantic
    # especially for the nested 'user' relation
    result = []
    for p in posts:
        is_liked = False
        if current_user_id:
            is_liked = PostLike.select().where((PostLike.user_id == current_user_id) & (PostLike.post == p)).exists()

        post_dict = {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category_id": p.category_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "views": p.views,
            "likes": p.likes,
            "is_liked": is_liked,
            "is_pinned": p.is_pinned,
            "user": {
                "id": p.user.id,
                "codemao_id": p.user.codemao_id,
                "username": p.user.username,
                "avatar_url": p.user.avatar_url,
                "description": p.user.description,
                "is_admin": p.user.is_admin
            }
        }
        result.append(post_dict)
        
    return result

@app.get("/api/posts/{post_id}", response_model=PostRead)
@limiter.limit("60/minute")
def read_post(post_id: int, request: Request, response: Response):
    try:
        post = Post.get_by_id(post_id)
        
        # Check cookie to prevent view spamming
        view_cookie = f"viewed_post_{post_id}"
        if not request.cookies.get(view_cookie):
            post.views += 1
            post.save()
            response.set_cookie(key=view_cookie, value="1", max_age=86400)

        # Determine current user for is_liked
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                current_user_id = int(payload.get("sub"))
            except:
                pass
        
        is_liked = False
        if current_user_id:
            is_liked = PostLike.select().where((PostLike.user_id == current_user_id) & (PostLike.post == post)).exists()

        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category_id": post.category_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "views": post.views,
            "likes": post.likes,
            "is_liked": is_liked,
            "is_pinned": post.is_pinned,
            "user": {
                "id": post.user.id,
                "codemao_id": post.user.codemao_id,
                "username": post.user.username,
                "avatar_url": post.user.avatar_url,
                "description": post.user.description,
                "is_admin": post.user.is_admin
            }
        }
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

@app.put("/api/posts/{post_id}/pin")
@limiter.limit("5/minute")
def pin_post(post_id: int, request: Request, current_user: User = Depends(get_current_user)):
    # Only admin can pin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to pin posts")
        
    try:
        post = Post.get_by_id(post_id)
        post.is_pinned = not post.is_pinned # Toggle
        post.save()
        return {"status": "success", "is_pinned": post.is_pinned}
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

@app.get("/api/posts/{post_id}/embed", response_class=HTMLResponse)
def embed_post(post_id: int, hide_title: bool = False):
    try:
        post = Post.get_by_id(post_id)
        # Convert Markdown to HTML
        html_content = markdown.markdown(post.content, extensions=['fenced_code', 'tables'])
        
        # Sanitize HTML
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'pre', 'code', 
            'img', 'blockquote', 'ul', 'ol', 'li', 'hr', 'table', 'thead', 
            'tbody', 'tr', 'th', 'td', 'div', 'span'
        ]
        allowed_attrs = {
            '*': ['class'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'a': ['href', 'title', 'target']
        }
        
        clean_html = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)

        # Process [work:ID] tags
        def replace_work_tag(match):
            try:
                work_id = int(match.group(1))
                # works module is imported below, but we can access it if it's in global scope
                # However, python functions capture global scope.
                # Let's ensure works is available. It is imported at module level later.
                # To be safe, we might need to move the import up or rely on it being available at runtime.
                # Since embed_post is called after app startup, works should be imported.
                work = works.get_work_details(work_id)
                
                if not work:
                    return f'<div class="work-card-error" style="padding:10px; background:#fee; color:red; border-radius:4px;">Work ID {work_id} not found</div>'
                
                # Sanitize data
                safe_name = bleach.clean(work['work_name'])
                safe_nick = bleach.clean(work['nickname'])
                
                return f"""
                <div class="work-card">
                    <a href="https://shequ.codemao.cn/work/{work['work_id']}" target="_blank" class="work-link">
                        <div class="work-cover" style="background-image: url('{work['preview_url']}')"></div>
                        <div class="work-info">
                            <div class="work-title">{safe_name}</div>
                            <div class="work-author">
                                <img src="{work['avatar_url']}" alt="Avatar">
                                <span>{safe_nick}</span>
                            </div>
                            <div class="work-stats">
                                <span>👁️ {work['views_count']}</span>
                                <span>❤️ {work['likes_count']}</span>
                            </div>
                        </div>
                    </a>
                </div>
                """
            except Exception as e:
                print(f"Error expanding work tag: {e}")
                return f'<span style="color:red">[Error loading work]</span>'

        clean_html = re.sub(r'\[work:(\d+)\]', replace_work_tag, clean_html)

        title_html = f"<h1>{post.title}</h1>" if not hide_title else ""
        meta_html = f'<div class="meta">Posted by <strong>{post.user.username}</strong> on {post.created_at.strftime("%Y-%m-%d %H:%M")}</div><hr>' if not hide_title else ""

        # Prepare dynamic CSS based on hide_title flag
        watermark_display = "none" if hide_title else "block"
        footer_display = "none" if hide_title else "block"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{post.title}</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                    padding: 20px; 
                    padding-bottom: 50px;
                    line-height: 1.6; 
                    color: #333;
                    margin: 0;
                    background-color: #fff;
                    position: relative;
                }}
                /* Mobile optimization */
                @media (max-width: 600px) {{
                    body {{
                        padding: 0px;
                        padding-bottom: 30px;
                    }}
                    img {{
                        border-radius: 4px;
                    }}
                }}
                
                h1 {{ font-size: 2em; margin-bottom: 0.5em; }}
                .meta {{ color: #666; font-size: 0.9em; margin-bottom: 1em; }}
                img {{ max-width: 100%; height: auto; border-radius: 8px; }}
                pre {{ background: #f4f4f4; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: monospace; }}
                code {{ font-family: monospace; background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }}
                blockquote {{ border-left: 4px solid #3b82f6; padding-left: 15px; color: #555; margin: 15px 0; background: #f8fafc; padding: 10px 15px; border-radius: 0 8px 8px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
                th {{ background-color: #f9fafb; font-weight: 600; }}
                a {{ color: #2563eb; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                hr {{ border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0; }}
                
                /* Watermark */
                .watermark {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: 4rem;
                    color: rgba(0, 0, 0, 0.05);
                    pointer-events: none;
                    white-space: nowrap;
                    z-index: 0;
                    display: {watermark_display};
                }}

                /* Footer Link */
                .footer-link {{
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px dashed #e5e7eb;
                    text-align: center;
                    font-size: 0.8em;
                    color: #999;
                    display: {footer_display};
                }}
                .footer-link a {{
                    font-weight: bold;
                }}
                
                /* Work Card */
                .work-card {{
                    margin: 10px 0;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    overflow: hidden;
                    max-width: 100%;
                    background: #fff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }}
                .work-link {{
                    display: block;
                    text-decoration: none;
                    color: inherit;
                }}
                .work-cover {{
                    height: 180px;
                    background-size: cover;
                    background-position: center;
                    background-color: #f3f4f6;
                }}
                .work-info {{
                    padding: 12px;
                }}
                .work-title {{
                    font-size: 1em;
                    font-weight: bold;
                    margin-bottom: 4px;
                    color: #111;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                .work-author {{
                    display: flex;
                    align-items: center;
                    font-size: 0.85em;
                    color: #666;
                    margin-bottom: 8px;
                }}
                .work-author img {{
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    margin-right: 6px;
                    object-fit: cover;
                }}
                .work-stats {{
                    display: flex;
                    gap: 10px;
                    font-size: 0.8em;
                    color: #888;
                }}
            </style>
        </head>
        <body>
            <div class="watermark">CodeMan Community</div>
            {title_html}
            {meta_html}
            <div class="content" style="position: relative; z-index: 1;">
                {clean_html}
            </div>
            <div class="footer-link">
                Read full discussion on <a href="http://localhost:5173/forum/{post.id}" target="_blank">CodeMan Community</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

@app.post("/api/posts", response_model=PostRead)
@limiter.limit("5/minute")
async def create_post(post: PostCreate, request: Request, current_user: User = Depends(get_current_user)):
    new_post = Post.create(
        title=post.title,
        content=post.content,
        category_id=post.category_id,
        user=current_user
    )
    
    # Return formatted response
    return {
            "id": new_post.id,
            "title": new_post.title,
            "content": new_post.content,
            "category_id": new_post.category_id,
            "created_at": new_post.created_at,
            "updated_at": new_post.updated_at,
            "views": new_post.views,
            "likes": new_post.likes,
            "is_pinned": new_post.is_pinned,
            "user": {
                "id": current_user.id,
                "codemao_id": current_user.codemao_id,
                "username": current_user.username,
                "avatar_url": current_user.avatar_url,
                "description": current_user.description,
                "is_admin": current_user.is_admin
            }
    }

@app.put("/api/posts/{post_id}", response_model=PostRead)
@limiter.limit("10/minute")
async def update_post(post_id: int, post_update: PostCreate, request: Request, current_user: User = Depends(get_current_user)):
    try:
        post = Post.get_by_id(post_id)
        
        # Check permissions: Author OR Admin
        if post.user.id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to edit this post")
            
        post.title = post_update.title
        post.content = post_update.content
        if post_update.category_id:
            post.category_id = post_update.category_id
        post.updated_at = datetime.utcnow()
        post.save()
        
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category_id": post.category_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "views": post.views,
            "likes": post.likes,
            "is_pinned": post.is_pinned,
            "user": {
                "id": post.user.id,
                "codemao_id": post.user.codemao_id,
                "username": post.user.username,
                "avatar_url": post.user.avatar_url,
                "description": post.user.description,
                "is_admin": post.user.is_admin
            }
        }
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

@app.delete("/api/posts/{post_id}")
@limiter.limit("10/minute")
async def delete_post(post_id: int, request: Request, current_user: User = Depends(get_current_user)):
    try:
        post = Post.get_by_id(post_id)
        
        # Check permissions: Author OR Admin
        if post.user.id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
            
        # Delete associated comments first (cascade usually handles this but peewee might need explicit)
        # Assuming cascade delete is not set up in DB, let's delete manually to be safe or rely on DB
        # SQLite with foreign keys enabled supports cascade.
        # But to be safe:
        Comment.delete().where(Comment.post == post).execute()
        
        post.delete_instance()
        return {"status": "success", "message": "Post deleted"}
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

@app.post("/api/reports", response_model=ReportRead)
@limiter.limit("5/minute")
async def create_report(report: ReportCreate, request: Request, current_user: User = Depends(get_current_user)):
    # Validate target exists
    if report.target_type == "post":
        try:
            Post.get_by_id(int(report.target_id))
        except:
            raise HTTPException(status_code=404, detail="Target post not found")
    elif report.target_type == "user":
        try:
            User.get_by_id(int(report.target_id))
        except:
            raise HTTPException(status_code=404, detail="Target user not found")
    # Add other types checks if needed
    
    new_report = Report.create(
        reporter=current_user,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason
    )
    
    return {
        "id": new_report.id,
        "reporter": {
            "id": current_user.id,
            "codemao_id": current_user.codemao_id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "description": current_user.description,
            "is_admin": current_user.is_admin
        },
        "target_type": new_report.target_type,
        "target_id": new_report.target_id,
        "reason": new_report.reason,
        "status": new_report.status,
        "created_at": new_report.created_at
    }

@app.get("/api/categories", response_model=List[CategoryRead])
def read_categories():
    return list(Category.select().dicts())

# --- Comments ---

@app.get("/api/posts/{post_id}/comments", response_model=List[CommentRead])
def read_comments(post_id: int, request: Request):
    # Check if post exists
    try:
        Post.get_by_id(post_id)
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")
        
    comments = (Comment
                .select(Comment, User)
                .join(User)
                .where((Comment.post_id == post_id) & (Comment.is_deleted == False))
                .order_by(Comment.created_at.desc()))
                
    # Determine current user for is_liked
    current_user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = int(payload.get("sub"))
        except:
            pass

    result = []
    for c in comments:
        is_liked = False
        if current_user_id:
            is_liked = CommentLike.select().where((CommentLike.user_id == current_user_id) & (CommentLike.comment == c)).exists()
            
        result.append({
            "id": c.id,
            "content": c.content,
            "created_at": c.created_at,
            "likes": c.likes,
            "is_liked": is_liked,
            "parent_id": c.parent_id,
            "user": {
                "id": c.user.id,
                "codemao_id": c.user.codemao_id,
                "username": c.user.username,
                "avatar_url": c.user.avatar_url,
                "description": c.user.description,
                "is_admin": c.user.is_admin
            }
        })
    return result

@app.post("/api/posts/{post_id}/like")
async def like_post(post_id: int, current_user: User = Depends(get_current_user)):
    try:
        post = Post.get_by_id(post_id)
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = PostLike.get_or_none(PostLike.user == current_user, PostLike.post == post)
    
    if existing_like:
        existing_like.delete_instance()
        post.likes = max(0, post.likes - 1)
        post.save()
        return {"status": "unliked", "likes": post.likes}
    else:
        PostLike.create(user=current_user, post=post)
        post.likes += 1
        post.save()
        
        # Notify owner
        if post.user.id != current_user.id:
             Notification.create(
                recipient=post.user,
                sender=current_user,
                type="like",
                message=f"liked your post: {post.title}",
                target_id=post.id,
                target_type="post"
            )
        
        return {"status": "liked", "likes": post.likes}

@app.post("/api/posts/comments/{comment_id}/like")
async def like_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    try:
        comment = Comment.get_by_id(comment_id)
    except Comment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")

    existing_like = CommentLike.get_or_none(CommentLike.user == current_user, CommentLike.comment == comment)
    
    if existing_like:
        existing_like.delete_instance()
        comment.likes = max(0, comment.likes - 1)
        comment.save()
        return {"status": "unliked", "likes": comment.likes}
    else:
        CommentLike.create(user=current_user, comment=comment)
        comment.likes += 1
        comment.save()
        return {"status": "liked", "likes": comment.likes}

@app.post("/api/posts/comments/{comment_id}/report")
async def report_comment(comment_id: int, report: ReportCreate, current_user: User = Depends(get_current_user)):
    try:
        comment = Comment.get_by_id(comment_id)
    except Comment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    Report.create(
        reporter=current_user,
        target_type="comment",
        target_id=str(comment.id),
        reason=report.reason
    )
    
    return {"status": "reported"}

@app.delete("/api/posts/{post_id}/comments/{comment_id}")
@limiter.limit("10/minute")
async def delete_comment(post_id: int, comment_id: int, request: Request, current_user: User = Depends(get_current_user)):
    try:
        comment = Comment.get_by_id(comment_id)
        if comment.post_id != post_id:
            raise HTTPException(status_code=400, detail="Comment does not belong to this post")
            
        if comment.user.id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        # Soft delete
        comment.is_deleted = True
        comment.content = "[This comment has been deleted]"
        comment.save()
        
        return {"status": "deleted"}
    except Comment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")

@app.get("/api/trending/posts", response_model=List[PostRead])
@limiter.limit("20/minute")
def get_trending_posts(request: Request):
    # Enhanced trending algorithm with time decay
    # Score = (likes * 2 + views) * time_decay_factor
    # Time decay: newer content gets higher scores
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Get posts from last 7 days with engagement
    # We calculate score in Python to avoid complex SQL date math issues across DBs
    try:
        recent_posts = list(Post.select().where(Post.created_at >= week_ago))
        print(f"Found {len(recent_posts)} recent posts")
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []
    
    def calculate_score(p):
        try:
            if not p.created_at:
                return 0
                
            # Age in days
            # Ensure p.created_at is datetime
            created_at = p.created_at
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    try:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                
            age = (now - created_at).total_seconds() / 86400
            # Engagement
            engagement = p.likes * 2 + p.views
            # Decay: Gravity 1.5
            return engagement / ((age + 1) ** 1.5)
        except Exception as e:
            print(f"Error calculating score for post {p.id}: {e}")
            return 0

    recent_posts.sort(key=calculate_score, reverse=True)
    posts = recent_posts[:12]
    
    # If not enough recent posts, fall back to global trending
    if len(posts) < 6:
        exclude_ids = [p.id for p in posts]
        additional_posts = (Post.select()
                           .where(Post.id.not_in(exclude_ids))
                           .order_by((Post.likes * 2 + Post.views).desc())
                           .limit(6 - len(posts)))
        posts = posts + list(additional_posts)
    
    return posts

@app.get("/api/trending/works", response_model=List[SearchResult])
@limiter.limit("20/minute")
def get_trending_works(request: Request):
    # Enhanced trending works with original author support
    from datetime import datetime, timedelta
    
    # Get trending works from last 30 days
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    
    # Fetch works in Python to calculate score
    try:
        recent_works = list(Work.select(Work, User).join(User).where(Work.created_at >= month_ago))
        print(f"Found {len(recent_works)} recent works")
    except Exception as e:
        print(f"Error fetching works: {e}")
        return []
    
    def calculate_score(w):
        try:
            if not w.created_at:
                return 0
                
            # Age in days
            created_at = w.created_at
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    try:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

            age = (now - created_at).total_seconds() / 86400
            # Engagement
            engagement = w.likes * 2 + w.views
            # Decay: Gravity 1.5
            return engagement / ((age + 1) ** 1.5)
        except Exception as e:
            print(f"Error calculating score for work {w.work_id}: {e}")
            return 0
        
    recent_works.sort(key=calculate_score, reverse=True)
    trending_works = recent_works[:12]
                
    results = []
    
    def add_to_results(works_list):
        for w in works_list:
            # Use original author info if system-owned work
            if w.user.codemao_id == "0" and w.original_author_name:
                author_name = w.original_author_name
            else:
                author_name = w.user.username
                
            results.append(SearchResult(
                type="work",
                id=str(w.work_id),
                title=w.name,
                subtitle=f"by {author_name}",
                url=f"https://shequ.codemao.cn/work/{w.work_id}",
                image_url=w.cover_url
            ))
            
    add_to_results(trending_works)
        
    # If not enough recent works, add popular works from all time
    if len(results) < 6:
        exclude_ids = [w.id for w in trending_works]
        additional_works = (Work.select(Work, User)
                             .join(User)
                             .where(Work.id.not_in(exclude_ids))
                             .order_by((Work.likes * 2 + Work.views).desc())
                             .limit(6 - len(results)))
        
        add_to_results(additional_works)
    
    return results

@app.post("/api/posts/{post_id}/comments", response_model=CommentRead)
@limiter.limit("10/minute")
async def create_comment(post_id: int, comment: CommentCreate, request: Request, current_user: User = Depends(get_current_user)):
    try:
        try:
            post = Post.get_by_id(post_id)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Verify parent if exists
        parent = None
        if comment.parent_id:
            try:
                parent = Comment.get(Comment.id == comment.parent_id)
                if parent.post != post:
                     raise HTTPException(status_code=400, detail="Parent comment does not belong to this post")
            except Comment.DoesNotExist:
                raise HTTPException(status_code=404, detail="Parent comment not found")
                
        new_comment = Comment.create(
            content=comment.content,
            user=current_user,
            post=post,
            parent=parent,
            likes=0,
            is_deleted=False
        )
        
        # Notify Post Owner or Parent Commenter
        if parent and parent.user.id != current_user.id:
            Notification.create(
                recipient=parent.user,
                sender=current_user,
                type="reply",
                message=f"replied to your comment on: {post.title[:30]}...",
                target_id=post.id,
                target_type="post"
            )
        elif post.user.id != current_user.id:
            Notification.create(
                recipient=post.user,
                sender=current_user,
                type="comment",
                message=f"commented on your post: {post.title[:30]}...",
                target_id=post.id,
                target_type="post"
            )

        # Notify Mentioned Users
        # Regex to find @username pattern
        mentioned_usernames = set(re.findall(r'@(\w+)', comment.content))
        for username in mentioned_usernames:
            # Don't notify self or post owner (already notified above)
            if username == current_user.username:
                continue
                
            try:
                target_user = User.get(User.username == username)
                if target_user.id == post.user.id:
                    continue # Already notified as post owner
                    
                Notification.create(
                    recipient=target_user,
                    sender=current_user,
                    type="mention",
                    message=f"mentioned you in a comment on: {post.title[:30]}...",
                    target_id=post.id,
                    target_type="post"
                )
            except User.DoesNotExist:
                pass # User not found, ignore

        return {
        "id": new_comment.id,
        "content": new_comment.content,
        "created_at": new_comment.created_at,
        "likes": 0,
        "is_liked": False,
        "parent_id": new_comment.parent.id if new_comment.parent else None,
        "user": {
            "id": current_user.id,
            "codemao_id": current_user.codemao_id,
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "description": current_user.description,
            "is_admin": current_user.is_admin
        }
    }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
