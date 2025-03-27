"""
Models module - Contains data models for validation
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enum types for use in models
class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    
class MessageSenderType(str, Enum):
    USER = "user"
    CLIENT = "client"
    AI = "ai"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class InteractionType(str, Enum):
    MESSAGE = "message"
    TASK = "task"
    RESPONSE = "response"
    
class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PENDING = "pending"

class IntegrationType(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    
class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"

class AdminRole(str, Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SUPPORT = "support"

# Base models
class ProfileBase(BaseModel):
    email: EmailStr
    company: Optional[str] = None
    account_setup_complete: bool = False
    welcome_email_sent: bool = False

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    company: Optional[str] = None
    account_setup_complete: Optional[bool] = None
    welcome_email_sent: Optional[bool] = None

class ConversationBase(BaseModel):
    user_id: str
    platform: Platform
    client_name: str
    client_company: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    client_name: Optional[str] = None
    client_company: Optional[str] = None
    status: Optional[ConversationStatus] = None

class MessageBase(BaseModel):
    conversation_id: str
    content: str
    sender_type: MessageSenderType

class MessageCreate(MessageBase):
    pass

class ResponseBase(BaseModel):
    user_id: str
    content: str
    platform: Platform

class ResponseCreate(ResponseBase):
    pass

class TaskBase(BaseModel):
    user_id: str
    description: str
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    platform: Platform
    client_name: str

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None

class InteractionBase(BaseModel):
    user_id: str
    platform: Platform
    client_name: str
    interaction_type: InteractionType

class InteractionCreate(InteractionBase):
    pass

class KnowledgeFileBase(BaseModel):
    user_id: str
    file_name: str
    file_size: int
    file_type: str
    content: str

class KnowledgeFileCreate(KnowledgeFileBase):
    pass

class SubscriptionTierBase(BaseModel):
    name: str
    description: str
    price: float
    features: List[str]
    platforms: List[Platform]

class SubscriptionTierCreate(SubscriptionTierBase):
    pass

class UserSubscriptionBase(BaseModel):
    user_id: str
    subscription_tier_id: str
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    start_date: datetime
    end_date: Optional[datetime] = None

class UserSubscriptionCreate(UserSubscriptionBase):
    pass

class UserSubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None

class AdminUserBase(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    role: AdminRole = AdminRole.SUPPORT

class AdminUserCreate(AdminUserBase):
    pass

class IntegrationsConfigBase(BaseModel):
    user_id: str
    integration_type: IntegrationType
    config: Dict[str, Any]
    status: IntegrationStatus = IntegrationStatus.PENDING

class IntegrationsConfigCreate(IntegrationsConfigBase):
    pass

class IntegrationsConfigUpdate(BaseModel):
    config: Optional[Dict[str, Any]] = None
    status: Optional[IntegrationStatus] = None

# Authentication models
class SignUp(BaseModel):
    email: EmailStr
    password: str
    company: Optional[str] = None

class Login(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordChange(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
