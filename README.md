# 青森調査: Repo Index (Codex Agent Navigation)

このリポジトリは、「青森県における浴室暖房の実態調査」を進めるための作業用リポジトリです。基盤repo（入浴統計）を**参照専用（read-only）**として扱い、成果物・新規解析・文献ログは本repoに集約します。

## Start Here (Most Important Paths)

- Manuscript Markdown (authoritative): `paper.md` / `paper_en.md`
- Final and fieldwork deliverables: `deliverables/`
- Evidence runs: `outputs/runs/`
- Anonymized analysis data: `data/processed/`
- Literature log: `refs.md`, `refs/search/`
- Code entry points: `src/scripts/`
- Writing rules: `docs/rules/markdown_generation_rules.md`, `docs/rules/statistical_reporting_policy.md`
- Agent skills: `.codex/skills/`

## Base Repo (Read-Only)

Base repo: `..\入浴統計`（参照専用）

| Read from base | Purpose |
| --- | --- |
| `..\入浴統計\deliverables\` | 完成版成果物（完成稿） |
| `..\入浴統計\outputs\runs\` | 完成版成果物に直結する根拠run |
| `..\入浴統計\data\processed\` | 完成版成果物に直結するデータ |
| `..\入浴統計\refs.md` / `..\入浴統計\refs\search\` | 既存研究の文献探索ログ |

## Write Here (This Repo Only)

| Write here | Purpose |
| --- | --- |
| `paper.md` / `paper_en.md` | 原稿（mdが正） |
| `deliverables/` | フェーズ別の設計資料・倫理書類・配布物・集計仕様 |
| `data/processed/` | Git管理可能な匿名化済み解析データ |
| `outputs/runs/` | 解析・感度分析のrun成果物 |
| `refs.md` / `refs/search/` | 文献探索ログ |
| `src/` | 青森調査の解析コード |

## Deliverables Layout

| Path | Purpose |
| --- | --- |
| `deliverables/01_planning/` | 事前調査レポート、進行管理ログ |
| `deliverables/02_ethics/` | 倫理審査申請書、COI最新版 |
| `deliverables/03_fieldwork_materials/` | 調査票、配布用docx/pdf/html、広告、表紙、現地運用手順、回収台帳テンプレート |
| `deliverables/04_data_entry_analysis/` | コードブック、入力テンプレート、集計仕様、認知テスト関連テンプレート |
| `deliverables/archive/` | 置換済みバックアップなど、通常参照しない過去版 |

## Survey Data Flow

- 紙原票、スキャン、個人が推測できるメモ、詳細回収台帳は `data/raw/` または外部保管先で管理し、Git管理しない。
- 匿名ID単位の入力済み解析CSVは `data/processed/aomori_survey_responses_anonymized.csv` とする。
- 実配布・回収状況の公開可能な要約だけ必要な場合は `data/processed/aomori_survey_collection_summary.csv` とする。
- 集計は `src/scripts/tabulate_aomori_paper_survey.py` を使い、結果は `outputs/runs/<tag>/` に出す。

## Workflow (md → docx)

- 編集は `paper.md` / `paper_en.md` を正とする。
- 引用は `refs.md` と `refs/search/` に先に記録し、本文へ反映する。
- docx生成は `src/scripts/build_paper_docx.ps1` を使い、生成物は `outputs/runs/<tag>/` に出す。
- 調査票の配布用docx生成は `src/scripts/build_questionnaire_docx.ps1` を使う。
- 生成物は `outputs/runs/<tag>/` に出す。
- 投稿用の最終成果物は適切な `deliverables/` サブディレクトリに置く。

### Questionnaire (md → docx)

固定コマンド例:

```powershell
pwsh src/scripts/build_questionnaire_docx.ps1 -Tag 20260209_questionnaire_docx_test
```

## Rules (Must Follow)

- Markdown rules: `docs/rules/markdown_generation_rules.md`
- Statistical reporting policy: `docs/rules/statistical_reporting_policy.md`
- 文献探索ログは `refs/search/` に保存し、`refs.md` へ要約してから本文へ反映する。
