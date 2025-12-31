import os
import sys

# Add the project root to path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Import the two Flask apps
from app import app as chatbot_app
from admin_portal.app import app as admin_app

# Configure the Admin App's URL structure when mounted
admin_app.config['APPLICATION_ROOT'] = '/admin'

# Define the merged application
# /      -> Chatbot
# /admin -> Admin Portal
application = DispatcherMiddleware(chatbot_app, {
    '/admin': admin_app
})

if __name__ == "__main__":
    # For local testing of the merged app
    run_simple('localhost', 5000, application, use_reloader=True, use_debugger=True)
