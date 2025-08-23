import pytest
from pathlib import Path

from interactive_video_booth.inference.stage2 import run_stage2
from interactive_video_booth.utils.errors import StageError


def test_stage2_single_frame_inference():
    base = Path(__file__).resolve().parents[1]
    cfg = base / "configs" / "last_camera.json"
    if not cfg.exists():
        pytest.skip("Stage 1 not completed or camera not configured; skipping Stage 2 smoke test.")

    try:
        code = run_stage2(base, prefer_gpu=False)
        assert code == 0
    except StageError as se:
        # Allow skip if model not available offline or camera failure
        msg = str(se)
        if se.code == 20 or (
            se.code == 21 and (
                "No camera chosen" in msg
                or "Failed to open camera" in msg
                or "Failed to capture a frame" in msg
            )
        ):
            pytest.skip(f"Stage 2 prerequisites not met: {msg}")
        raise
