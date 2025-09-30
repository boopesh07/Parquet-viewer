# backend/server.py
import sys
import os

# Add the parquetformatter_api to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'parquetformatter_api'))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)