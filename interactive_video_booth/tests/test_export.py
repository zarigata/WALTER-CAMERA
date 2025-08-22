import os

def test_outputs_dir_exists():
    out_dir = os.path.abspath('interactive_video_booth/outputs')
    assert os.path.isdir(out_dir)
