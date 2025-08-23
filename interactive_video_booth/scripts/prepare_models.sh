#!/usr/bin/env bash
set -euo pipefail

# Prepare models online (one-time) so future runs are fully offline.
# Ensure your virtual environment is activated, or python resolves to the correct interpreter.

python -m interactive_video_booth.main --prepare-models

echo "Models prepared successfully."
