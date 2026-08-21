# 投稿用DOCX最終確認

## 対象

- 投稿用DOCX: `deliverables/05_manuscript/onki_short_report_ja_submission.docx`
- 正本Markdown: `paper.md`
- 前報参照: `../入浴統計/deliverables/FinalFile_Manuscript_Noshiro.docx`
- 投稿規定: 日本温泉気候物理医学会「雑誌投稿規定」（2026年8月5日改訂）
- 確認日: 2026年8月21日

## DOCX内の適合確認

| 確認項目 | 判定 | 確認結果 |
| --- | --- | --- |
| 表紙 | 適合 | 短報、和文題名、著者、所属、責任著者の氏名・所属・住所・電話・Fax・E-mail、利益相反なし、ランニングタイトルを記載した。 |
| 和文抄録 | 適合 | 見出し・キーワードを除いて799字で、800字以内。 |
| 和文キーワード | 適合 | 5個。 |
| 本文書式 | 適合 | A4、上下25 mm、左右30 mm、12 pt、約35字×32行を想定した行送り。ページ番号と行番号を付した。 |
| 観察研究の記載 | 適合 | 横断研究であること、対象、便宜抽出、調査期間、変数、欠測処理、集計方法、倫理承認、限界、一般化可能性の制約、資金源を記載した。 |
| 引用 | 適合 | 本文の引用番号を右肩の片括弧付き表記へ変更した。 |
| 引用文献 | 適合 | 6編で、短報の30編以内。引用順とし、雑誌名・年・巻・頁の順に統一し、学会誌名を「日温気物医誌」とした。 |
| 和文論文の英文抄録 | 適合 | 引用文献後の独立ページから開始し、英文題名、著者ローマ字名、英文所属、Abstract、5個のKeywords、Corresponding authorを配置した。 |
| 英文抄録語数 | 適合 | 空白区切り380語、保守的な正規表現集計391語で、400語以内。 |
| 図表説明 | 適合 | 英文抄録の後からFigure Legendを独立ページに置き、続いてTable、Figureを各独立ページに配置した。表題・説明は英文。 |
| 英文校閲 | 適合 | Editage校正反映済みの英文題名、英文抄録、Table 1、Figure 1 legendおよびFigure 1を使用した。 |
| DOCX技術監査 | 適合 | A4・13頁、変更履歴0件、コメント0件、表1点、図1点。埋込図はPNG 3046×1542 px。プレースホルダーは残っていない。 |

## 投稿時に別途必要な確認・添付

- 投稿依頼文を用意する。
- 学会所定の投稿承諾書へ署名・捺印する。
- 学会所定の倫理関係チェックリストを添付する。
- 横断研究としてSTROBEチェックリストとの対応を最終確認する。本文には主要項目を記載済みだが、チェックリスト自体は本DOCXに含めない。
- 図は投稿時に高品質な画像ファイルとして別添する。
- 著者の会員資格と、必要な場合の投稿料を確認する。

## 検証

- `python -m py_compile src/scripts/format_onki_manuscript_docx.py`: 成功
- `npx --yes markdownlint-cli2 paper.md`: 0件
- `python -m unittest discover -s tests -v`: 10件成功
- LibreOffice PDF変換による全13頁の目視確認: 表紙、和文抄録、英文抄録、Figure Legend、Table、Figureに欠落・重なりなし
- SHA-256: `693E2BD4CA8C707E571F87BDF8FE90C5973D14A4E32D3854F732D7ED0EB63519`

## 参照URL

- 学会誌について: https://www.onki.jp/magazine/about
- 雑誌投稿規定（2026年8月5日改訂）: https://www.onki.jp/wp/wp-content/uploads/85ec6e771266b5060ce709533c88013e-2.pdf
