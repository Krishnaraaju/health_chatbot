from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize SQLAlchemy with no settings (will be configured by the app)
db = SQLAlchemy()

class User(db.Model):
    """Stores basic user information."""
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(100), unique=True, nullable=False) # Could be Session ID or Phone Number
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100), nullable=True) # Optional: District/City
    
    interactions = db.relationship('Interaction', backref='user', lazy=True)

class Interaction(db.Model):
    """Logs individual messages between User and Chatbot."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    
    intent_detected = db.Column(db.String(50), nullable=True) # e.g., "symptom_check", "general_chat"
    confidence_score = db.Column(db.Float, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True) # "Positive", "Neutral", "Negative"
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Flags for Admin Review
    flagged_for_review = db.Column(db.Boolean, default=False)
    admin_correction = db.Column(db.Text, nullable=True) # If admin overrides the answer

class Admin(db.Model):
    """Admin users for the portal."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="superadmin")

def init_db(app, db_path="database.db"):
    """
    Initializes the database with the given Flask app.
    Ensures the DB file is created in the shared directory.
    """
    if not os.path.isabs(db_path):
        # Default to a 'storage' folder in the parent directory or same directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level if needed, or keep it in shared. 
        # Let's keep it in 'instance' or root. 
        # For simplicity, let's put it in the same folder as app.py (parent of shared)
        project_root = os.path.dirname(base_dir) 
        db_path = os.path.join(project_root, "database.db")

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print(f"✅ Database initialized at: {db_path}")
