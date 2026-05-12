# Aomori Survey OCR Ingest System Test Report

## Test Date

- 2026-05-12

## Input Checked

- Scan directory: `C:\Users\cross\Desktop\作成中書類\研究\青森アンケート\青森アンケート`
- Image files found: 462
- Expected count: 154 responses x 3 pages = 462
- Count check: pass

## Commands Run

```powershell
python src\scripts\ocr_ingest_aomori_survey.py --check-deps
python src\scripts\ocr_ingest_aomori_survey.py --input-dir outputs\runs\20260512_ocr_ingest_system_test_input_9 --output-dir outputs\runs\20260512_ocr_ingest_system_test_9 --allow-sequence-page-fallback
python src\scripts\ocr_ingest_aomori_survey.py --finalize-reviewed --reviewed-csv outputs\runs\20260512_ocr_ingest_system_test_9\aomori_survey_responses_reviewed.csv --final-output outputs\runs\20260512_ocr_ingest_system_test_9\finalize_smoke_test.csv --allow-review-pending
```

## Results

- OCR dependencies: pass
  - OpenCV import OK
  - pytesseract import OK
  - Tesseract 5.5.0 available
  - Tesseract languages `jpn` and `eng` available
- Small real-scan ingest: pass for execution
  - Test input: first 9 images, linked into `outputs/runs/20260512_ocr_ingest_system_test_input_9`
  - Output directory: `outputs/runs/20260512_ocr_ingest_system_test_9`
  - Generated `ocr_pages.csv`, `ocr_candidates.csv`, `ocr_review_queue.csv`, `aomori_survey_responses_reviewed.csv`, and `review_crops/`
- Page classification with sequence fallback: pass
  - `page_q1_q5`: 3 pages
  - `page_q6_q9`: 3 pages
  - `page_q10_q11`: 3 pages
- Finalize smoke test: pass
  - Reviewed CSV column validation and output writing succeeded to `finalize_smoke_test.csv`

## Blocking Findings Before Production

- Red handwritten ID OCR is not reliable on the first 9 real scans.
  - 6 of 9 page IDs were unreadable.
  - One visible `3` was OCR-read as `2`.
  - The current system should not use red ID OCR alone as the primary response ID source.
- Fixed checkbox coordinates do not match the current scanned images closely enough.
  - Example: first page visually shows Q1=8, Q2=1, Q3=4, Q4=1, Q5=3.
  - The OCR candidate output instead included Q1=7, Q2=2, and several `99` review values.
  - This indicates coordinate calibration is required before production ingest.

## Recommendation

- Do not run production ingest yet.
- Add an explicit sequence-based response ID mode for this scan batch, because files are confirmed to be ordered as 154 sets of 3 pages.
- Recalibrate checkbox coordinates against the actual 2026-05-11 scans, or replace fixed coordinates with image-based checkbox detection.
- After recalibration, rerun the same 9-image smoke test and compare against manual readings before processing all 462 images.
