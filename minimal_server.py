"""
Minimal MCP server for testing - use this if the full server has issues
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Minimal MCP Server")

@app.get("/")
async def root():
    return {"message": "Minimal MCP server is running", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "Server is running",
        "terraform_available": False  # We'll add this later
    }

@app.get("/terraform_state/ec2")
async def get_ec2_state():
    return {
        "message": "No EC2 instances found",
        "resource_type": "ec2",
        "resources": []
    }

if __name__ == "__main__":
    print("🚀 Starting Minimal MCP Server...")
    print("📡 Server: http://127.0.0.1:8000")
    print("📚 Docs: http://127.0.0.1:8000/docs")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)