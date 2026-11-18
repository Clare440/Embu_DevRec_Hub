
import sys
import os

# Add the project directory to Python's path
path = '/home/CLAREWAMBUI/EMBU_CLAUDE_files'

if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['SECRET_KEY'] = 'clare-secret-key-12345'
os.environ['HMAC_SECRET'] = 'clare-hmac-secret-67890'

# Import Flask applisscation
from app import app as application
