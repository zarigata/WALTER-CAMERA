import obsws_python as obs
import logging
from app.settings import settings

logging.basicConfig(level=logging.INFO)

class OBSController:
    def __init__(self):
        self.client = obs.ReqClient(
            host=settings.obs_host,
            port=settings.obs_port,
            password=settings.obs_password
        )

    def connect(self):
        try:
            # The ReqClient handles connection automatically
            # Just test the connection with a simple request
            self.client.get_version()
            logging.info("Connected to OBS WebSocket.")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to OBS WebSocket: {e}")
            return False

    def disconnect(self):
        # ReqClient handles disconnection automatically when object is destroyed
        logging.info("Disconnected from OBS WebSocket.")

    def set_scene(self, scene_name: str):
        try:
            self.client.set_current_program_scene(scene_name)
            logging.info(f"Switched to scene: {scene_name}")
        except Exception as e:
            logging.error(f"Failed to switch scene to {scene_name}: {e}")

    def start_recording(self):
        try:
            self.client.start_record()
            logging.info("Started recording.")
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")

    def stop_recording(self):
        try:
            self.client.stop_record()
            logging.info("Stopped recording.")
        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")

# Singleton instance
obs_controller = OBSController()
