from __future__ import annotations
import argparse
import sys
from pathlib import Path

from .utils.errors import StageError
from .utils.env_check import run_stage0
from .capture.camera_discovery import discover_and_validate_camera
from .utils.logger import get_logger
from .inference.providers import select_onnx_providers
import json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Interactive Video Booth staged runner")
    p.add_argument("--stage", type=int, default=None, help="Run a single stage (0 or 1 currently implemented)")
    p.add_argument("--force", action="store_true", help="Force continue on flaky camera in Stage 1")
    p.add_argument("--device", type=str, default=None, help="Explicit camera source (e.g., 0, 1, rtsp://..., /dev/video0)")
    p.add_argument(
        "--inference",
        type=str,
        choices=["auto", "cpu", "gpu"],
        default="auto",
        help="Select inference mode for later stages (auto chooses GPU if available)",
    )
    p.add_argument("--auto", action="store_true", help="Run stages sequentially from 0 upward (stops on failure)")
    return p.parse_args()


def run_stage1(base_dir: Path, force: bool = False, device: str | None = None) -> int:
    stage_label = "STAGE 1"
    log = get_logger(stage_label, base_dir)
    report = discover_and_validate_camera(base_dir=base_dir, device=device, force=force)
    res_w, res_h = report.resolution
    print(
        f"[STAGE 1] Camera found: index={report.source} resolution={res_w}x{res_h} "
        f"fps={report.fps_est} frames_ok_pct={report.frames_ok_pct}"
    )
    return 0


def determine_and_persist_backend(base_dir: Path, mode: str) -> None:
    prefer_gpu = mode in ("auto", "gpu")
    providers, label = select_onnx_providers(prefer_gpu=prefer_gpu)
    cfg_dir = base_dir / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "requested_mode": mode,
        "selected_label": label,
        "onnxruntime_providers": providers,
    }
    with (cfg_dir / "runtime_backend.json").open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[INFO] Inference backend selected: {label} providers={providers}")


def main() -> int:
    args = parse_args()
    base_dir = Path(__file__).resolve().parents[1]

    try:
        if args.auto:
            # Stage 0
            print("[STAGE 0] Running...")
            run_stage0(base_dir)
            determine_and_persist_backend(base_dir, args.inference)
            # Stage 1
            print("[STAGE 1] Running...")
            run_stage1(base_dir, force=args.force, device=args.device)
            print("Auto run complete. Further stages TBD.")
            return 0

        if args.stage is None:
            print("No --stage provided. Use --auto to run sequentially or --stage N.")
            return 0

        if args.stage == 0:
            code = run_stage0(base_dir)
            determine_and_persist_backend(base_dir, args.inference)
            return code
        elif args.stage == 1:
            return run_stage1(base_dir, force=args.force, device=args.device)
        else:
            print("Only Stage 0 and 1 are implemented in this prototype.")
            return 0
    except StageError as se:
        # Ensure exit code
        return se.code


if __name__ == "__main__":
    sys.exit(main())
