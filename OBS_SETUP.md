# OBS Setup Instructions

1. Download and install OBS Studio from https://obsproject.com/

2. Install the obs-websocket plugin from https://github.com/Palakis/obs-websocket/releases

3. Open OBS Studio.

4. Create three scenes: "after", "standby", "recording". Set "after" as the default scene.

5. Go to Tools > WebSocket Server Settings.

6. Enable WebSocket server, set port to 4444, set password if desired (update in backend/app.py).

7. In OBS, go to Settings > Output > Recording.

8. Set Recording Path to the absolute path of backend/videos/ (e.g., g:\PROJETOS\petrobras\backend\videos\)

9. Set Recording Format to MP4.

10. Start OBS.

11. Run the backend: python app.py or via Docker.

12. Access the web interface at http://localhost:8000/tablet for control, /admin for settings, /download for download.
