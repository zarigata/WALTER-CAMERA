from __future__ import annotations
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np  # type: ignore
import cv2  # type: ignore

from .providers import select_onnx_providers
from ..capture.camera_discovery import _parse_source
from ..utils.logger import get_logger, write_error_log
from ..utils.errors import StageError
from ..utils.assets import prepare_models


## Note: Stage 2 operates strictly offline; models must be pre-downloaded via --prepare-models.


@dataclass
class Detection:
    xyxy: Tuple[float, float, float, float]
    conf: float
    cls: int


# ---------------------- IO helpers ----------------------
## Download helpers removed; use utils.assets.prepare_models() before running offline.


# ---------------------- Session & inference ----------------------

def _load_session(model_path: Path, prefer_gpu: bool) -> tuple[Any, str]:
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as e:
        raise StageError(21, f"onnxruntime not available: {e}")

    providers, label = select_onnx_providers(prefer_gpu=prefer_gpu)
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.intra_op_num_threads = max(1, _cpu_count_physical_fallback())
    try:
        sess = ort.InferenceSession(str(model_path), sess_options=so, providers=providers)
    except Exception as e:
        raise StageError(21, f"Failed to load ONNX model: {e}")
    return sess, label


def _infer_with_opencv_dnn(model_path: Path, inp: np.ndarray) -> List[np.ndarray]:
    # inp expected shape (1,3,H,W), float32 [0,1]
    try:
        net = cv2.dnn.readNetFromONNX(str(model_path))
        net.setInput(inp)
        out = net.forward()
        return [out]
    except Exception as e:
        raise StageError(21, f"OpenCV DNN inference failed: {e}")


def _cpu_count_physical_fallback() -> int:
    try:
        import psutil  # type: ignore

        return psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
    except Exception:
        import os

        return os.cpu_count() or 1


@dataclass
class ModelConfig:
    input_size: int = 320
    use_pose: bool = False


def _load_model_config(cfg_dir: Path) -> ModelConfig:
    cfg_path = cfg_dir / "model_config.json"
    if not cfg_path.exists():
        # default config
        return ModelConfig()
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        return ModelConfig(
            input_size=int(data.get("input_size", 320)),
            use_pose=bool(data.get("use_pose", False)),
        )
    except Exception:
        return ModelConfig()


# ---------------------- Pre/Post ----------------------

def _letterbox_resize(image: np.ndarray, new_size: int) -> tuple[np.ndarray, float, Tuple[int, int]]:
    h, w = image.shape[:2]
    scale = min(new_size / h, new_size / w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((new_size, new_size, 3), 114, dtype=np.uint8)
    top = (new_size - nh) // 2
    left = (new_size - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return canvas, scale, (left, top)


def _nms(dets: np.ndarray, iou_thresh: float = 0.45) -> List[int]:
    if dets.size == 0:
        return []
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep: List[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_thresh)[0]
        order = order[inds + 1]
    return keep


def _parse_yolov8_onnx_output(outputs: List[np.ndarray], conf_thres: float, img_size: int, scale: float, pad: Tuple[int, int]) -> List[Detection]:
    # Try to find the tensor with predictions in either shape (N, 84/85) or (84/85, N)
    arr = None
    for out in outputs:
        a = np.squeeze(out)
        if a.ndim == 3:
            # e.g., (1, N, 84/85)
            a = a[0]
        if a.ndim == 2:
            if a.shape[-1] >= 84:
                # (N, 84/85)
                arr = a
                break
            if a.shape[0] >= 84:
                # (84/85, N) -> transpose
                arr = a.T
                break
    if arr is None:
        return []

    num_cols = arr.shape[1]
    # Heuristic: if 85 cols => [x,y,w,h,obj,80 classes]; if 84 => [x,y,w,h,80 classes]
    if num_cols >= 85:
        boxes = arr[:, :4]
        obj = arr[:, 4:5]
        cls_probs = arr[:, 5:]
        cls_ids = cls_probs.argmax(axis=1)
        cls_scores = cls_probs.max(axis=1)
        scores = (obj.reshape(-1) * cls_scores.reshape(-1))
    else:
        boxes = arr[:, :4]
        cls_probs = arr[:, 4:]
        cls_ids = cls_probs.argmax(axis=1)
        scores = cls_probs.max(axis=1)

    # Convert boxes (cx,cy,w,h) -> (x1,y1,x2,y2)
    cx, cy, bw, bh = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = cx - bw / 2
    y1 = cy - bh / 2
    x2 = cx + bw / 2
    y2 = cy + bh / 2

    # Undo letterbox scaling
    left, top = pad
    x1 = (x1 - left) / scale
    y1 = (y1 - top) / scale
    x2 = (x2 - left) / scale
    y2 = (y2 - top) / scale

    dets = np.stack([x1, y1, x2, y2, scores, cls_ids], axis=1)
    # Filter conf
    dets = dets[dets[:, 4] >= conf_thres]
    if dets.size == 0:
        return []
    # NMS
    keep = _nms(dets[:, :5], 0.45)
    dets = dets[keep]

    out: List[Detection] = []
    for x1, y1, x2, y2, sc, cid in dets:
        out.append(Detection((float(x1), float(y1), float(x2), float(y2)), float(sc), int(cid)))
    return out


# ---------------------- Effects stubs ----------------------

def _load_effects() -> List[str]:
    # For Stage 2 we only instantiate stubs; real params will come in Stage 4
    try:
        from ..effects.aura import AuraEffect  # noqa: F401
        from ..effects.trail import TrailEffect  # noqa: F401
        return ["aura", "trail"]
    except Exception:
        return ["aura", "trail"]


# ---------------------- Stage 2 orchestrator ----------------------

def run_stage2(base_dir: Path, prefer_gpu: bool, conf_thres: float = 0.3, force: bool = False) -> int:
    stage_label = "STAGE 2"
    log = get_logger(stage_label, base_dir)

    models_dir = base_dir / "models"
    outputs_dir = base_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    cfg_dir = base_dir / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    # Load config and choose model
    mcfg = _load_model_config(cfg_dir)
    target_size = int(mcfg.input_size or 320)

    # Require pre-downloaded model files (offline). Use manifest via assets.prepare_models
    model_path: Path | None = None
    try:
        assets = prepare_models(base_dir, allow_download=False)
        # Default model id
        model_path = assets.get("yolov8n")
    except StageError as se:
        write_error_log(stage_label, base_dir, "stage2_error.log", se.message)
        if not force:
            raise

    # Load session (if model available)
    t0 = time.time()
    sess = None
    backend_label = "none"
    if model_path is not None:
        try:
            sess, backend_label = _load_session(model_path, prefer_gpu=prefer_gpu)
        except StageError as se:
            # Keep sess=None and proceed to OpenCV DNN fallback below
            write_error_log(stage_label, base_dir, "stage2_error.log", se.message)
    t1 = time.time()

    # Capture one frame from chosen camera
    last_cam = cfg_dir / "last_camera.json"
    frame: np.ndarray | None = None
    opened_source: str | None = None
    if last_cam.exists():
        try:
            cam_info = json.loads(last_cam.read_text(encoding="utf-8"))
            src = cam_info.get("source", 0)
            disp, ocv_src = _parse_source(src)
            cap = cv2.VideoCapture(ocv_src)
            if cap is not None and cap.isOpened():
                # Try a few attempts to get a valid frame
                for _ in range(5):
                    ret, f = cap.read()
                    if ret and f is not None and f.size > 0:
                        frame = f
                        opened_source = str(disp)
                        break
                    time.sleep(0.05)
                cap.release()
        except Exception as e:
            write_error_log(stage_label, base_dir, "stage2_error.log", f"Error opening last camera: {e}")

    # If still no frame, try default indices if forced, else error
    if frame is None:
        if force:
            for probe in [0, 1, 2, "usb:0"]:
                try:
                    disp, ocv_src = _parse_source(probe)
                    cap = cv2.VideoCapture(ocv_src)
                    if cap is not None and cap.isOpened():
                        for _ in range(5):
                            ret, f = cap.read()
                            if ret and f is not None and f.size > 0:
                                frame = f
                                opened_source = str(disp)
                                break
                            time.sleep(0.05)
                        cap.release()
                        if frame is not None:
                            break
                except Exception:
                    continue
        if frame is None and not force:
            msg = "Failed to capture a frame for inference (no camera)."
            write_error_log(stage_label, base_dir, "stage2_error.log", msg)
            raise StageError(21, msg)

    # As a last resort under --force, create a dummy frame
    if frame is None and force:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, "NO CAMERA - DUMMY FRAME", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2, cv2.LINE_AA)
        opened_source = "dummy"

    # Preprocess
    tp0 = time.time()
    img = frame[:, :, ::-1]  # BGR->RGB
    lb, scale, pad = _letterbox_resize(img, target_size)
    inp = lb.astype(np.float32) / 255.0
    inp = np.transpose(inp, (2, 0, 1))  # CHW
    inp = np.expand_dims(inp, 0)
    tp1 = time.time()

    # Inference
    ti0 = time.time()
    ran_inference = False
    raw_outputs: List[np.ndarray] = []
    if sess is not None:
        try:
            inputs = {sess.get_inputs()[0].name: inp}
            raw_outputs = sess.run(None, inputs)
            ran_inference = True
        except Exception as e:
            write_error_log(stage_label, base_dir, "stage2_error.log", f"Inference error: {e}")
            # Try OpenCV DNN fallback if model exists
            if model_path is not None:
                try:
                    raw_outputs = _infer_with_opencv_dnn(model_path, inp)
                    ran_inference = True
                    backend_label = "opencv-dnn"
                except Exception as e2:
                    write_error_log(stage_label, base_dir, "stage2_error.log", f"OpenCV DNN fallback failed: {e2}")
                    if not force:
                        raise StageError(21, f"Inference error: {e}; OpenCV DNN fallback failed: {e2}")
            elif not force:
                raise StageError(21, f"Inference error: {e}")
    elif model_path is not None:
        # No ORT session (e.g., ORT missing). Try OpenCV DNN
        try:
            raw_outputs = _infer_with_opencv_dnn(model_path, inp)
            ran_inference = True
            backend_label = "opencv-dnn"
        except Exception as e:
            write_error_log(stage_label, base_dir, "stage2_error.log", f"OpenCV DNN fallback failed: {e}")
            if not force:
                raise StageError(21, f"OpenCV DNN fallback failed: {e}")
    ti1 = time.time()

    # Parse
    dets: List[Detection] = []
    if ran_inference:
        dets = _parse_yolov8_onnx_output(raw_outputs, conf_thres=conf_thres, img_size=target_size, scale=scale, pad=pad)
    tp2 = time.time()

    # Draw overlay on original BGR frame
    overlay = frame.copy()
    for d in dets:
        x1, y1, x2, y2 = map(int, d.xyxy)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{d.cls}:{d.conf:.2f}"
        cv2.putText(overlay, label, (x1, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    # Save outputs
    debug_img_path = outputs_dir / "stage2_inference_debug.jpg"
    cv2.imwrite(str(debug_img_path), overlay)

    infer_ms = int((ti1 - ti0) * 1000)
    total_ms = int((t1 - t0) * 1000 + (tp1 - tp0) * 1000 + infer_ms + (tp2 - ti1) * 1000)

    status = "ok" if ran_inference else ("no_inference" if model_path is None else "inference_failed")
    if frame is not None and opened_source is None:
        opened_source = "unknown"
    stage2_json = {
        "status": status,
        "fallback": None if ran_inference else {
            "reason": (
                "model/session unavailable" if model_path is None or sess is None else "runtime_error"
            ),
            "force": force,
        },
        "camera_source": opened_source,
        "model": str(model_path.name) if model_path is not None else None,
        "backend": backend_label,
        "input_size": target_size,
        "detections": len(dets),
        "timing_ms": {
            "load_model": int((t1 - t0) * 1000),
            "preprocess": int((tp1 - tp0) * 1000),
            "inference": infer_ms if ran_inference else None,
            "postprocess": int((tp2 - ti1) * 1000) if ran_inference else None,
            "total_est": total_ms,
        },
    }
    (outputs_dir / "stage2_debug.json").write_text(json.dumps(stage2_json, indent=2), encoding="utf-8")

    # Effects load
    effects = _load_effects()

    if model_path is not None and (sess is not None or backend_label == "opencv-dnn"):
        try:
            log.info(f"Model load OK: {model_path.name} ({backend_label})")
        except Exception:
            log.info(f"Model load OK: ({backend_label})")
    else:
        log.info("Model not loaded (running diagnostics only or forced run without inference)")
    log.info(f"Inference {'OK' if ran_inference else 'skipped'}: found {len(dets)} detections")
    log.info(f"Effects loaded: {', '.join(effects)}")

    if infer_ms > 1000:
        log.info(f"WARNING: slow inference: {infer_ms} ms. Consider smaller input_size (e.g., 320) or a lighter model.")

    return 0
