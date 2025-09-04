import os
import shutil
import glob
import logging
from app.settings import settings

class FileManager:
    def __init__(self):
        self.latest_folder = settings.latest_video_folder
        self.old_folder = settings.old_videos_folder
        self.cloud_folder = settings.cloud_folder
        # This path needs to be configured in OBS settings
        self.recording_path = settings.recording_path 

    def move_old_videos(self):
        """Moves all files from the 'latest' folder to the 'old' folder."""
        files = glob.glob(os.path.join(self.latest_folder, '*'))
        for f in files:
            try:
                # Copy to cloud folder first
                shutil.copy(f, self.cloud_folder)
                logging.info(f"Copied video {f} to {self.cloud_folder}")
                
                # Then move to old folder
                shutil.move(f, self.old_folder)
                logging.info(f"Moved old video {f} to {self.old_folder}")
            except Exception as e:
                logging.error(f"Error processing file {f}: {e}")

    def get_newest_recording(self) -> str | None:
        """Finds the most recent video file in the OBS recording path."""
        if not os.path.isdir(self.recording_path):
            logging.error(f"Recording path not found: {self.recording_path}")
            return None
        
        # Common video file extensions
        video_extensions = ('*.mkv', '*.mp4', '*.flv', '*.mov', '*.avi')
        list_of_files = []
        for ext in video_extensions:
            list_of_files.extend(glob.glob(os.path.join(self.recording_path, ext)))

        if not list_of_files:
            logging.warning("No recordings found in the recording path.")
            return None

        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file

    def move_newest_to_latest(self):
        """Moves the newest recording to the 'latest' folder."""
        newest_video = self.get_newest_recording()
        if newest_video:
            try:
                shutil.move(newest_video, self.latest_folder)
                logging.info(f"Moved newest video {newest_video} to {self.latest_folder}")
            except Exception as e:
                logging.error(f"Error moving newest video: {e}")

    def get_latest_video_path(self) -> str | None:
        """Gets the path of the video in the 'latest' folder."""
        files = glob.glob(os.path.join(self.latest_folder, '*'))
        if files:
            return files[0]
        return None

    def get_old_videos_list(self) -> list[str]:
        """Returns a list of filenames in the 'old' folder."""
        files = glob.glob(os.path.join(self.old_folder, '*'))
        return [os.path.basename(f) for f in files]

# Singleton instance
file_manager = FileManager()
