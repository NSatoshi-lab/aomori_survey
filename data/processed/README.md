# Processed Data

このディレクトリには、解析に使う匿名化済みデータだけを保存する。

## 管理方針

- 紙原票、スキャン、個人が推測できるメモ、詳細回収台帳はGit管理しない。
- 上記の生データ・作業メモは `data/raw/` または外部保管先で管理する。
- 匿名ID単位の入力済み解析CSVは `data/processed/aomori_survey_responses_anonymized.csv` とする。
- 実配布・回収状況の公開可能な要約は `data/processed/aomori_survey_collection_summary.csv` に保存する。

## 期待する解析CSV

- 1行は1回答票を表す。
- 列定義は `deliverables/04_data_entry_analysis/20260430_aomori_survey_codebook_v2.md` に従う。
- 初期入力時のヘッダは `deliverables/04_data_entry_analysis/20260430_aomori_survey_data_entry_template_v2.csv` を使う。

## OCR目視確認済みデータ

- 本解析の主データは `data/processed/aomori_survey_responses_reviewed_confirmed.csv` とする。
- `data/processed/aomori_survey_responses_reviewed_manual_latest.csv` は、`manual_review_decisions.csv` を全件反映した承認前状態の監査用データとして保持する。
- 由来runは `outputs/runs/20260512_ocr_ingest_q6_q99_scoped_patch_full_dry_run/`。
- 同run配下の元OCR出力と `manual_review_decisions.csv` は監査証跡として保持するが、`outputs/runs/` はGit管理対象外のため、本解析に使う重要CSVはこのディレクトリで追跡する。
