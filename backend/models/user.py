"""
Dana AI Platform - User Model

This module defines the User model for authentication and user management.
"""

from flask_login import UserMixin
from sqlalchemy import Column, String, Integer, DateTime, Boolean, UUID as SQLAlchemyUUID
from sqlalchemy.sql import func
import uuid

from backend.main import db

class User(UserMixin, db.Model):
    """User model for authentication and basic user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    auth_id = Column(SQLAlchemyUUID(as_uuid=True), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    @classmethod
    def find_by_email(cls, email):
        """Find a user by email address"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_auth_id(cls, auth_id):
        """Find a user by auth_id"""
        return cls.query.filter_by(auth_id=auth_id).first()