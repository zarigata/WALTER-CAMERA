import asyncio
import logging
import os
import time
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.obs_controller import obs_controller
from app.file_manager import file_manager
from app.settings import settings, Settings

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Connecting to OBS...")
    if not obs_controller.connect():
        logging.warning("Could not connect to OBS. Some features may not work.")
    # Set initial scene
    obs_controller.set_scene("after")
    yield
    # Shutdown
    logging.info("Disconnecting from OBS...")
    obs_controller.disconnect()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# --- Recording Workflow ---
async def recording_flow():
    """The main logic for the recording sequence."""
    try:
        logging.info("Starting recording flow...")
        
        obs_controller.set_scene("standby")
        await asyncio.sleep(settings.standby_delay)

        obs_controller.set_scene("recording")
        obs_controller.start_recording()
        await asyncio.sleep(settings.recording_duration)

        obs_controller.stop_recording()
        obs_controller.set_scene("after")

        # Move the newly created video to latest folder after recording is complete
        await asyncio.sleep(2) 
        file_manager.move_newest_to_latest()
        logging.info("Recording flow completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during the recording flow: {e}")
        # Ensure we return to a safe state
        obs_controller.set_scene("after")

# --- API Endpoints ---
@app.post("/api/recording/start")
async def start_recording_endpoint(background_tasks: BackgroundTasks):
    """Endpoint to trigger the recording flow as a background task."""
    background_tasks.add_task(recording_flow)
    return JSONResponse(content={"message": "Recording process started."}, status_code=202)

@app.get("/api/videos/latest")
async def get_latest_video():
    """Endpoint to get the latest video file."""
    latest_video_path = file_manager.get_latest_video_path()
    if latest_video_path and os.path.exists(latest_video_path):
        filename = os.path.basename(latest_video_path)
        return FileResponse(
            path=latest_video_path,
            filename=filename,
            media_type='video/mp4',
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    raise HTTPException(status_code=404, detail="No latest video found.")

@app.post("/api/videos/move-to-old")
async def move_latest_to_old():
    """Endpoint to move the latest video to the old folder."""
    try:
        file_manager.move_old_videos()
        return JSONResponse(content={"message": "Video moved to old folder."}, status_code=200)
    except Exception as e:
        logging.error(f"Error moving video to old folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to move video.")

@app.get("/api/videos/old")
async def get_old_videos():
    """Endpoint to get a list of old video filenames."""
    return {"videos": file_manager.get_old_videos_list()}

@app.get("/api/settings")
async def get_settings():
    """Returns the current application settings."""
    return settings.dict()

@app.post("/api/settings")
async def update_settings(new_settings: Settings):
    """Updates application settings. Note: This is a simplified implementation."""
    global settings
    settings = new_settings
    # Here you would typically save this to a file or a more persistent store
    # For now, it only updates the in-memory settings object
    logging.info(f"Settings updated: {settings.dict()}")
    return {"message": "Settings updated successfully", "settings": settings.dict()}

# --- Static Files Mounting ---
# The order of mounting is important. Most specific routes should come first.

# Serve static video files
app.mount("/videos/latest", StaticFiles(directory=settings.latest_video_folder), name="videos_latest")
app.mount("/videos/old", StaticFiles(directory=settings.old_videos_folder), name="videos_old")

# Serve frontend assets
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Serve frontend pages
app.mount("/admin", StaticFiles(directory="frontend/admin", html=True), name="admin")
app.mount("/tablet", StaticFiles(directory="frontend/tablet", html=True), name="tablet")
app.mount("/download", StaticFiles(directory="frontend/download", html=True), name="download")

# Serve the main index page at the root
@app.get("/", response_class=FileResponse)
async def read_index():
    return "frontend/index.html"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
