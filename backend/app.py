from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import asyncio
import os
import shutil
from obswebsocket import obsws, requests

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# OBS WebSocket settings
OBS_HOST = "localhost"
OBS_PORT = 4444
OBS_PASSWORD = ""

# Recording settings
RECORDING_DURATION = 10  # seconds
DELAY_BEFORE_RECORDING = 3  # seconds

# Video directories
VIDEO_DIR = "videos"
LATEST_DIR = os.path.join(VIDEO_DIR, "latest")
OLD_DIR = os.path.join(VIDEO_DIR, "old")

os.makedirs(LATEST_DIR, exist_ok=True)
os.makedirs(OLD_DIR, exist_ok=True)

# Mount videos for download
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")

def get_obs_client():
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
    ws.connect()
    return ws

async def recording_workflow():
    ws = get_obs_client()
    try:
        # Switch to standby
        ws.call(requests.SetCurrentScene("standby"))
        await asyncio.sleep(DELAY_BEFORE_RECORDING)
        
        # Switch to recording and start
        ws.call(requests.SetCurrentScene("recording"))
        ws.call(requests.StartRecording())
        await asyncio.sleep(RECORDING_DURATION)
        
        # Stop recording and switch back
        ws.call(requests.StopRecording())
        ws.call(requests.SetCurrentScene("after"))
        
        # Wait a bit for file to be written
        await asyncio.sleep(2)
        
        # Video management
        files = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
        if files:
            # Sort by modification time, get latest
            files.sort(key=lambda x: os.path.getmtime(os.path.join(VIDEO_DIR, x)), reverse=True)
            new_video = files[0]
            
            # Move old latest to old
            latest_files = os.listdir(LATEST_DIR)
            for f in latest_files:
                shutil.move(os.path.join(LATEST_DIR, f), os.path.join(OLD_DIR, f))
            
            # Move new to latest
            shutil.move(os.path.join(VIDEO_DIR, new_video), os.path.join(LATEST_DIR, new_video))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ws.disconnect()

@app.post("/start_recording")
async def start_recording():
    asyncio.create_task(recording_workflow())
    return {"status": "Recording started"}

@app.get("/latest_video")
async def get_latest_video():
    latest_files = os.listdir(LATEST_DIR)
    if latest_files:
        return {"url": f"/videos/latest/{latest_files[0]}"}
    return {"error": "No video available"}

@app.get("/old_videos")
async def get_old_videos():
    old_files = os.listdir(OLD_DIR)
    return {"videos": [f"/videos/old/{f}" for f in old_files]}

@app.get("/admin")
async def admin_page():
    return FileResponse("frontend/static/admin.html")

@app.get("/tablet")
async def tablet_page():
    return FileResponse("frontend/static/tablet.html")

@app.get("/download")
async def download_page():
    return FileResponse("frontend/static/download.html")

# Placeholder for settings
settings = {
    "obs_host": OBS_HOST,
    "obs_port": OBS_PORT,
    "recording_duration": RECORDING_DURATION,
    "delay": DELAY_BEFORE_RECORDING
}

@app.get("/admin/settings")
async def get_settings():
    return settings

@app.post("/admin/settings")
async def update_settings(request: Request):
    data = await request.json()
    global OBS_HOST, OBS_PORT, RECORDING_DURATION, DELAY_BEFORE_RECORDING
    OBS_HOST = data.get("obs_host", OBS_HOST)
    OBS_PORT = data.get("obs_port", OBS_PORT)
    RECORDING_DURATION = data.get("recording_duration", RECORDING_DURATION)
    DELAY_BEFORE_RECORDING = data.get("delay", DELAY_BEFORE_RECORDING)
    return {"status": "Settings updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
