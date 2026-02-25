
from peewee import *
from datetime import datetime
import os

db_path = os.getenv('DB_PATH', 'database.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    # Codemao ID as primary identifier
    codemao_id = CharField(unique=True, index=True) 
    username = CharField() # Codemao username/nickname
    avatar_url = CharField(null=True)
    description = TextField(null=True) # User bio
    codemao_token = TextField(null=True) # Store Codemao OAuth token
    # --- Secure Credential Storage ---
    login_identity = CharField(null=True) # The ID used to login (phone/email/username)
    encrypted_password = TextField(null=True) # Encrypted password (AES-256)
    # ---------------------------------
    is_admin = BooleanField(default=False)
    is_banned = BooleanField(default=False)
    ban_reason = TextField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField(default=datetime.utcnow)

class Category(BaseModel):
    name = CharField(unique=True)
    slug = CharField(unique=True)

class Post(BaseModel):
    title = CharField()
    content = TextField() # Markdown content
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    user = ForeignKeyField(User, backref='posts')
    category = ForeignKeyField(Category, backref='posts', null=True)
    
    views = IntegerField(default=0)
    likes = IntegerField(default=0)
    is_pinned = BooleanField(default=False) # New field for pinning posts

class Comment(BaseModel):
    content = TextField()
    created_at = DateTimeField(default=datetime.utcnow)
    likes = IntegerField(default=0, null=True) # Make nullable for compatibility
    is_deleted = BooleanField(default=False, null=True) # Make nullable for compatibility
    
    user = ForeignKeyField(User, backref='comments')
    post = ForeignKeyField(Post, backref='comments')
    parent = ForeignKeyField('self', backref='replies', null=True)

class PostLike(BaseModel):
    user = ForeignKeyField(User, backref='liked_posts')
    post = ForeignKeyField(Post, backref='post_likes')
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = (
            (('user', 'post'), True),
        )

class CommentLike(BaseModel):
    user = ForeignKeyField(User, backref='liked_comments')
    comment = ForeignKeyField(Comment, backref='comment_likes')
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = (
            (('user', 'comment'), True),
        )

class Work(BaseModel):
    work_id = IntegerField(unique=True) # Codemao Work ID
    name = CharField()
    cover_url = CharField(null=True)
    description = TextField(null=True)
    bcm_url = CharField(null=True) # User provided
    user = ForeignKeyField(User, backref='works') # Internal owner
    original_author_id = CharField(null=True) # Original Codemao author ID
    original_author_name = CharField(null=True) # Original Codemao author name
    original_author_avatar = CharField(null=True) # Original Codemao author avatar
    created_at = DateTimeField(default=datetime.utcnow)
    likes = IntegerField(default=0)
    views = IntegerField(default=0)

class Notification(BaseModel):
    recipient = ForeignKeyField(User, backref='notifications')
    sender = ForeignKeyField(User, backref='sent_notifications')
    type = CharField() # 'reply', 'like', 'system', 'follow'
    message = CharField()
    target_id = IntegerField(null=True) # Post ID or Work ID or User ID
    target_type = CharField(null=True) # 'post', 'work', 'user'
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

class Follow(BaseModel):
    follower = ForeignKeyField(User, backref='following')
    followed = ForeignKeyField(User, backref='followers')
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = (
            (('follower', 'followed'), True),
        )

# Review Model Deleted - Replaced by WorkComment

class WorkComment(BaseModel):
    user = ForeignKeyField(User, backref='work_comments')
    work = ForeignKeyField(Work, backref='work_comments')
    content = TextField()
    parent = ForeignKeyField('self', backref='replies', null=True)
    likes = IntegerField(default=0)
    is_deleted = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

class WorkLike(BaseModel):
    user = ForeignKeyField(User, backref='liked_works')
    work = ForeignKeyField(Work, backref='work_likes')
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = (
            (('user', 'work'), True),
        )

class WorkCommentLike(BaseModel):
    user = ForeignKeyField(User, backref='liked_work_comments')
    comment = ForeignKeyField(WorkComment, backref='comment_likes')
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        indexes = (
            (('user', 'comment'), True),
        )

class Banner(BaseModel):
    title = CharField()
    image_url = CharField() # background_url
    link_url = CharField() # target_url
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)

class BcmComment(BaseModel):
    bcm_post_id = CharField() # Codemao Post ID (string)
    content = TextField()
    created_at = DateTimeField(default=datetime.utcnow)
    user = ForeignKeyField(User, backref='bcm_comments')

class OAuthApplication(BaseModel):
    name = CharField()
    client_id = CharField(unique=True, index=True)
    client_secret = CharField() # Hashed ideally, but for now plaintext or simple hash
    redirect_uris = TextField() # Comma separated
    owner = ForeignKeyField(User, backref='oauth_apps')
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)

class OAuthCode(BaseModel):
    code = CharField(unique=True, index=True)
    client_id = CharField()
    user = ForeignKeyField(User, backref='oauth_codes')
    redirect_uri = CharField()
    expires_at = DateTimeField()
    scope = CharField(default="user_info")

class Announcement(BaseModel):
    content = TextField()
    type = CharField(default="banner") # banner, modal, toast
    active = BooleanField(default=True)
    created_by = ForeignKeyField(User, backref='announcements')
    created_at = DateTimeField(default=datetime.utcnow)

class SystemSetting(BaseModel):
    key = CharField(unique=True)
    value = TextField()

class Report(BaseModel):
    reporter = ForeignKeyField(User, backref='reports')
    target_type = CharField() # 'post', 'comment', 'work', 'user'
    target_id = CharField() # ID can be string (for external) or int
    reason = TextField()
    status = CharField(default="pending") # pending, resolved, rejected
    created_at = DateTimeField(default=datetime.utcnow)
    resolved_at = DateTimeField(null=True)
    resolved_by = ForeignKeyField(User, backref='resolved_reports', null=True)

class ChatMessage(BaseModel):
    user = ForeignKeyField(User, backref='chat_messages')
    content = TextField()
    msg_type = CharField(default="text") # text, image, system
    created_at = DateTimeField(default=datetime.utcnow)
    
    class Meta:
        indexes = (
            (('created_at',), False),
        )

class DirectMessage(BaseModel):
    sender = ForeignKeyField(User, backref='sent_dms')
    recipient = ForeignKeyField(User, backref='received_dms')
    content = TextField()
    msg_type = CharField(default="text")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    
    class Meta:
        indexes = (
            (('sender', 'recipient', 'created_at'), False),
        )

class FriendRequest(BaseModel):
    sender = ForeignKeyField(User, backref='sent_friend_requests')
    recipient = ForeignKeyField(User, backref='received_friend_requests')
    status = CharField(default="pending") # pending, accepted, rejected
    created_at = DateTimeField(default=datetime.utcnow)
    
    class Meta:
        indexes = (
            (('sender', 'recipient'), True), # Unique constraint to prevent duplicate requests
        )

def create_tables():
    with db:
        # Review removed from list
        db.create_tables([User, Category, Post, Comment, PostLike, CommentLike, Work, Notification, Follow, WorkComment, WorkLike, WorkCommentLike, Banner, BcmComment, OAuthApplication, OAuthCode, Announcement, SystemSetting, Report, ChatMessage, DirectMessage, FriendRequest])
