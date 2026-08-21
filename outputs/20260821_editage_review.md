# Editage校正結果の確認と反映判断

## 対象

- ジョブコード: `LDZPO_2`
- 証明書発行日: 2026-08-20
- 校正対象: 英文題名、英文抄録、Table 1、Figure 1 legendおよびFigure 1
- 原本保存先: `deliverables/05_manuscript/editage/20260820_LDZPO_2/`

## 原本ファイルとSHA-256

| ファイル | SHA-256 |
| --- | --- |
| `Certificate_of_editing-LDZPO_2_wuspmbuvct.pdf` | `1DA4412414FA3AEA77A019F3C4A40B3807ACC27E7C316F7BCEFD907C39D24579` |
| `Letter_from_the_Editor.docx` | `2A8A0EADAE2045F7833B98F4F0353FAAA9513CB572E9200D66501E11AD09D6A9` |
| `onki_short_report_ja_submission_comment.docx` | `B3E640A71EB6653CBF549FE95C8128CC33012A6242B9161D4F626416B782E9C3` |
| `onki_short_report_ja_submission.docx` | `3FDF297D5F95A7CBAF54F2D2CC72A44DE25D379C0AF4565713505B6FFD51E753` |

## 採用した校正

- 英文題名の `in the Bathroom` を、対象者ごとの浴室を示す `in Bathrooms` に変更した。
- 英文抄録の目的を先に提示し、`self-reported`、British Englishの日付表記と綴り、複合形容詞、`respectively`、結論の明確化を採用した。
- Table 1とFigure 1 legendの冠詞、単複、句読点、欠測説明および自然な語法を採用した。
- Table 1、Figure 1および最終DOCXの英語範囲表記にはen dashを用いることとした。

## 採用しなかった校正

- `bathroom heating dryer(s)` から `heating` を削除する提案は採用しなかった。前報および参照専用の基盤repoにある公的集計用語の翻訳資産で採用済みの公式英訳と、本研究系列内の用語一貫性を優先した。
- 英文抄録への機器背景説明の追加は、公式英訳を維持することと400語制限を優先し、採用しなかった。
- Editageへの謝辞追記は任意提案であり、校正証明書を別途提出するため採用しなかった。

## 実装上の扱い

- `paper.md` を正本とし、リポジトリ規約に従ってMarkdown内の範囲はASCIIハイフンで保持する。
- 投稿用DOCXの整形時、Table 1 XLSXの生成時、および英語Figure 1の描画時に、英語の範囲だけをen dashへ変換する。
- 和文本文、`paper_en.md`、解析対象、集計値および統計記述方針は変更しない。

## 検証記録

- 再生成run: `outputs/runs/20260821_131724_editage_revision/`
- English Abstract: 空白区切り380語、保守的な正規表現集計391語
- 解析回帰テスト: 10件成功
- markdownlint: 違反0件
- Table 1: 解析CSV・XLSXの全36行一致、A4縦1ページ
- 投稿用DOCX: A4、13ページ、変更履歴0件、コメント0件、Figure 1表示確認済み
