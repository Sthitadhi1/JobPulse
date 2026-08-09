import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("[JobPulse] Starting Open Source Real-Time Discovery Engine")
    print("[Dashboard] Web UI: http://127.0.0.1:8000/dashboard/")
    print("[API Specs] OpenAPI Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
