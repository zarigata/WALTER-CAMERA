import os
import yaml
from dataclasses import dataclass

@dataclass
class AppConfig:
    watched_folder: str
    output_width: int
    output_height: int
    fps: int
    record_duration_s: int
    gpu: bool

@dataclass
class CameraConfig:
    primary_camera_id: str | int | None
    secondary_camera_id: str | int | None

@dataclass
class FusionConfig:
    seg_weight: float
    motion_weight: float
    on_threshold: float
    off_threshold: float
    persistence_frames: int

@dataclass
class RenderConfig:
    fullscreen: bool
    window_name: str
    effect: str

@dataclass
class Config:
    app: AppConfig
    cameras: CameraConfig
    fusion: FusionConfig
    render: RenderConfig


def load_config(path: str) -> Config:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    app = data.get('app', {})
    cameras = data.get('cameras', {})
    fusion = data.get('fusion', {})
    render = data.get('render', {})

    watched = os.path.abspath(app.get('watched_folder', 'interactive_video_booth/outputs'))
    os.makedirs(watched, exist_ok=True)

    return Config(
        app=AppConfig(
            watched_folder=watched,
            output_width=int(app.get('output_width', 1920)),
            output_height=int(app.get('output_height', 1080)),
            fps=int(app.get('fps', 30)),
            record_duration_s=int(app.get('record_duration_s', 10)),
            gpu=bool(app.get('gpu', False)),
        ),
        cameras=CameraConfig(
            primary_camera_id=cameras.get('primary_camera_id', 0),
            secondary_camera_id=cameras.get('secondary_camera_id', None),
        ),
        fusion=FusionConfig(
            seg_weight=float(fusion.get('seg_weight', 0.6)),
            motion_weight=float(fusion.get('motion_weight', 0.4)),
            on_threshold=float(fusion.get('on_threshold', 0.4)),
            off_threshold=float(fusion.get('off_threshold', 0.2)),
            persistence_frames=int(fusion.get('persistence_frames', 10)),
        ),
        render=RenderConfig(
            fullscreen=bool(render.get('fullscreen', True)),
            window_name=str(render.get('window_name', 'Silhouette Booth')),
            effect=str(render.get('effect', 'glow')),
        ),
    )
