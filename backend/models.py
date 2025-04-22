"""
Dana AI Platform - Database Models

This module defines the database models for the Dana AI Platform.
"""

from flask_login import UserMixin
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from backend.main import db

class User(UserMixin, db.Model):
    """User model for authentication and basic user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    auth_id = Column(UUID(as_uuid=True), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class IntegrationConfig(db.Model):
    """Integration configuration model for storing integration settings"""
    __tablename__ = 'integration_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    integration_type = Column(String(50), nullable=False)
    config = Column(JSON, nullable=True)
    status = Column(String(20), default='inactive')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<IntegrationConfig {self.integration_type} for user {self.user_id}>'

class KnowledgeFile(db.Model):
    """Knowledge file model for storing knowledge base files"""
    __tablename__ = 'knowledge_files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=True)
    storage_path = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<KnowledgeFile {self.filename} for user {self.user_id}>'

class TokenUsage(db.Model):
    """Token usage model for tracking AI token usage"""
    __tablename__ = 'token_usage'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    model = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TokenUsage {self.tokens_used} tokens for user {self.user_id}>'