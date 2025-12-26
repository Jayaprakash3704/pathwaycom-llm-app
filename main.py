"""
Main Entry Point - FastAPI Server

Runs the REST API interface for incident management.

Usage:
    python main.py

Then access:
    - API docs: http://localhost:8000/docs
    - Dashboard: python client/dashboard.py overview
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from dotenv import load_dotenv


def main():
    """Start FastAPI server."""
    # Load environment variables
    load_dotenv()
    
    # Server configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print("="*80)
    print("  Pathway Incident Management API - Interface Layer")
    print("="*80)
    print(f"\n🌐 Starting API server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Docs: http://localhost:{port}/docs")
    print("\n📋 This interface layer:")
    print("   • Queries incidents from Pathway backend outputs")
    print("   • Provides human-in-the-loop override capabilities")
    print("   • Explains agent decisions using LLM")
    print("   • Exposes REST API for dashboards and external systems")
    print("\n⚙️  Backend connection:")
    print("   • Reads from: ./storage/incidents.json (Pathway outputs)")
    print("   • In production: Connect to Pathway REST connector or shared database")
    print("\n" + "="*80 + "\n")
    
    # Run server
    uvicorn.run(
        "app.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
