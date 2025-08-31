"""
Walter Camera - Multi-purpose Python Application
Handles web servers, file monitoring, macros, and OBS integration
"""

import os
import threading
import time
from flask import Flask, render_template_string, send_from_directory, request, jsonify
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

# Flask apps
main_app = Flask(__name__)
config_app = Flask(__name__)
big_screen_app = Flask(__name__)
download_app = Flask(__name__)
tablet_app = Flask(__name__)

# Main app routes
@main_app.route('/')
def main_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Walter Camera - Main</title></head>
    <body>
        <h1>Walter Camera Control</h1>
        <button onclick="startSystem()">Start System</button>
        <script>
            function startSystem() {
                fetch('/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => alert(data.message));
            }
        </script>
    </body>
    </html>
    ''')

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
    if current_video:
        filename = os.path.basename(current_video)
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head><title>Download Video</title></head>
        <body>
            <h1>Download Current Video</h1>
            <p>Current video: {filename}</p>
            <a href="/download/{filename}" download>Download Video</a>
        </body>
        </html>
        ''')
    else:
        return "<h1>No video available</h1>"

@download_app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(VIDEO_FOLDER, filename, as_attachment=True)

# Tablet app routes
@tablet_app.route('/')
def tablet_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Tablet Control</title></head>
    <body>
        <h1>Recording Control</h1>
        <button onclick="startRecording()">Start Recording</button>
        <button onclick="stopRecording()">Stop Recording</button>
        <script>
            function startRecording() {
                fetch('/start_recording', {method: 'POST'})
                .then(response => response.json())
                .then(data => alert(data.message));
            }
            function stopRecording() {
                fetch('/stop_recording', {method: 'POST'})
                .then(response => response.json())
                .then(data => alert(data.message));
            }
        </script>
    </body>
    </html>
    ''')

@tablet_app.route('/start_recording', methods=['POST'])
def start_recording_route():
    start_recording()
    return jsonify({"message": "Recording started"})

@tablet_app.route('/stop_recording', methods=['POST'])
def stop_recording_route():
    stop_recording()
    return jsonify({"message": "Recording stopped"})

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
