"""
Database Models Module - Contains SQLAlchemy models for the application database
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON as PostgresJSON

from app import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    # role column removed as it doesn't exist in the public schema
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    integration_configs = db.relationship('IntegrationConfig', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    subscriptions = db.relationship('UserSubscription', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Profile(db.Model):
    """Profile model for user account information"""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(128))
    account_setup_complete = db.Column(db.Boolean, default=False)
    welcome_email_sent = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Profile {self.email}>'

class Conversation(db.Model):
    """Conversation model for tracking user-client conversations"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    client_name = db.Column(db.String(128), nullable=False)
    client_company = db.Column(db.String(128))
    status = db.Column(db.String(20), default='active')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.platform} - {self.client_name}>'

class Message(db.Model):
    """Message model for storing messages in conversations"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # user, client, ai
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_type}>'

class Task(db.Model):
    """Task model for user follow-up tasks"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(10), default='medium')
    platform = db.Column(db.String(20), nullable=False)
    client_name = db.Column(db.String(128), nullable=False)
    due_date = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.id}: {self.status} - {self.description[:20]}>'

class Response(db.Model):
    """Response model for AI-generated responses"""
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    used = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Response {self.id}: {self.platform}>'

class IntegrationConfig(db.Model):
    """IntegrationConfig model for integration configurations"""
    __tablename__ = 'integration_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    integration_type = db.Column(db.String(50), nullable=False)
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'integration_type', name='unique_user_integration'),
    )
    
    def __repr__(self):
        return f'<IntegrationConfig {self.integration_type}: {self.status}>'

class KnowledgeFile(db.Model):
    """KnowledgeFile model for user knowledge base documents"""
    __tablename__ = 'knowledge_files'
    
    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    file_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<KnowledgeFile {self.file_name}>'

class SubscriptionFeature(db.Model):
    """SubscriptionFeature model for individual features offered in subscription tiers"""
    __tablename__ = 'subscription_features'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionFeature {self.name}>'

class SubscriptionTier(db.Model):
    """SubscriptionTier model for defining subscription plans"""
    __tablename__ = 'subscription_tiers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.JSON, nullable=False)
    platforms = db.Column(db.JSON, nullable=False)
    monthly_price = db.Column(db.Float)
    annual_price = db.Column(db.Float)
    is_popular = db.Column(db.Boolean, default=False)
    trial_days = db.Column(db.Integer, default=0)
    max_users = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    feature_limits = db.Column(db.JSON)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_subscriptions = db.relationship('UserSubscription', backref='subscription_tier', lazy='dynamic')
    
    def __repr__(self):
        return f'<SubscriptionTier {self.name}: ${self.price}>'

class Subscription(db.Model):
    """Subscription model for user subscriptions - compatible with older code"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    subscription_id = db.Column(db.String(100))
    payment_method_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Subscription {self.id}: {self.plan_type} ({self.status})>'
        
class UserSubscription(db.Model):
    """UserSubscription model for user subscription information"""
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tiers.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    payment_method_id = db.Column(db.String(100))
    billing_cycle = db.Column(db.String(20), default='monthly')
    auto_renew = db.Column(db.Boolean, default=True)
    trial_end_date = db.Column(db.DateTime)
    last_billing_date = db.Column(db.DateTime)
    next_billing_date = db.Column(db.DateTime)
    cancellation_date = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('SubscriptionInvoice', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'subscription_tier_id', name='unique_user_subscription'),
    )
    
    def __repr__(self):
        return f'<UserSubscription {self.user_id}: {self.status}>'

class SubscriptionInvoice(db.Model):
    """SubscriptionInvoice model for tracking subscription payments"""
    __tablename__ = 'subscription_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    billing_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime)
    payment_method_id = db.Column(db.String(100))
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    items = db.Column(db.JSON, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionInvoice {self.invoice_number}: ${self.amount} {self.currency}>'

class AdminUser(db.Model):
    """AdminUser model for administrative user information"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), default='support')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminUser {self.username}: {self.role}>'

class Interaction(db.Model):
    """Interaction model for tracking user-client interactions"""
    __tablename__ = 'interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    client_name = db.Column(db.String(128), nullable=False)
    interaction_type = db.Column(db.String(20), nullable=False)  # message, task, response
    related_id = db.Column(db.Integer)  # ID of the related message, task, or response
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Interaction {self.id}: {self.interaction_type}>'

class Payment(db.Model):
    """Payment model for tracking payment transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tiers.id'), nullable=False)
    # Optional reference to subscription if it exists already
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'))
    order_id = db.Column(db.String(100), unique=True)  # Our internal order ID
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly or annual
    payment_method = db.Column(db.String(100), default='pesapal')
    payment_provider_reference = db.Column(db.String(100))  # PesaPal tracking ID
    payment_date = db.Column(db.DateTime)  # When payment was completed
    invoice_url = db.Column(db.String(255))  # URL to invoice
    meta_data = db.Column(db.JSON)  # Additional data like tracking info, redirect URLs
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount} {self.currency} - {self.status}>'

class Setting(db.Model):
    """Setting model for storing system settings"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.JSON)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}>'

class KnowledgeItem(db.Model):
    """KnowledgeItem model for user knowledge base entries"""
    __tablename__ = 'knowledge_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # document, snippet, note, etc.
    tags = db.Column(db.JSON)
    meta_data = db.Column(db.JSON)  # Changed from 'metadata' (reserved name)
    source_file_id = db.Column(db.String(255), db.ForeignKey('knowledge_files.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_file = db.relationship('KnowledgeFile', backref='knowledge_items')
    
    def __repr__(self):
        return f'<KnowledgeItem {self.id}: {self.title[:30]}>'

class APIUsage(db.Model):
    """APIUsage model for tracking API usage for rate limiting and quotas"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)  # GET, POST, PUT, DELETE
    request_count = db.Column(db.Integer, default=0)
    last_request_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'endpoint', 'method', name='unique_user_endpoint_method'),
    )
    
    def __repr__(self):
        return f'<APIUsage {self.user_id}: {self.endpoint} ({self.request_count})>'

class Notification(db.Model):
    """Notification model for user notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # info, warning, error, success
    is_read = db.Column(db.Boolean, default=False)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title[:30]}>'

class Webhook(db.Model):
    """Webhook model for managing external webhooks"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    secret = db.Column(db.String(100))
    event_types = db.Column(db.JSON, nullable=False)  # Array of event types to trigger webhook
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Webhook {self.id}: {self.name}>'

class WebhookDelivery(db.Model):
    """WebhookDelivery model for tracking webhook delivery attempts"""
    __tablename__ = 'webhook_deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhooks.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    response_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    successful = db.Column(db.Boolean)
    attempt_count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    webhook = db.relationship('Webhook', backref='deliveries')
    
    def __repr__(self):
        return f'<WebhookDelivery {self.id}: {self.event_type} - {self.successful}>'

class BatchJob(db.Model):
    """BatchJob model for tracking batch processing jobs"""
    __tablename__ = 'batch_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)  # document_processing, export, etc.
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    total_items = db.Column(db.Integer, default=0)
    processed_items = db.Column(db.Integer, default=0)
    failed_items = db.Column(db.Integer, default=0)
    result_url = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BatchJob {self.id}: {self.job_type} - {self.status}>'

class UserActivity(db.Model):
    """UserActivity model for tracking user activity for analytics"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    meta_data = db.Column(db.JSON)  # Changed from 'metadata' (reserved name)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserActivity {self.id}: {self.user_id} - {self.activity_type}>'