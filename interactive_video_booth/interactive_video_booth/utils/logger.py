import logging
from logging import Logger
from datetime import datetime
from pathlib import Path


def _ensure_logs_dir(base_dir: Path) -> Path:
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_logger(stage_label: str, base_dir: Path) -> Logger:
    """Create a timestamped console+file logger with stage prefix.

    Args:
        stage_label: e.g., "STAGE 0"
        base_dir: project base directory
    """
    logs_dir = _ensure_logs_dir(base_dir)
    logger = logging.getLogger(f"ivb.{stage_label}")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    ts_fmt = "%Y-%m-%d %H:%M:%S"

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(f"[%(asctime)s] [{stage_label}] %(message)s", datefmt=ts_fmt))

    logfile = logs_dir / f"{stage_label.lower().replace(' ', '_')}.log"
    fileh = logging.FileHandler(logfile, encoding="utf-8")
    fileh.setLevel(logging.INFO)
    fileh.setFormatter(logging.Formatter(f"[%(asctime)s] [{stage_label}] %(levelname)s: %(message)s", datefmt=ts_fmt))

    logger.addHandler(console)
    logger.addHandler(fileh)
    return logger


def write_error_log(stage_label: str, base_dir: Path, filename: str, message: str) -> None:
    logs_dir = _ensure_logs_dir(base_dir)
    path = logs_dir / filename
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] [{stage_label}] ERROR: {message}\n")
