import pytest
from pathlib import Path
from interactive_video_booth.capture.camera_discovery import discover_and_validate_camera
from interactive_video_booth.utils.errors import StageError


def test_stage1_camera_discovery():
    base = Path(__file__).resolve().parents[1]
    try:
        report = discover_and_validate_camera(base, device=None, force=False)
        assert report.source is not None
        assert isinstance(report.resolution, tuple)
    except StageError as e:
        # If no camera, assert proper error code 10
        assert e.code == 10
        pytest.skip("No camera available on test machine")
