# Petrobras Camera Booth Control System (Windows)

This project is a web-based control system for a camera booth that uses OBS Studio to manage scenes and recordings. It is designed to run directly on a Windows machine.

## Features

- **Web-Based Control**: Control OBS scenes and recordings from a browser.
- **Simple Workflow**: A one-touch button on a tablet starts the entire recording sequence.
- **Automated File Management**: New videos are saved to a "latest" folder, and old ones are archived.
- **Petrobras-Themed UI**: Clean, professional interface following Petrobras branding guidelines.
- **Admin Panel**: Configure OBS connection, recording duration, and delays.
- **Windows Scripts**: Simple `install.bat` and `run.bat` for easy setup and execution.

---

## Prerequisites

- **Windows Operating System**
- **Python 3.11+**: [Download here](https://www.python.org/downloads/). Make sure to check **"Add Python to PATH"** during installation.
- **OBS Studio**: [Download here](https://obsproject.com/).
- **OBS WebSocket Plugin**: [Download here](https://github.com/obsproject/obs-websocket/releases). Version 5.x is required.

---

## 1. OBS Setup

1.  **Install OBS WebSocket Plugin**: Follow the installation instructions for the plugin.
2.  **Enable WebSocket Server**:
    - In OBS, go to `Tools` -> `WebSocket Server Settings`.
    - Check `Enable WebSocket Server`.
    - Note the `Server Port` (default is `4455`).
    - Set a `Server Password` for security.
3.  **Create OBS Scenes**:
    You must create three scenes in OBS with the exact following names:
    - `after` (This should be your default/idle scene)
    - `standby` (A scene to prepare the user, e.g., a countdown)
    - `recording` (The scene that will be active during recording)
4.  **Set Recording Path**:
    - In OBS, go to `File` -> `Settings` -> `Output`.
    - Under the `Recording` tab, set the `Recording Path`. This is the temporary folder where OBS will save new videos.
    - **Important**: You must copy this exact path and set it as the `RECORDING_PATH` value in your `.env` file. The application will automatically move the latest video from this folder into the project's `videos/latest` directory.

---

## 2. System Configuration

1.  **Create `.env` file**:
    In the project folder, make a copy of `.env.example` and rename it to `.env`.

2.  **Edit `.env` file**:
    Open the `.env` file with a text editor and fill in the values based on your OBS setup.

    ```ini
    # OBS WebSocket Settings
    OBS_HOST=localhost
    OBS_PORT=4455
    OBS_PASSWORD=your_obs_websocket_password

    # Video File Management
    # This MUST match the Recording Path configured in your OBS settings.
    # The application watches this folder for new videos.
    # Example: C:\Users\YourUser\Videos\OBS
    RECORDING_PATH=C:\Path\To\Your\OBS\Recordings

    # Delays and Durations (in seconds)
    STANDBY_DELAY=3
    RECORDING_DURATION=10
    ```

---

## 3. Running the Application

1.  **Install Dependencies**:
    Double-click the `install.bat` file. This will create a Python virtual environment and install all necessary libraries. Wait for it to complete.

2.  **Run the Server**:
    Double-click the `run.bat` file. This will start the web server.

3.  **Access the Application**:
    With the server running, open a web browser on the same machine or on a device on the same network (like a tablet).
    - **Tablet Control**: `http://localhost:8000/tablet`
    - **Download Page**: `http://localhost:8000/download`
    - **Admin Panel**: `http://localhost:8000/admin`

---

## Project Structure

```
/
├── app/                # FastAPI Backend
├── frontend/           # Frontend HTML, CSS, JS
├── videos/             # Stores recorded videos
├── .env.example        # Example environment variables
├── install.bat         # Installation script for Windows
├── run.bat             # Execution script for Windows
└── requirements.txt    # Python dependencies
```
