import os
import sys
from pathlib import Path
import subprocess

def run_chroma_admin():
    """Run the ChromaDB Admin interface"""
    # Check if vector_db exists
    vector_db_path = Path("vector_db")
    if not vector_db_path.exists():
        print(f"Vector database not found at {vector_db_path}")
        return

    # Install required packages
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "pandas"], check=True)

    # Start Streamlit
    print("Starting ChromaDB Admin...")
    print("The interface will be available at http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    
    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "scripts/chroma_admin_app.py"
    ])

if __name__ == "__main__":
    run_chroma_admin() 