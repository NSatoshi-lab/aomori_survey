# Step 5 集計仕様（配布版Q1-Q11対応 v3）

## 目的

- 紙アンケート回収後に、必須3表と品質指標を再現可能に作成する。
- 配布版Q1-Q11を正として、OCR取り込み後の匿名化済み解析CSVをPythonで再集計する。
- 便宜抽出の限界を明示した上で、浴室暖房乾燥機の設置・使用状況、セントラル暖房使用、寒さ体感、未導入/未使用理由を要約する。

## サンプルサイズ前提（固定）

- 信頼水準: 95%
- 許容誤差: ±12pp
- 比率推定の保守設定: `p=0.5`
- 便宜抽出補正: `deff=1.2`
- 無効・主要欠損見込み: 15%
- 計算結果:
  - `n0 = 1.96^2 * p*(1-p) / E^2 = 66.7 -> 67`
  - `n_valid = ceil(67 * 1.2) = 81`
  - `n_collected = ceil(81 / 0.85) = 96`
  - 運用目標回収票: 100

## 入力データ

- 入力CSV:
  - `data/processed/aomori_survey_responses_anonymized.csv`
- 入力テンプレート:
  - `deliverables/04_data_entry_analysis/20260430_aomori_survey_data_entry_template_v2.csv`
- コードブック:
  - `deliverables/04_data_entry_analysis/20260430_aomori_survey_codebook_v2.md`
- 必須カラム:
  - `response_id`
  - `q2_housing_type`
  - `q7_bath_heater_status`
  - `q8_reason_codes`
  - `q9_central_heating_use`
  - `q11_bathroom_cold_7pt`
- Pythonスクリプトは、入力テンプレート定義の全カラムを要求する。

## 主解析仕様

- Q7は配布版の3値ステータスとして扱う。
  - `1`: 設置しており使用もしている
  - `2`: 設置しているが使用していない
  - `3`: 設置も使用もしていない
  - `99`: 無回答/判定不能
- Q7×Q9は記述統計（割合＋95%CI）を主とする。
  - 小標本で期待度数が小さい場合は exact 法を優先する。
  - exact 法の実装がない環境では、検定結果を省略し記述統計のみで解釈する。
- Q8理由（`q8_reason_codes`）は多重回答率で集計し、群差は探索的解釈に限定する。
- 居住地域は配布版で取得していないため、解析CSVには含めない。

## 出力物（必須）

- `qc_summary.csv`
  - 総票数、有効票数、無効票数、主要欠損率、解析ゲート判定
- `table1_q7_status_x_bathroom_cold_7pt.csv`
  - 表1: Q7ステータス × 浴室寒さ7段階
- `table2_q7_status_x_central_heating.csv`
  - 表2: Q7ステータス × セントラル暖房使用
- `table3_q8_reason_x_housing_type.csv`
  - 表3: Q8理由 × 住宅種別
- `tabulation_report.md`
  - 実行ログ、主要指標、判定ルール適用結果、割合・95%CI

## 無効票判定

- 次のいずれかに該当する票を無効とする。
  - `q7_bath_heater_status` 欠損
  - Q7が2または3で、`q8_reason_codes` 欠損
  - `q11_bathroom_cold_7pt` 欠損

## 優勢判定（Step 6用）

- `no_need`（不要群）と `barrier`（障壁群）を集計し、差が10pp以上なら優勢と判定する。
- Q8理由コード1を不要群、コード2-7を障壁群として扱う。
- コード8（その他）は自由記述確認後に別途カテゴリ化し、一次判定では上記2群に含めない。
- 10pp未満は「拮抗」として扱う。

## 解析ゲート

- `valid_responses >= 80` かつ `main_missing_rate_pct < 20`:
  - 主解析として結果を本文で解釈する。
- `60 <= valid_responses < 80` かつ `main_missing_rate_pct < 20`:
  - 探索的解析として提示し、結論は限定的記述に留める。
- `valid_responses < 60` または `main_missing_rate_pct >= 20`:
  - 記述統計中心とし、比較結論は保留する。

## 実行コマンド

```powershell
python src/scripts/tabulate_aomori_paper_survey.py `
  --input-csv data/processed/aomori_survey_responses_anonymized.csv `
  --output-dir outputs/runs/20260430_aomori_paper_survey_tabulation
```

## 受け入れ基準

- 計算再現テスト: `E=0.12, deff=1.2, invalid=0.15` で `有効81/回収96/運用100` が再現できる。
- 感度テスト: `E=0.10` で回収目標が100票超、`E=0.15` で回収目標が大きく減る。
- 解析ゲート判定が `>=80`, `60-79`, `<60` の3区分で一意に出力される。
- 必須3表を生成する。
- 修正済みCSV、Excel一次集計、Python再集計が一致する。
