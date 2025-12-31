import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

# Mock dependencies to bypass import errors during verification
from unittest.mock import MagicMock
sys.modules['deep_translator'] = MagicMock()
sys.modules['groq_service'] = MagicMock()
sys.modules['alert_service'] = MagicMock()
# Also mock joblib/sklearn if needed, but let's try these first

from app import app
from shared.database import db, Interaction, User

def verify():
    print("🔎 Verifying Database Integration...")
    
    db_path = os.path.join(os.getcwd(), "database.db")
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at {db_path}")
        # Try creating it manually to see if init works
        print("   Attempting to initialize...")
        with app.app_context():
            db.create_all()
            
    if os.path.exists(db_path):
        print(f"✅ Database file found at {db_path}")
    
    with app.app_context():
        try:
            user_count = User.query.count()
            inter_count = Interaction.query.count()
            print(f"✅ Connection Successful!")
            print(f"📊 Current Stats: {user_count} Users, {inter_count} Interactions")
            
            # Test Write
            print("📝 Testing Write Operation...")
            test_user = User(user_identifier="test_verifier")
            db.session.add(test_user)
            db.session.commit()
            
            test_inter = Interaction(
                user_id=test_user.id,
                user_message="Test Message",
                bot_response="Test Response",
                intent_detected="test",
                confidence_score=1.0
            )
            db.session.add(test_inter)
            db.session.commit()
            print("✅ Write Successful!")
            
            # Cleanup
            db.session.delete(test_inter)
            db.session.delete(test_user)
            db.session.commit()
            print("🧹 Cleanup Successful!")
            
        except Exception as e:
            print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    verify()
