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
    SLACK = "slack"
    EMAIL = "email"
    
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
    # Social media platforms
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    
    # Business tools
    EMAIL = "email"
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    SLACK = "slack"
    GOOGLE_ANALYTICS = "google_analytics"
    ZENDESK = "zendesk"
    SHOPIFY = "shopify"
    
    # Database connectors
    DATABASE_MYSQL = "mysql"
    DATABASE_POSTGRESQL = "postgresql"
    DATABASE_MONGODB = "mongodb"
    DATABASE_SQLSERVER = "sqlserver"
    
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
    filename: str
    file_size: int
    file_type: str
    content: str
    category: Optional[str] = None
    tags: Optional[Union[List[str], str]] = None
    binary_data: Optional[Union[Dict[str, Any], str]] = None
    metadata: Optional[Union[Dict[str, Any], str]] = None

class KnowledgeFileCreate(KnowledgeFileBase):
    pass

class KnowledgeFileUpdate(BaseModel):
    filename: Optional[str] = None
    file_type: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[Union[List[str], str]] = None
    binary_data: Optional[Union[Dict[str, Any], str]] = None
    metadata: Optional[Union[Dict[str, Any], str]] = None

class SubscriptionFeatureBase(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None

class SubscriptionFeatureCreate(SubscriptionFeatureBase):
    pass

class SubscriptionFeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class SubscriptionTierBase(BaseModel):
    name: str
    description: str
    price: float
    features: List[str]
    platforms: List[Platform]
    monthly_price: Optional[float] = None
    annual_price: Optional[float] = None
    is_popular: bool = False
    trial_days: int = 0
    max_users: Optional[int] = None
    is_active: bool = True
    feature_limits: Optional[Dict[str, int]] = None

class SubscriptionTierCreate(SubscriptionTierBase):
    pass

class SubscriptionTierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    features: Optional[List[str]] = None
    platforms: Optional[List[Platform]] = None
    monthly_price: Optional[float] = None
    annual_price: Optional[float] = None
    is_popular: Optional[bool] = None
    trial_days: Optional[int] = None
    max_users: Optional[int] = None
    is_active: Optional[bool] = None
    feature_limits: Optional[Dict[str, int]] = None

class UserSubscriptionBase(BaseModel):
    user_id: str
    subscription_tier_id: str
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    start_date: datetime
    end_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    billing_cycle: Optional[str] = "monthly"
    auto_renew: bool = True
    trial_end_date: Optional[datetime] = None
    last_billing_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    cancellation_date: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

class UserSubscriptionCreate(UserSubscriptionBase):
    pass

class UserSubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None
    subscription_tier_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None
    next_billing_date: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

class SubscriptionInvoiceBase(BaseModel):
    user_id: str
    subscription_id: str
    amount: float
    currency: str = "USD"
    status: str = "pending"
    billing_date: datetime
    paid_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    invoice_number: str
    items: List[Dict[str, Any]]

class SubscriptionInvoiceCreate(SubscriptionInvoiceBase):
    pass

class SubscriptionInvoiceUpdate(BaseModel):
    status: Optional[str] = None
    paid_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None

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
