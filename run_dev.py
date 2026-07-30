import uvicorn
import os
from fastapi.staticfiles import StaticFiles
from backend.app.main import app

# Mount static frontend assets
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    print("=" * 60)
    print("[JobPulse] Starting Open Source Real-Time Discovery Engine")
    print("[Dashboard] Web UI: http://127.0.0.1:8000/dashboard/")
    print("[API Specs] OpenAPI Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("run_dev:app", host="127.0.0.1", port=8000, reload=True)
