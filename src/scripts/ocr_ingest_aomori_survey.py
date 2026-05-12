#!/usr/bin/env python3
"""Ingest scanned Aomori paper survey JPEGs into reviewable CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from PIL import Image, ImageOps

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover - dependency check path
    cv2 = None
    np = None

try:
    import pytesseract
    from pytesseract import Output
except Exception:  # pragma: no cover - dependency check path
    pytesseract = None
    Output = None


EXPECTED_COLUMNS = [
    "response_id",
    "q1_age_group",
    "q2_housing_type",
    "q3_building_age_band",
    "q4_tenure",
    "q5_winter_home_bath_freq",
    "q6_window_insulation",
    "q7_bath_heater_status",
    "q8_reason_codes",
    "q8_other_text",
    "q9_central_heating_use",
    "q10_alt_heating_types",
    "q10_other_text",
    "q11_dressingroom_cold_7pt",
    "q11_bathroom_cold_7pt",
]

ANALYSIS_DERIVED_COLUMNS = [
    "q7_bath_heater_status_analysis",
    "q7_q8_inconsistency_flag",
    "q7_analysis_note",
    "manual_review_notes",
]

NUMERIC_COLUMNS = [
    "q1_age_group",
    "q2_housing_type",
    "q3_building_age_band",
    "q4_tenure",
    "q5_winter_home_bath_freq",
    "q6_window_insulation",
    "q7_bath_heater_status",
    "q9_central_heating_use",
    "q11_dressingroom_cold_7pt",
    "q11_bathroom_cold_7pt",
]

PAGE_TYPES = ["page_q1_q5", "page_q6_q9", "page_q10_q11"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
TEXT_CONFIDENCE_THRESHOLD = 70.0
CHECK_SELECTED_THRESHOLD = 0.08
CHECK_AMBIGUOUS_THRESHOLD = 0.03
WIDE_CHECKBOX_FRAME_FIELDS = {
    "q1_age_group",
    "q2_housing_type",
    "q4_tenure",
    "q5_winter_home_bath_freq",
    "q6_window_insulation",
    "q11_dressingroom_cold_7pt",
    "q11_bathroom_cold_7pt",
}
TESSERACT_STANDARD_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]
TESSDATA_STANDARD_DIRS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tessdata",
    Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata"),
]


@dataclass(frozen=True)
class OptionSpec:
    code: int
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    page_type: str
    kind: str
    options: tuple[OptionSpec, ...] = ()
    bbox: tuple[float, float, float, float] | None = None
    relevant_if_field: str | None = None
    relevant_if_code: int | None = None


def opt(code: int, bbox: tuple[float, float, float, float]) -> OptionSpec:
    return OptionSpec(code=code, bbox=bbox)


# Normalized bboxes are intentionally conservative and can be tuned after the
# first real scan test. They target the printed checkbox area, not full labels.
DEFAULT_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        "q1_age_group",
        "page_q1_q5",
        "single",
        (
            opt(1, (0.072, 0.191, 0.090, 0.207)),
            opt(2, (0.528, 0.191, 0.546, 0.207)),
            opt(3, (0.072, 0.222, 0.090, 0.238)),
            opt(4, (0.528, 0.222, 0.546, 0.238)),
            opt(5, (0.072, 0.253, 0.090, 0.269)),
            opt(6, (0.528, 0.253, 0.546, 0.269)),
            opt(7, (0.072, 0.284, 0.090, 0.300)),
            opt(8, (0.528, 0.284, 0.546, 0.300)),
        ),
    ),
    FieldSpec(
        "q2_housing_type",
        "page_q1_q5",
        "single",
        (
            opt(1, (0.072, 0.365, 0.090, 0.381)),
            opt(2, (0.072, 0.405, 0.090, 0.421)),
        ),
    ),
    FieldSpec(
        "q3_building_age_band",
        "page_q1_q5",
        "single",
        (
            opt(1, (0.072, 0.498, 0.090, 0.514)),
            opt(2, (0.528, 0.498, 0.546, 0.514)),
            opt(3, (0.072, 0.529, 0.090, 0.545)),
            opt(4, (0.528, 0.529, 0.546, 0.545)),
            opt(5, (0.072, 0.560, 0.090, 0.576)),
        ),
    ),
    FieldSpec(
        "q4_tenure",
        "page_q1_q5",
        "single",
        (
            opt(1, (0.072, 0.643, 0.090, 0.659)),
            opt(2, (0.072, 0.683, 0.090, 0.699)),
        ),
    ),
    FieldSpec(
        "q5_winter_home_bath_freq",
        "page_q1_q5",
        "single",
        (
            opt(1, (0.072, 0.778, 0.090, 0.794)),
            opt(2, (0.072, 0.814, 0.090, 0.830)),
            opt(3, (0.072, 0.850, 0.090, 0.866)),
            opt(4, (0.072, 0.886, 0.090, 0.902)),
            opt(5, (0.072, 0.922, 0.090, 0.938)),
        ),
    ),
    FieldSpec(
        "q6_window_insulation",
        "page_q6_q9",
        "single",
        (
            opt(1, (0.072, 0.119, 0.090, 0.135)),
            opt(2, (0.072, 0.161, 0.090, 0.177)),
            opt(3, (0.072, 0.203, 0.090, 0.219)),
            opt(4, (0.072, 0.245, 0.090, 0.261)),
        ),
    ),
    FieldSpec(
        "q7_bath_heater_status",
        "page_q6_q9",
        "single",
        (
            opt(1, (0.072, 0.345, 0.090, 0.361)),
            opt(2, (0.072, 0.386, 0.090, 0.402)),
            opt(3, (0.072, 0.427, 0.090, 0.443)),
        ),
    ),
    FieldSpec(
        "q8_reason_codes",
        "page_q6_q9",
        "multi",
        (
            opt(1, (0.072, 0.538, 0.090, 0.554)),
            opt(2, (0.072, 0.575, 0.090, 0.591)),
            opt(3, (0.072, 0.612, 0.090, 0.628)),
            opt(4, (0.072, 0.649, 0.090, 0.665)),
            opt(5, (0.072, 0.686, 0.090, 0.702)),
            opt(6, (0.072, 0.723, 0.090, 0.739)),
            opt(7, (0.072, 0.760, 0.090, 0.776)),
            opt(8, (0.072, 0.797, 0.090, 0.813)),
        ),
    ),
    FieldSpec(
        "q8_other_text",
        "page_q6_q9",
        "text",
        bbox=(0.080, 0.848, 0.900, 0.918),
        relevant_if_field="q8_reason_codes",
        relevant_if_code=8,
    ),
    FieldSpec(
        "q9_central_heating_use",
        "page_q6_q9",
        "single",
        (
            opt(1, (0.072, 0.884, 0.090, 0.900)),
            opt(2, (0.072, 0.919, 0.090, 0.935)),
            opt(3, (0.072, 0.954, 0.090, 0.970)),
        ),
    ),
    FieldSpec(
        "q10_alt_heating_types",
        "page_q10_q11",
        "multi",
        (
            opt(1, (0.072, 0.124, 0.090, 0.140)),
            opt(2, (0.072, 0.162, 0.090, 0.178)),
            opt(3, (0.072, 0.200, 0.090, 0.216)),
            opt(4, (0.072, 0.238, 0.090, 0.254)),
            opt(5, (0.072, 0.276, 0.090, 0.292)),
        ),
    ),
    FieldSpec(
        "q10_other_text",
        "page_q10_q11",
        "text",
        bbox=(0.330, 0.228, 0.900, 0.268),
        relevant_if_field="q10_alt_heating_types",
        relevant_if_code=4,
    ),
    FieldSpec(
        "q11_dressingroom_cold_7pt",
        "page_q10_q11",
        "single",
        (
            opt(1, (0.090, 0.421, 0.108, 0.437)),
            opt(2, (0.090, 0.459, 0.108, 0.475)),
            opt(3, (0.090, 0.497, 0.108, 0.513)),
            opt(4, (0.090, 0.535, 0.108, 0.551)),
            opt(5, (0.090, 0.573, 0.108, 0.589)),
            opt(6, (0.090, 0.611, 0.108, 0.627)),
            opt(7, (0.090, 0.649, 0.108, 0.665)),
        ),
    ),
    FieldSpec(
        "q11_bathroom_cold_7pt",
        "page_q10_q11",
        "single",
        (
            opt(1, (0.090, 0.767, 0.108, 0.783)),
            opt(2, (0.090, 0.805, 0.108, 0.821)),
            opt(3, (0.090, 0.843, 0.108, 0.859)),
            opt(4, (0.090, 0.881, 0.108, 0.897)),
            opt(5, (0.090, 0.919, 0.108, 0.935)),
            opt(6, (0.090, 0.957, 0.108, 0.973)),
            opt(7, (0.090, 0.986, 0.108, 0.998)),
        ),
    ),
)

REAL_SCAN_SINGLE_FALLBACK_OPTIONS: dict[str, tuple[OptionSpec, ...]] = {
    "q6_window_insulation": (
        opt(1, (0.084, 0.086, 0.104, 0.102)),
        opt(2, (0.081, 0.115, 0.101, 0.131)),
        opt(3, (0.081, 0.145, 0.101, 0.161)),
        opt(4, (0.081, 0.177, 0.101, 0.193)),
    ),
    "q7_bath_heater_status": (
        opt(1, (0.081, 0.427, 0.101, 0.443)),
        opt(2, (0.081, 0.457, 0.101, 0.473)),
        opt(3, (0.081, 0.487, 0.101, 0.503)),
    ),
    "q9_central_heating_use": (
        opt(1, (0.081, 0.821, 0.101, 0.837)),
        opt(2, (0.081, 0.852, 0.101, 0.868)),
        opt(3, (0.081, 0.882, 0.101, 0.898)),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR ingest for Aomori Q1-Q11 paper survey scans."
    )
    parser.add_argument("--input-dir", help="Directory containing final JPEG scans")
    parser.add_argument("--output-dir", help="Run output directory")
    parser.add_argument("--tag", help="Output tag when --output-dir is omitted")
    parser.add_argument("--check-deps", action="store_true", help="Check OCR dependencies")
    parser.add_argument(
        "--write-layout-json",
        help="Write the default fixed-layout coordinates to JSON and exit",
    )
    parser.add_argument(
        "--layout-json",
        help="Read fixed-layout coordinates from JSON instead of using built-in defaults",
    )
    parser.add_argument(
        "--sequence-response-ids",
        action="store_true",
        help="Assign response_id from natural image order in 3-page sets",
    )
    parser.add_argument(
        "--sequence-page-types",
        action="store_true",
        help="Assign page_type from natural image order in 3-page sets without page OCR",
    )
    parser.add_argument(
        "--sequence-start",
        type=int,
        default=1,
        help="First numeric ID for --sequence-response-ids",
    )
    parser.add_argument(
        "--expected-responses",
        type=int,
        default=154,
        help="Expected reviewed response rows for finalization",
    )
    parser.add_argument(
        "--allow-sequence-page-fallback",
        action="store_true",
        help="Use image order modulo 3 for scanned questionnaire pages 2-4 when OCR page classification is unknown",
    )
    parser.add_argument(
        "--finalize-reviewed",
        action="store_true",
        help="Copy a reviewed CSV to the final anonymized processed CSV",
    )
    parser.add_argument("--reviewed-csv", help="Reviewed CSV to finalize")
    parser.add_argument(
        "--final-output",
        default="data/processed/aomori_survey_responses_anonymized.csv",
        help="Final anonymized CSV path for --finalize-reviewed",
    )
    return parser.parse_args()


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def output_dir_from_args(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return Path(args.output_dir)
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S_ocr_ingest")
    return Path("outputs") / "runs" / tag


def check_dependencies() -> tuple[bool, list[str]]:
    messages: list[str] = []
    ok = True
    if cv2 is None or np is None:
        ok = False
        messages.append("opencv-python is not importable.")
    else:
        messages.append(f"opencv-python import OK: {cv2.__version__}")
    if pytesseract is None:
        ok = False
        messages.append("pytesseract is not importable.")
        return ok, messages
    messages.append("pytesseract import OK.")
    configured_path = configure_tesseract_cmd()
    if configured_path:
        messages.append(f"tesseract path configured: {configured_path}")
    tessdata_dir = find_tessdata_dir()
    if tessdata_dir:
        messages.append(f"tessdata path configured: {tessdata_dir}")
    try:
        version = str(pytesseract.get_tesseract_version())
        messages.append(f"tesseract executable OK: {version}")
    except Exception as exc:
        ok = False
        messages.append(f"tesseract executable not available: {exc}")
    try:
        langs = set(list_tesseract_languages(configured_path, tessdata_dir))
        if {"jpn", "eng"}.issubset(langs):
            messages.append("tesseract languages OK: jpn, eng")
        else:
            ok = False
            messages.append(f"missing tesseract languages; installed={sorted(langs)}")
    except Exception as exc:
        ok = False
        messages.append(f"could not inspect tesseract languages: {exc}")
    return ok, messages


def list_tesseract_languages(tesseract_cmd: str, tessdata_dir: str) -> list[str]:
    cmd = [tesseract_cmd or "tesseract"]
    if tessdata_dir:
        cmd.extend(["--tessdata-dir", tessdata_dir])
    cmd.append("--list-langs")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("List of available languages")
    ]


def configure_tesseract_cmd() -> str:
    if pytesseract is None:
        return ""
    env_path = os.environ.get("TESSERACT_CMD", "").strip()
    candidates = [Path(env_path)] if env_path else []
    candidates.extend(TESSERACT_STANDARD_PATHS)
    for candidate in candidates:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return str(candidate)
    return shutil.which("tesseract") or ""


def find_tessdata_dir() -> str:
    env_prefix = os.environ.get("TESSDATA_PREFIX", "").strip()
    candidates = [Path(env_prefix)] if env_prefix else []
    candidates.extend(TESSDATA_STANDARD_DIRS)
    for candidate in candidates:
        if (candidate / "eng.traineddata").exists() and (candidate / "jpn.traineddata").exists():
            return str(candidate)
    return ""


def tesseract_config(psm: int | None = 6, extra: str = "") -> str:
    parts: list[str] = []
    tessdata_dir = find_tessdata_dir()
    if tessdata_dir:
        parts.extend(["--tessdata-dir", tessdata_dir])
    if psm is not None:
        parts.extend(["--psm", str(psm)])
    if extra:
        parts.append(extra)
    return " ".join(parts)


def ensure_dependencies() -> None:
    ok, messages = check_dependencies()
    if not ok:
        raise RuntimeError(
            "OCR dependencies are not ready:\n"
            + "\n".join(f"- {message}" for message in messages)
        )


def field_specs_to_json() -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for field in DEFAULT_FIELDS:
        item: dict[str, Any] = {
            "name": field.name,
            "page_type": field.page_type,
            "kind": field.kind,
        }
        if field.options:
            item["options"] = [
                {"code": option.code, "bbox": option.bbox} for option in field.options
            ]
        if field.bbox:
            item["bbox"] = field.bbox
        if field.relevant_if_field:
            item["relevant_if_field"] = field.relevant_if_field
            item["relevant_if_code"] = field.relevant_if_code
        payload.append(item)
    return payload


def field_specs_from_json(path: Path) -> tuple[FieldSpec, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fields: list[FieldSpec] = []
    for item in payload:
        options = tuple(
            opt(int(option["code"]), tuple(float(value) for value in option["bbox"]))
            for option in item.get("options", [])
        )
        bbox = item.get("bbox")
        fields.append(
            FieldSpec(
                name=str(item["name"]),
                page_type=str(item["page_type"]),
                kind=str(item["kind"]),
                options=options,
                bbox=tuple(float(value) for value in bbox) if bbox else None,
                relevant_if_field=item.get("relevant_if_field"),
                relevant_if_code=(
                    int(item["relevant_if_code"])
                    if item.get("relevant_if_code") is not None
                    else None
                ),
            )
        )
    return tuple(fields)


def field_specs_from_args(args: argparse.Namespace) -> tuple[FieldSpec, ...]:
    if args.layout_json:
        return field_specs_from_json(Path(args.layout_json))
    return DEFAULT_FIELDS


def list_images(input_dir: Path) -> list[Path]:
    images = [
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images, key=natural_key)


def crop_relative(image: Image.Image, bbox: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    x1, y1, x2, y2 = bbox
    return image.crop(
        (
            max(0, int(round(x1 * width))),
            max(0, int(round(y1 * height))),
            min(width, int(round(x2 * width))),
            min(height, int(round(y2 * height))),
        )
    )


def find_checkbox_crop(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
    max_frame_size: int = 70,
    min_frame_aspect: float = 0.70,
    max_frame_aspect: float = 1.30,
) -> tuple[Image.Image, str]:
    """Refine an expected checkbox bbox to the nearest detected square frame."""
    fallback = crop_relative(image, bbox)
    if cv2 is None or np is None:
        return fallback, "opencv_missing"

    width, height = image.size
    x1, y1, x2, y2 = bbox
    expected_cx = ((x1 + x2) / 2) * width
    expected_cy = ((y1 + y2) / 2) * height
    pad_x = max(18, int(round((x2 - x1) * width * 1.5)))
    pad_y = max(18, int(round((y2 - y1) * height * 1.5)))
    sx1 = max(0, int(round(expected_cx - pad_x)))
    sy1 = max(0, int(round(expected_cy - pad_y)))
    sx2 = min(width, int(round(expected_cx + pad_x)))
    sy2 = min(height, int(round(expected_cy + pad_y)))
    search = image.crop((sx1, sy1, sx2, sy2))
    gray = np.array(search.convert("L"))
    binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY_INV)[1]
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[tuple[float, tuple[int, int, int, int]]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if not (18 <= w <= max_frame_size and 18 <= h <= max_frame_size):
            continue
        aspect = w / h if h else 0
        if not min_frame_aspect <= aspect <= max_frame_aspect:
            continue
        rect_area = float(w * h)
        extent = cv2.contourArea(contour) / rect_area if rect_area else 0.0
        if extent < 0.25:
            continue
        cx = sx1 + x + (w / 2)
        cy = sy1 + y + (h / 2)
        distance = ((cx - expected_cx) ** 2 + (cy - expected_cy) ** 2) ** 0.5
        shape_penalty = abs(1.0 - aspect) * 10
        candidates.append((distance + shape_penalty, (sx1 + x, sy1 + y, w, h)))

    if not candidates:
        return fallback, "checkbox_frame_not_detected"

    _, (x, y, w, h) = min(candidates, key=lambda item: item[0])
    crop_pad = 4
    refined = image.crop(
        (
            max(0, x - crop_pad),
            max(0, y - crop_pad),
            min(width, x + w + crop_pad),
            min(height, y + h + crop_pad),
        )
    )
    return refined, ""


def save_crop(image: Image.Image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return str(path)


def mean_confidence(data: dict[str, list[Any]]) -> float | None:
    values: list[float] = []
    for raw in data.get("conf", []):
        try:
            value = float(raw)
        except Exception:
            continue
        if value >= 0:
            values.append(value)
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def ocr_text(image: Image.Image, lang: str = "jpn+eng", psm: int = 6) -> tuple[str, float | None]:
    if pytesseract is None or Output is None:
        return "", None
    data = pytesseract.image_to_data(
        image,
        lang=lang,
        output_type=Output.DICT,
        config=tesseract_config(psm=psm),
    )
    words = [str(word).strip() for word in data.get("text", []) if str(word).strip()]
    return " ".join(words).strip(), mean_confidence(data)


def extract_red_id(image: Image.Image, crop_dir: Path, image_stem: str) -> dict[str, Any]:
    roi = crop_relative(image, (0.58, 0.72, 0.98, 0.98))
    if cv2 is None or np is None:
        crop_path = save_crop(roi, crop_dir / f"{image_stem}_red_id.jpg")
        return {
            "red_id_raw": "",
            "response_id": "",
            "red_id_confidence": "",
            "red_id_crop": crop_path,
            "red_id_issue": "opencv_missing",
        }

    arr = np.array(roi.convert("RGB"))
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    lower1 = np.array([0, 55, 60])
    upper1 = np.array([12, 255, 255])
    lower2 = np.array([165, 55, 60])
    upper2 = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
    points = cv2.findNonZero(mask)
    if points is not None:
        x, y, w, h = cv2.boundingRect(points)
        pad = 20
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(roi.size[0], x + w + pad)
        y2 = min(roi.size[1], y + h + pad)
        id_crop = roi.crop((x1, y1, x2, y2))
    else:
        id_crop = roi
    id_crop = ImageOps.autocontrast(id_crop.convert("RGB"))
    crop_path = save_crop(id_crop, crop_dir / f"{image_stem}_red_id.jpg")

    if pytesseract is None or Output is None:
        return {
            "red_id_raw": "",
            "response_id": "",
            "red_id_confidence": "",
            "red_id_crop": crop_path,
            "red_id_issue": "pytesseract_missing",
        }
    data = pytesseract.image_to_data(
        id_crop,
        lang="eng",
        output_type=Output.DICT,
        config=tesseract_config(psm=7, extra="-c tessedit_char_whitelist=0123456789"),
    )
    raw = "".join(str(word).strip() for word in data.get("text", []))
    digits = re.sub(r"\D", "", raw)
    response_id = normalize_response_id(digits) if digits else ""
    return {
        "red_id_raw": raw,
        "response_id": response_id,
        "red_id_confidence": mean_confidence(data) or "",
        "red_id_crop": crop_path,
        "red_id_issue": "" if response_id else "red_id_unreadable",
    }


def normalize_response_id(value: str) -> str:
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return ""
    return f"GS-{int(digits):04d}"


def sequence_response_id(index: int, sequence_start: int) -> str:
    return normalize_response_id(str(sequence_start + (index // len(PAGE_TYPES))))


def sequence_page_position(index: int) -> int:
    return (index % len(PAGE_TYPES)) + 1


def classify_page_type(
    image: Image.Image,
    index: int,
    allow_sequence_fallback: bool,
) -> tuple[str, str, float | None]:
    text, conf = ocr_text(image, lang="jpn+eng", psm=6)
    compact = re.sub(r"\s+", "", text)
    if "アンケートへのご回答にあたって" in compact or "調査の目的" in compact:
        return "cover", text, conf
    if "Q1" in compact and "Q5" in compact:
        return "page_q1_q5", text, conf
    if "Q6" in compact and "Q9" in compact:
        return "page_q6_q9", text, conf
    if "Q10" in compact and "Q11" in compact:
        return "page_q10_q11", text, conf
    if allow_sequence_fallback:
        return PAGE_TYPES[index % len(PAGE_TYPES)], text, conf
    return "unknown", text, conf


def check_mark_score(crop: Image.Image) -> float:
    if cv2 is None or np is None:
        return 0.0
    gray = np.array(crop.convert("L"))
    height, width = gray.shape[:2]
    x1 = int(width * 0.25)
    x2 = int(width * 0.75)
    y1 = int(height * 0.25)
    y2 = int(height * 0.75)
    center = gray[y1:y2, x1:x2]
    if center.size == 0:
        center = gray
    dark_ratio = float((center < 185).mean())
    return round(dark_ratio, 4)


def parse_code_list(value: str) -> set[int]:
    codes: set[int] = set()
    for token in str(value or "").split(";"):
        token = token.strip()
        if not token:
            continue
        try:
            codes.add(int(token))
        except ValueError:
            continue
    return codes


def readable_text(value: str) -> bool:
    text = re.sub(r"\s+", "", value)
    if not text:
        return False
    return bool(re.search(r"[ぁ-んァ-ン一-龥A-Za-z0-9]", text))


def candidate_row(
    response_id: str,
    source_file: str,
    page_type: str,
    field: str,
    value: str,
    confidence: Any,
    crop_path: str,
    needs_review: bool,
    review_reason: str,
) -> dict[str, Any]:
    return {
        "response_id": response_id,
        "source_file": source_file,
        "page_type": page_type,
        "field": field,
        "value": value,
        "confidence": confidence,
        "crop_path": crop_path,
        "needs_review": int(needs_review),
        "review_reason": review_reason,
    }


def process_choice_field(
    image: Image.Image,
    image_path: Path,
    crop_dir: Path,
    response_id: str,
    page_type: str,
    field: FieldSpec,
) -> dict[str, Any]:
    max_frame_size = 95 if field.name in WIDE_CHECKBOX_FRAME_FIELDS else 70
    min_frame_aspect = 0.45 if field.name in WIDE_CHECKBOX_FRAME_FIELDS else 0.70
    max_frame_aspect = 1.45 if field.name in WIDE_CHECKBOX_FRAME_FIELDS else 1.30

    def evaluate_options(
        options: tuple[OptionSpec, ...],
        crop_suffix: str = "",
    ) -> tuple[list[int], list[int], list[str], dict[int, float], list[str]]:
        selected: list[int] = []
        ambiguous: list[int] = []
        detection_issues: list[str] = []
        scores: dict[int, float] = {}
        crop_paths: list[str] = []
        for option in options:
            crop, detection_issue = find_checkbox_crop(
                image,
                option.bbox,
                max_frame_size=max_frame_size,
                min_frame_aspect=min_frame_aspect,
                max_frame_aspect=max_frame_aspect,
            )
            crop_path = save_crop(
                crop,
                crop_dir
                / f"{response_id or 'unknown'}_{image_path.stem}_{field.name}{crop_suffix}_{option.code}.jpg",
            )
            crop_paths.append(crop_path)
            score = 0.0 if detection_issue else check_mark_score(crop)
            scores[option.code] = score
            if score >= CHECK_SELECTED_THRESHOLD:
                selected.append(option.code)
            elif score >= CHECK_AMBIGUOUS_THRESHOLD:
                ambiguous.append(option.code)
            if detection_issue:
                ambiguous.append(option.code)
                detection_issues.append(f"{detection_issue}:{option.code}")
        return selected, ambiguous, detection_issues, scores, crop_paths

    selected, ambiguous, detection_issues, scores, crop_paths = evaluate_options(
        field.options
    )
    fallback_used = False
    if (
        field.kind == "single"
        and len(selected) != 1
        and field.name in REAL_SCAN_SINGLE_FALLBACK_OPTIONS
    ):
        (
            fallback_selected,
            fallback_ambiguous,
            fallback_detection_issues,
            fallback_scores,
            fallback_crop_paths,
        ) = evaluate_options(REAL_SCAN_SINGLE_FALLBACK_OPTIONS[field.name], "_fallback")
        if len(fallback_selected) == 1:
            selected = fallback_selected
            ambiguous = fallback_ambiguous
            detection_issues = fallback_detection_issues
            scores = fallback_scores
            crop_paths.extend(fallback_crop_paths)
            fallback_used = True

    review_reasons: list[str] = []
    if cv2 is None or np is None:
        review_reasons.append("opencv_missing")
    if field.kind == "single":
        value = str(selected[0]) if len(selected) == 1 else "99"
        if len(selected) == 0:
            review_reasons.append("no_mark_detected")
        elif len(selected) > 1:
            review_reasons.append("multiple_marks_detected")
    else:
        value = ";".join(str(code) for code in sorted(selected))
    if ambiguous:
        review_reasons.append(
            "ambiguous_mark_score:" + ";".join(map(str, sorted(set(ambiguous))))
        )
    review_reasons.extend(sorted(set(detection_issues)))
    if fallback_used:
        review_reasons.append("fallback_layout_used")

    return candidate_row(
        response_id=response_id,
        source_file=str(image_path),
        page_type=page_type,
        field=field.name,
        value=value,
        confidence=json.dumps(scores, ensure_ascii=False),
        crop_path=";".join(crop_paths),
        needs_review=bool(review_reasons),
        review_reason=";".join(review_reasons),
    )


def process_text_field(
    image: Image.Image,
    image_path: Path,
    crop_dir: Path,
    response_id: str,
    page_type: str,
    field: FieldSpec,
    current_values: dict[str, str],
) -> dict[str, Any]:
    assert field.bbox is not None
    relevant = True
    if field.relevant_if_field and field.relevant_if_code is not None:
        relevant = field.relevant_if_code in parse_code_list(
            current_values.get(field.relevant_if_field, "")
        )
    crop = crop_relative(image, field.bbox)
    crop_path = save_crop(crop, crop_dir / f"{response_id or 'unknown'}_{image_path.stem}_{field.name}.jpg")
    if not relevant:
        value = ""
        confidence = ""
        review_reasons: list[str] = []
    else:
        value, confidence = ocr_text(ImageOps.autocontrast(crop.convert("RGB")), psm=6)
        review_reasons = []
        if pytesseract is None:
            review_reasons.append("pytesseract_missing")
        if not value:
            review_reasons.append("free_text_blank")
        if confidence is not None and confidence < TEXT_CONFIDENCE_THRESHOLD:
            review_reasons.append("low_text_confidence")
        if value and not readable_text(value):
            review_reasons.append("text_not_readable")
    return candidate_row(
        response_id=response_id,
        source_file=str(image_path),
        page_type=page_type,
        field=field.name,
        value=value,
        confidence=confidence if confidence is not None else "",
        crop_path=crop_path,
        needs_review=bool(review_reasons),
        review_reason=";".join(review_reasons),
    )


def process_fields_for_page(
    image: Image.Image,
    image_path: Path,
    crop_dir: Path,
    response_id: str,
    page_type: str,
    field_specs: tuple[FieldSpec, ...],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    current_values: dict[str, str] = {}
    fields = [field for field in field_specs if field.page_type == page_type]
    for field in fields:
        if field.kind in {"single", "multi"}:
            row = process_choice_field(
                image=image,
                image_path=image_path,
                crop_dir=crop_dir,
                response_id=response_id,
                page_type=page_type,
                field=field,
            )
            current_values[field.name] = str(row["value"])
            candidates.append(row)
    for field in fields:
        if field.kind == "text":
            row = process_text_field(
                image=image,
                image_path=image_path,
                crop_dir=crop_dir,
                response_id=response_id,
                page_type=page_type,
                field=field,
                current_values=current_values,
            )
            current_values[field.name] = str(row["value"])
            candidates.append(row)
    return candidates


def build_review_row(
    response_id: str,
    source_file: str,
    page_type: str,
    field: str,
    issue_type: str,
    candidate_value: str = "",
    crop_path: str = "",
) -> dict[str, Any]:
    return {
        "response_id": response_id,
        "source_file": source_file,
        "page_type": page_type,
        "field": field,
        "issue_type": issue_type,
        "candidate_value": candidate_value,
        "crop_path": crop_path,
        "resolved_value": "",
        "notes": "",
    }


def default_response_row(response_id: str) -> dict[str, Any]:
    row = {column: "" for column in EXPECTED_COLUMNS}
    row["response_id"] = response_id
    row["confirmed"] = ""
    row["source_files"] = ""
    row["review_crop_paths"] = ""
    for column in NUMERIC_COLUMNS:
        row[column] = "99"
    return row


def aggregate_responses(
    pages: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    review_rows: list[dict[str, Any]] = []
    ids = sorted({str(page["response_id"]) for page in pages if str(page["response_id"])})
    ids.extend(
        sorted(
            {
                f"UNREADABLE_{Path(str(page['source_file'])).stem}"
                for page in pages
                if not str(page["response_id"])
            }
        )
    )
    response_rows = {response_id: default_response_row(response_id) for response_id in ids}
    review_by_id: dict[str, list[str]] = {response_id: [] for response_id in ids}

    pages_by_id: dict[str, list[dict[str, Any]]] = {}
    for page in pages:
        response_id = str(page["response_id"]) or f"UNREADABLE_{Path(str(page['source_file'])).stem}"
        pages_by_id.setdefault(response_id, []).append(page)
    for response_id, group in pages_by_id.items():
        response_rows.setdefault(response_id, default_response_row(response_id))
        response_rows[response_id]["source_files"] = ";".join(
            str(page["source_file"]) for page in sorted(group, key=lambda page: int(page["file_order"]))
        )
        response_rows[response_id]["review_crop_paths"] = ";".join(
            str(page.get("red_id_crop", "")) for page in group if str(page.get("red_id_crop", ""))
        )
        page_types = [str(page["page_type"]) for page in group]
        missing = [page_type for page_type in PAGE_TYPES if page_type not in page_types]
        duplicates = sorted({page_type for page_type in page_types if page_types.count(page_type) > 1})
        if missing:
            issue = "missing_pages:" + ";".join(missing)
            review_by_id.setdefault(response_id, []).append(issue)
            review_rows.append(build_review_row(response_id, "", "", "__pages__", issue))
        if duplicates:
            issue = "duplicate_page_types:" + ";".join(duplicates)
            review_by_id.setdefault(response_id, []).append(issue)
            review_rows.append(build_review_row(response_id, "", "", "__pages__", issue))
        for page in group:
            if page.get("needs_review"):
                issue = str(page.get("review_reason", "page_needs_review"))
                review_by_id.setdefault(response_id, []).append(issue)
                review_rows.append(
                    build_review_row(
                        response_id=response_id,
                        source_file=str(page["source_file"]),
                        page_type=str(page["page_type"]),
                        field="__page__",
                        issue_type=issue,
                        crop_path=str(page.get("red_id_crop", "")),
                    )
                )

    for candidate in candidates:
        response_id = str(candidate["response_id"]) or f"UNREADABLE_{Path(str(candidate['source_file'])).stem}"
        response_rows.setdefault(response_id, default_response_row(response_id))
        field = str(candidate["field"])
        if field in EXPECTED_COLUMNS:
            response_rows[response_id][field] = str(candidate["value"])
        crop_path = str(candidate["crop_path"])
        if crop_path:
            current_crops = str(response_rows[response_id].get("review_crop_paths", ""))
            response_rows[response_id]["review_crop_paths"] = (
                f"{current_crops};{crop_path}" if current_crops else crop_path
            )
        if int(candidate["needs_review"]):
            issue = str(candidate["review_reason"])
            review_by_id.setdefault(response_id, []).append(f"{field}:{issue}")
            review_rows.append(
                build_review_row(
                    response_id=response_id,
                    source_file=str(candidate["source_file"]),
                    page_type=str(candidate["page_type"]),
                    field=field,
                    issue_type=issue,
                    candidate_value=str(candidate["value"]),
                    crop_path=str(candidate["crop_path"]),
                )
            )

    for response_id, row in response_rows.items():
        issues = sorted(set(review_by_id.get(response_id, [])))
        row["needs_review"] = int(bool(issues))
        row["review_reasons"] = ";".join(issues)
    return list(response_rows.values()), review_rows


def page_needs_review(page: dict[str, Any]) -> tuple[bool, str]:
    reasons: list[str] = []
    if not page["response_id"]:
        reasons.append("red_id_unreadable")
    if page["page_type"] == "unknown":
        reasons.append("page_type_unknown")
    if page["page_type"] == "cover":
        reasons.append("unexpected_cover_page_scanned")
    if page.get("red_id_issue"):
        reasons.append(str(page["red_id_issue"]))
    return bool(reasons), ";".join(sorted(set(reasons)))


def run_ingest(args: argparse.Namespace) -> Path:
    ensure_dependencies()
    input_dir = Path(args.input_dir) if args.input_dir else None
    if input_dir is None or not input_dir.exists():
        raise FileNotFoundError("--input-dir is required and must exist")
    field_specs = field_specs_from_args(args)
    output_dir = output_dir_from_args(args)
    output_dir.mkdir(parents=True, exist_ok=True)
    crop_dir = output_dir / "review_crops"
    crop_dir.mkdir(parents=True, exist_ok=True)

    pages: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    images = list_images(input_dir)
    if not images:
        raise RuntimeError(f"No JPEG/PNG images found in {input_dir}")
    if args.sequence_response_ids and len(images) % len(PAGE_TYPES) != 0:
        raise RuntimeError(
            f"--sequence-response-ids requires image count to be a multiple of {len(PAGE_TYPES)}; "
            f"found {len(images)}"
        )

    for index, image_path in enumerate(images):
        with Image.open(image_path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
        red_id = extract_red_id(image, crop_dir, image_path.stem)
        if args.sequence_page_types:
            page_type, page_text, page_conf = PAGE_TYPES[index % len(PAGE_TYPES)], "", None
        else:
            page_type, page_text, page_conf = classify_page_type(
                image, index, args.allow_sequence_page_fallback
            )
        red_response_id = str(red_id["response_id"])
        if args.sequence_response_ids:
            response_id = sequence_response_id(index, args.sequence_start)
            response_id_source = "sequence"
            red_id_issue = ""
            red_id_ocr_issue = str(red_id["red_id_issue"])
            red_id_mismatch = (
                f"red_id_mismatch:{red_response_id}"
                if red_response_id and red_response_id != response_id
                else ""
            )
        else:
            response_id = red_response_id
            response_id_source = "red_ocr"
            red_id_issue = str(red_id["red_id_issue"])
            red_id_ocr_issue = str(red_id["red_id_issue"])
            red_id_mismatch = ""
        page = {
            "source_file": str(image_path),
            "file_order": index + 1,
            "set_page_position": sequence_page_position(index),
            "red_id_raw": red_id["red_id_raw"],
            "red_response_id": red_response_id,
            "response_id": response_id,
            "response_id_source": response_id_source,
            "red_id_confidence": red_id["red_id_confidence"],
            "red_id_crop": red_id["red_id_crop"],
            "page_type": page_type,
            "page_ocr_confidence": page_conf if page_conf is not None else "",
            "page_ocr_preview": page_text[:240],
            "red_id_issue": red_id_issue,
            "red_id_ocr_issue": red_id_ocr_issue,
            "red_id_mismatch": red_id_mismatch,
        }
        needs_review, reason = page_needs_review(page)
        page["needs_review"] = int(needs_review)
        page["review_reason"] = reason
        pages.append(page)
        if page_type in PAGE_TYPES:
            candidates.extend(
                process_fields_for_page(
                    image=image,
                    image_path=image_path,
                    crop_dir=crop_dir,
                    response_id=str(response_id),
                    page_type=page_type,
                    field_specs=field_specs,
                )
            )

    response_rows, review_rows = aggregate_responses(pages, candidates)

    pd.DataFrame(pages).to_csv(output_dir / "ocr_pages.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(candidates).to_csv(
        output_dir / "ocr_candidates.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(review_rows).to_csv(
        output_dir / "ocr_review_queue.csv", index=False, encoding="utf-8-sig"
    )
    reviewed_columns = EXPECTED_COLUMNS + [
        "confirmed",
        "needs_review",
        "review_reasons",
        "source_files",
        "review_crop_paths",
    ]
    pd.DataFrame(response_rows).reindex(columns=reviewed_columns).to_csv(
        output_dir / "aomori_survey_responses_reviewed.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return output_dir


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Failed to read CSV: {last_error}")


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def finalize_reviewed(args: argparse.Namespace) -> Path:
    if not args.reviewed_csv:
        raise ValueError("--reviewed-csv is required with --finalize-reviewed")
    reviewed_csv = Path(args.reviewed_csv)
    df = read_csv_with_fallback(reviewed_csv)
    missing = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing:
        raise KeyError(f"Reviewed CSV is missing expected columns: {missing}")
    if len(df) != int(args.expected_responses):
        raise RuntimeError(
            f"Reviewed CSV has {len(df)} response rows; expected {args.expected_responses}."
        )
    if "confirmed" not in df.columns:
        raise KeyError("Reviewed CSV is missing required confirmation column: confirmed")
    confirmed = df["confirmed"].apply(truthy)
    if not bool(confirmed.all()):
        raise RuntimeError(
            f"Reviewed CSV has {int((~confirmed).sum())} rows without confirmed=1. "
            "Confirm every response before finalization."
        )
    output_columns = EXPECTED_COLUMNS + [
        column for column in ANALYSIS_DERIVED_COLUMNS if column in df.columns
    ]
    out = df[output_columns].copy()
    for column in NUMERIC_COLUMNS:
        out[column] = out[column].replace("", "99")
    final_output = Path(args.final_output)
    final_output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(final_output, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    return final_output


def main() -> None:
    args = parse_args()
    if args.write_layout_json:
        path = Path(args.write_layout_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(field_specs_to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(path)
        return
    if args.check_deps:
        ok, messages = check_dependencies()
        print("\n".join(messages))
        if not ok:
            sys.exit(1)
        return
    if args.finalize_reviewed:
        final_output = finalize_reviewed(args)
        print(final_output)
        return
    output_dir = run_ingest(args)
    print(output_dir)


if __name__ == "__main__":
    main()
