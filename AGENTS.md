# AGENTS

## 目的

- 青森調査repoの作業規約を定義し、Codex Agent運用を安定させる。
- 基盤repo（`..\入浴統計`）は参照専用（read-only）とする。

## 常時ルール

- 解析結果や本文の記述は `docs/rules/statistical_reporting_policy.md` に従う。
- Markdown編集は `docs/rules/markdown_generation_rules.md` を必ず満たす。
- 生データ/キャッシュはGit管理しない（`data/raw/` 以下に新規追跡ファイルを作らない）。
- 文献探索の根拠は `refs.md` に記録してから本文へ反映する。
- 文献探索ログは `refs/search/` に1検索1ファイル（`YYYYMMDD_HHMMSS_<slug>.json`）で保存し、`refs.md` に要約とリンクを記載する。
- 非OA/取得不可の場合は `refs.md` に DOI+URL+検索日+DB+クエリ を最小情報として残す。

## SKILLの優先使用（該当タスクでは必ず使用）

- 文献探索ログ（`refs.md`）の更新: `$literature-refs`
- 文献検索/取得/引用: `$zotero-cite`
- 原稿執筆・更新（md → docx）: `$paper-writing`
- 作業区切りの通常のコミット・プッシュ（PRなし）: `$aomori-git-publish`

## 作業区切りのコミット・プッシュ

- 「ここまでの作業内容要旨をコメントしてコミット・プッシュ」等の依頼では、PR作成が明示されていない限り `$aomori-git-publish` を使う。
- 通常の区切り作業ではplain Gitで現在ブランチへプッシュし、`main`からの新規ブランチ作成、`gh`の確認、PR作成を必須にしない。
- `gh`未導入はplain Gitによるコミット・プッシュの停止理由にしない。GitのHTTPS認証またはpushが実際に失敗した場合のみ、コミットを保持して原因を報告する。
- コミット前に対象差分と検証結果を確認し、対象ファイルを明示してステージする。
- コミットは簡潔な日本語件名と、変更理由・主要変更・検証結果をまとめた本文で構成する。
- PR作成またはブランチ公開まで明示された場合のみ、`$github:yeet` のPRフローを使用する。

## 成果物の安定出力

- 出力タグが未指定の場合は `YYYYMMDD_HHMMSS_<slug>` を既定とする（ASCII小文字+数字+アンダースコア）。
- 生成物は `outputs/` 配下に保存し、別パスが必要な場合のみユーザーに確認する。

## 実行後の内省

- AGENTS.mdやSKILL.mdを参照してタスクを完了した後、記述の修正・追記が望ましいか内省する。
- 改善が必要と判断した場合は提案のみ行い、自動で修正・追記しない。
