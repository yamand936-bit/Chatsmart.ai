import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
