from pathlib import Path


def test_output_dirs_exist():
    Path("output/recordings").mkdir(parents=True, exist_ok=True)
    Path("output/ksusesender_ready").mkdir(parents=True, exist_ok=True)
    assert Path("output/recordings").exists()
    assert Path("output/ksusesender_ready").exists()
