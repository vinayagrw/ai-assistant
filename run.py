from app.api.main import app

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,  # Enable debug mode for development
        threaded=True
        # processes=MAX_WORKERS  # Use multiple processes
    ) 
