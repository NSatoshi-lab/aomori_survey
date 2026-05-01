# 五所川原市 紙アンケート OCR取り込み仕様（v1）

## 目的

- スキャナーでJPEG化した配布版2-4ページ回答票を、匿名ID単位の解析CSVへ変換する。
- OCRと画像処理の低信頼ケースを検出し、目視確認できる形で出力する。
- 確定済み匿名CSVだけを `data/processed/aomori_survey_responses_anonymized.csv` として集計へ渡す。

## 入力画像

- 入力フォルダには完成版JPEGだけを置く。
- アンケート用紙1枚目（表紙・同意説明）は回答項目がないためスキャン対象外とし、各セット2-4枚目だけを入力する。
- スキャン標準はカラー300dpi、A4縦、傾きと欠けが少ない状態とする。
- ファイル名は自然順で読むが、回答票の確定は赤字IDとページ内容判定で行う。
- 赤字IDは各ページ右下に数字のみで大きく記入する。
- 取り込み時は `1` を `GS-0001`、`12` を `GS-0012` のように正規化する。

## OCR構成

- ローカルOCRはTesseract 5系を既定とし、`jpn` と `eng` のtraineddataを使う。
- Python依存は `pytesseract`, `opencv-python`, `Pillow`, `pandas` を使う。
- Tesseractが未導入または日本語データがない場合、取り込みスクリプトの依存確認で停止する。
- 画像や自由記述は外部サービスへ送信しない。

## ページ判定

- ページ種別は印字内容から判定する。
- 期待するページ種別は `page_q1_q5`, `page_q6_q9`, `page_q10_q11` の3種類。
- `--allow-sequence-page-fallback` 使用時は、入力画像が各セット2-4枚目だけで自然順に並んでいる前提で3枚周期に割り当てる。
- 1つの `response_id` で3種類が揃わない場合、同じページ種別が重複する場合、または表紙ページが混入した場合は目視確認に回す。

## 回答判定

- チェック欄は固定帳票の相対座標で切り出し、チェック欄中央部の濃色画素比で選択候補を判定する。
- 単一選択で複数候補が閾値を超えた場合、選択候補なしの場合、または閾値付近の場合は自動確定せずレビュー対象にする。
- 複数選択は閾値を超えた候補を `;` 区切りで保存する。候補なしの場合は空文字とする。
- 自由記述はTesseractの候補文字列と平均信頼度を保存する。信頼度が低い、空欄疑い、日本語として崩れている場合は切り出し画像付きでレビュー対象にする。

## 出力

- 既定のrun出力先は `outputs/runs/YYYYMMDD_HHMMSS_ocr_ingest/` とする。
- `ocr_pages.csv`: 画像ファイル単位の赤字ID、正規化ID、ページ種別、ページレベルのレビュー要否。
- `ocr_candidates.csv`: 設問単位の候補値、信頼度、切り出し画像パス、レビュー要否。
- `ocr_review_queue.csv`: 目視確認が必要なID、ページ、設問、理由、候補値。
- `review_crops/`: 赤字ID、チェック欄、自由記述欄の切り出し画像。
- `aomori_survey_responses_reviewed.csv`: OCR候補を行単位に集約した修正用CSV。目視修正後、このファイルを正として最終化する。

## 最終化

- OCR直後のCSVは候補値であり、レビュー対象が残る場合は最終解析CSVにしない。
- 目視確認後、修正済み `aomori_survey_responses_reviewed.csv` を入力として最終化し、`data/processed/aomori_survey_responses_anonymized.csv` を作成する。
- スキャンJPEG、切り出し画像、OCR中間ファイルはGit管理しない。

## 実行例

```powershell
python src/scripts/ocr_ingest_aomori_survey.py --check-deps
python src/scripts/ocr_ingest_aomori_survey.py --input-dir C:\path\to\scans
python src/scripts/ocr_ingest_aomori_survey.py `
  --finalize-reviewed `
  --reviewed-csv outputs\runs\20260430_120000_ocr_ingest\aomori_survey_responses_reviewed.csv `
  --final-output data\processed\aomori_survey_responses_anonymized.csv
```

## 受け入れ基準

- 空の配布版2-4ページ由来画像で、ページ種別が3種類に分類される。
- 赤字数字 `1` と `12` が、それぞれ `GS-0001` と `GS-0012` に正規化される。
- 欠損ページ、同一ID内の重複ページ、単一選択の複数チェック、自由記述低信頼が `ocr_review_queue.csv` に出る。
- 目視修正済みCSVから `data/processed/aomori_survey_responses_anonymized.csv` を作成できる。
