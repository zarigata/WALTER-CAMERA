# Camera Booth System

This is a camera booth system using OBS for recording and a web interface for control.

## Features

- OBS scene management: after, standby, recording
- Web control pages: Admin, Tablet Control, Download
- Video management: latest and old videos
- Petrobras-themed UI

## Setup

1. Follow OBS_SETUP.md for OBS configuration.

2. For backend:
   - python -m venv venv
   - .\venv\Scripts\Activate.ps1
   - pip install -r requirements.txt
   - python app.py

3. Or use Docker: docker-compose up

4. Access at http://localhost:8000/tablet for tablet control, /admin for admin panel, /download for download page.
