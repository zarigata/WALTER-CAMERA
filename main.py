import os
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, send_from_directory, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pyautogui
import obswebsocket, obswebsocket.requests
from obswebsocket import obsws, requests

# Configuration
VIDEO_FOLDER = "videos"
OLD_VIDEO_FOLDER = "old_videos"
MAIN_PORT = 5000
CONFIG_PORT = 5001
BIG_SCREEN_PORT = 5002
DOWNLOAD_PORT = 5003
TABLET_PORT = 5004

# Ensure directories exist
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(OLD_VIDEO_FOLDER, exist_ok=True)

# Global variables
obs_client = None
current_video = None
system_status = "ready"
workflow_step = "Ready for next session"
progress = 0
is_workflow_running = False

# Status tracking
status_lock = threading.Lock()

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_file and event.src_path.endswith(('.mp4', '.avi', '.mkv')):
            global current_video
            if current_video:
                # Move old video to old_videos folder
                old_path = os.path.join(OLD_VIDEO_FOLDER, os.path.basename(current_video))
                os.rename(current_video, old_path)
            current_video = event.src_path

def start_obs_connection():
    global obs_client
    try:
        obs_client = obsws("localhost", 4444, "password")  # Adjust password as needed
        obs_client.connect()
        print("Connected to OBS")
    except Exception as e:
        print(f"Failed to connect to OBS: {e}")

def start_recording():
    if obs_client:
        try:
            obs_client.call(requests.StartRecording())
            print("Recording started")
        except Exception as e:
            print(f"Failed to start recording: {e}")

def stop_recording():
    if obs_client:
        try:
            obs_client.call(requests.StopRecording())
            print("Recording stopped")
        except Exception as e:
            print(f"Failed to stop recording: {e}")

def execute_macro(key):
    try:
        pyautogui.press(key)
        print(f"Pressed {key}")
    except Exception as e:
        print(f"Failed to press {key}: {e}")

def update_status(status, step, progress_val):
    global system_status, workflow_step, progress
    with status_lock:
        system_status = status
        workflow_step = step
        progress = progress_val

def automated_workflow():
    global is_workflow_running
    if is_workflow_running:
        return {"success": False, "message": "Workflow already running"}

    is_workflow_running = True
    update_status("running", "Starting workflow...", 0)

    try:
        # Step 1: Press F6 scene
        update_status("running", "Switching to F6 scene", 10)
        execute_macro('f6')
        time.sleep(3)  # Wait 3 seconds

        # Step 2: Press F7 scene and start recording
        update_status("running", "Switching to F7 scene and starting recording", 30)
        execute_macro('f7')
        start_recording()
        time.sleep(10)  # Wait 10 seconds

        # Step 3: Stop recording and press F8 scene
        update_status("running", "Stopping recording and switching to F8 scene", 80)
        stop_recording()
        execute_macro('f8')

        # Step 4: Ready for next user
        update_status("ready", "Ready for next session", 100)
        is_workflow_running = False

        return {"success": True, "message": "Workflow completed successfully"}

    except Exception as e:
        update_status("error", f"Error: {str(e)}", 0)
        is_workflow_running = False
        return {"success": False, "message": str(e)}

# Flask apps
main_app = Flask(__name__)
config_app = Flask(__name__)
big_screen_app = Flask(__name__)
download_app = Flask(__name__)
tablet_app = Flask(__name__)

# Main app routes
@main_app.route('/')
def main_page():
    with status_lock:
        return render_template('index.html',
                             status=system_status,
                             progress=progress,
                             workflow_step=workflow_step)

@main_app.route('/start_workflow', methods=['POST'])
def start_workflow():
    result = automated_workflow()
    return jsonify(result)

@main_app.route('/get_status')
def get_status():
    with status_lock:
        return jsonify({
            "status": system_status,
            "progress": progress,
            "workflow_step": workflow_step
        })

@main_app.route('/start', methods=['POST'])
def start_system():
    # Start file monitoring
    observer = Observer()
    observer.schedule(VideoHandler(), VIDEO_FOLDER, recursive=False)
    observer.start()

    # Start OBS connection
    start_obs_connection()

    return jsonify({"message": "System started successfully"})

# Config app routes
@config_app.route('/')
def config_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Configuration</title></head>
    <body>
        <h1>System Configuration</h1>
        <form id="configForm">
            <label>Video Folder: <input type="text" id="videoFolder" value="{{VIDEO_FOLDER}}"></label><br>
            <label>Old Video Folder: <input type="text" id="oldVideoFolder" value="{{OLD_VIDEO_FOLDER}}"></label><br>
            <button type="submit">Save Config</button>
        </form>
        <script>
            document.getElementById('configForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const config = {
                    videoFolder: document.getElementById('videoFolder').value,
                    oldVideoFolder: document.getElementById('oldVideoFolder').value
                };
                fetch('/save_config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                })
                .then(response => response.json())
                .then(data => alert(data.message));
            });
        </script>
    </body>
    </html>
    ''')

@config_app.route('/save_config', methods=['POST'])
def save_config():
    data = request.json
    # In a real app, you'd save this to a config file
    return jsonify({"message": "Configuration saved"})

# Big screen app routes
@big_screen_app.route('/')
def big_screen_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Big Screen Control</title></head>
    <body>
        <h1>Macro Controls</h1>
        <button onclick="sendMacro('f6')">F6</button>
        <button onclick="sendMacro('f7')">F7</button>
        <button onclick="sendMacro('f8')">F8</button>
        <button onclick="sendMacro('f9')">F9</button>
        <script>
            function sendMacro(key) {
                fetch('/macro/' + key, {method: 'POST'})
                .then(response => response.json())
                .then(data => alert(data.message));
            }
        </script>
    </body>
    </html>
    ''')

@big_screen_app.route('/macro/<key>', methods=['POST'])
def execute_macro_route(key):
    execute_macro(key)
    return jsonify({"message": f"Executed {key} macro"})

# Download app routes
@download_app.route('/')
def download_page():
    global current_video

    def get_video_info(filepath):
        if not filepath or not os.path.exists(filepath):
            return None
        stat = os.stat(filepath)
        return {
            'filename': os.path.basename(filepath),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

    current_video_info = get_video_info(current_video) if current_video else None

    old_videos = []
    if os.path.exists(OLD_VIDEO_FOLDER):
        for file in os.listdir(OLD_VIDEO_FOLDER):
            if file.endswith(('.mp4', '.avi', '.mkv')):
                filepath = os.path.join(OLD_VIDEO_FOLDER, file)
                info = get_video_info(filepath)
                if info:
                    old_videos.append(info)

    return render_template('download.html',
                         current_video=current_video_info,
                         old_videos=old_videos)

@download_app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(VIDEO_FOLDER, filename, as_attachment=True)

@download_app.route('/download/old/<filename>')
def download_old_file(filename):
    return send_from_directory(OLD_VIDEO_FOLDER, filename, as_attachment=True)

# Tablet app routes
@tablet_app.route('/')
def tablet_page():
    return render_template('tablet.html')

@tablet_app.route('/start_recording', methods=['POST'])
def start_recording_route():
    start_recording()
    return jsonify({"success": True, "message": "Recording started"})

@tablet_app.route('/stop_recording', methods=['POST'])
def stop_recording_route():
    stop_recording()
    return jsonify({"success": True, "message": "Recording stopped"})

def run_server(app, port):
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Start all servers in separate threads
    servers = [
        (main_app, MAIN_PORT),
        (config_app, CONFIG_PORT),
        (big_screen_app, BIG_SCREEN_PORT),
        (download_app, DOWNLOAD_PORT),
        (tablet_app, TABLET_PORT)
    ]
    
    threads = []
    for app, port in servers:
        thread = threading.Thread(target=run_server, args=(app, port))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    print("All servers started. Press Ctrl+C to stop.")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
