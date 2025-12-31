from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sys

# --- SHARED INTEGRATION ---
# Add parent directory to path to import shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from shared.database import db, init_db, User, Interaction, Admin

app = Flask(__name__)
app.secret_key = "super_secret_admin_key_change_in_prod" 

# Initialize Shared Database
# Note: passing database path in parent dir
init_db(app)

# Directories
DATA_DIR = os.path.join(parent_dir, "Data")        # For Alerts & ML Data
MASTER_DIR = os.path.join(parent_dir, "MasterData") # For Static Knowledge (CMS)

# --- ROUTES ---

@app.route("/")
def index():
    if "admin_user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Simple Hardcoded Auth for Prototype (Replace with DB check in Prod)
        # Or check against Admin table if seeded
        if username == "admin" and password == "admin123":
            session["admin_user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials!")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_user", None)
    return redirect(url_for("login"))

# --- MODULE 1: DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    if "admin_user" not in session:
        return redirect(url_for("login"))
    
    # Fetch Analytics
    total_users = User.query.count()
    total_interactions = Interaction.query.count()
    
    # Recent Logs
    recent_logs = Interaction.query.order_by(Interaction.timestamp.desc()).limit(10).all()
    
    return render_template("dashboard.html", 
                           total_users=total_users, 
                           total_interactions=total_interactions,
                           recent_logs=recent_logs)

# --- MODULE 2: CMS ---
@app.route("/cms", methods=["GET", "POST"])
def cms():
    if "admin_user" not in session: return redirect(url_for("login"))
    
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file part!")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No selected file!")
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            # Only allow specific files to be updated for safety
            allowed_files = ["vaccination_schedule.json", "symptom_Description.csv", "symptom_precaution.csv"]
            if filename in allowed_files:
                save_path = os.path.join(MASTER_DIR, filename)
                file.save(save_path)
                flash(f"✅ Successfully updated {filename}")
                
                # Ideally, trigger a reload in the main app (e.g., via a flag in DB or API call)
                # For now, just updating the file is enough for next restart/reload
            else:
                flash(f"⚠️ Error: Only {', '.join(allowed_files)} can be updated.")
                
    # List files
    files = []
    # List files
    files = []
    if os.path.exists(MASTER_DIR):
        files = [f for f in os.listdir(MASTER_DIR) if f.endswith('.json') or f.endswith('.csv')]
        
    return render_template("cms.html", files=files)

# --- MODULE 3: BROADCAST ---
@app.route("/broadcast", methods=["GET", "POST"])
def broadcast():
    if "admin_user" not in session: return redirect(url_for("login"))
    
    json_path = os.path.join(DATA_DIR, "manual_alerts.json")
    import json # Ensure json is imported
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "clear":
            # Clear all
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump([], f)
            flash("All alerts cleared.")
            
        else:
            # Add new alert
            title = request.form.get("title")
            message = request.form.get("message")
            severity = request.form.get("severity")
            
            new_alert = {
                "title": title,
                "message": message,
                "severity": severity,
                "active": True,
                "date": datetime.now().strftime("%d %b %Y")
            }
            
            current_alerts = []
            if os.path.exists(json_path):
                with open(json_path, "r", encoding='utf-8') as f:
                    try: current_alerts = json.load(f)
                    except: pass
            
            current_alerts.insert(0, new_alert) # Add to top
            
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump(current_alerts, f, indent=4)
            flash("📢 Alert Broadcasted Successfully!")
            
    # Load current
    current_alerts = []
    if os.path.exists(json_path):
        with open(json_path, "r", encoding='utf-8') as f:
            try: current_alerts = json.load(f)
            except: pass
            
    return render_template("broadcast.html", alerts=current_alerts)

# --- MODULE 4: QUALITY CONTROL ---
@app.route("/qc", methods=["GET", "POST"])
def qc():
    if "admin_user" not in session: return redirect(url_for("login"))
    
    if request.method == "POST":
        inter_id = request.form.get("interaction_id")
        correction = request.form.get("correction")
        
        if inter_id and correction:
            interaction = Interaction.query.get(inter_id)
            if interaction:
                interaction.admin_correction = correction
                interaction.flagged_for_review = False # Mark as reviewed
                db.session.commit()
                flash("✅ Correction saved. AI will learn from this in future updates.")
            
    # Fetch "Red Flag" interactions: Low confidence (< 60%) or Explicitly Flagged
    flagged_logs = Interaction.query.filter(
        (Interaction.confidence_score < 60) | (Interaction.flagged_for_review == True)
    ).order_by(Interaction.timestamp.desc()).limit(50).all()
    
    return render_template("qc.html", logs=flagged_logs)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
