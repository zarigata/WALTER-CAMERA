from pathlib import Path
from interactive_video_booth.utils.env_check import run_stage0


def test_stage0_ok():
    base = Path(__file__).resolve().parents[1]
    code = run_stage0(base)
    assert code == 0
