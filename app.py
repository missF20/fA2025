"""
Dana AI Platform

Main application module for the Dana AI Platform.
"""

import os
import logging
from flask import Flask, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)

# Configure application
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///dana_ai.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Register error handlers
@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 error"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def handle_server_error(error):
    """Handle 500 error"""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Register root routes
@app.route("/")
def index():
    """API root endpoint"""
    return jsonify({
        "name": "Dana AI API",
        "version": "1.0.0",
        "status": "online"
    })

@app.route("/status")
def status():
    """API status endpoint"""
    return jsonify({
        "status": "online",
        "database": "connected"
    })

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from models_db import User
    return User.query.get(int(user_id))

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        import models_db
        
        # Create tables
        db.create_all()
        logger.info("Database initialized")

# Initialize automation system
def init_automation():
    """Initialize the automation system"""
    try:
        # Import and initialize automation system
        from automation import initialize_sync
        initialize_sync()
        logger.info("Automation system initialized")
    except Exception as e:
        logger.error(f"Error initializing automation system: {e}")

# Register blueprints/routes
def register_blueprints():
    """Register all route blueprints"""
    try:
        # Import all blueprints
        from routes.ai_test import ai_test_bp
        from routes.subscription_management import subscription_mgmt_bp
        from routes.pdf_analysis import pdf_analysis_bp
        
        # Import new blueprint modules
        from routes.admin import admin_bp
        from routes.visualization import visualization_bp
        from routes.webhooks import webhooks_bp
        from routes.notifications import notifications_bp
        from routes.exports import exports_bp
        from routes.batch import batch_bp
        from routes.email import email_bp
        from routes.ai_responses import ai_response_bp
        
        # Register existing blueprints
        app.register_blueprint(ai_test_bp)
        app.register_blueprint(subscription_mgmt_bp)
        app.register_blueprint(pdf_analysis_bp)
        
        # Register new blueprints
        app.register_blueprint(admin_bp)
        app.register_blueprint(visualization_bp)
        app.register_blueprint(webhooks_bp)
        app.register_blueprint(notifications_bp)
        app.register_blueprint(exports_bp)
        app.register_blueprint(batch_bp)
        app.register_blueprint(email_bp)
        app.register_blueprint(ai_response_bp)
        
        logger.info("Route blueprints registered")
    except Exception as e:
        logger.error(f"Error registering blueprints: {e}")

# Initialize application
def init_app():
    """Initialize the application"""
    # Initialize database
    init_db()
    
    # Register blueprints
    register_blueprints()
    
    # Initialize automation system
    init_automation()
    
    logger.info("Application initialized")

# Initialize the application when this module is imported
init_app()