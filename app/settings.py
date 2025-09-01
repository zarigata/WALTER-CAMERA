from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # OBS WebSocket Settings
    obs_host: str = os.getenv("OBS_HOST", "localhost")
    obs_port: int = int(os.getenv("OBS_PORT", 4455))
    obs_password: str = os.getenv("OBS_PASSWORD", "")

    # Video File Management
    # Defaulting to project's videos directory
    video_base_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'videos'))
    latest_video_folder: str = os.path.join(video_base_path, 'latest')
    old_videos_folder: str = os.path.join(video_base_path, 'old')

    recording_path: str = os.getenv("RECORDING_PATH", "")

    # Recording Workflow
    standby_delay: int = int(os.getenv("STANDBY_DELAY", 3))
    recording_duration: int = int(os.getenv("RECORDING_DURATION", 10))

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# Ensure video directories exist
os.makedirs(settings.latest_video_folder, exist_ok=True)
os.makedirs(settings.old_videos_folder, exist_ok=True)
