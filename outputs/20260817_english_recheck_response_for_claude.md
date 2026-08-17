# 英文再点検（第2巡）への対応結果

- 作成日: 2026-08-17
- 対象: `paper.md` の English Abstract、Table 1脚注、Fig. 1 legend
- 再点検メモ: `outputs/20260817_english_recheck_for_gpt.md`
- 基本方針: 和文正本との一対一対応を維持し、英文単独で生じる構文・分母・尺度定義の曖昧性だけを解消する

## 対応結果

| ID | 判断 | 対応と理由 |
| --- | --- | --- |
| R-1 | 採用 | 両群の解析値を再確認すると、費用系と住宅・設置制約系の重複は1-4群、5-7群とも各1人であり、現行の算術記述自体は正しかった。ただし、カテゴリが非排他的であることだけから不一致を必然視しないよう、`can exceed`を用いた一般的な説明へ変更した。 |
| R-2 | 採用 | 7件法の回答を解析上`bathroom coldness scores`と呼ぶことをMethods内で明示し、別変数との誤読を避けた。 |
| R-3 | 採用 | Table 1脚注で、浴室・脱衣所のthermal-sensation ratingsを対応するcoldness scoresとして扱ったことを明記した。実質的な数値変換を示唆する`derived`は使用しなかった。 |
| R-4 | 採用 | `Of the 154 respondents, central heating use was analyzed for 145 with non-missing data.`とし、145人と154人の関係および`that item`の指示先の曖昧性を解消した。 |
| R-5 | 採用 | セントラル暖房の欠測9人は割合なしの別行、その他暖房設備の欠測8人は147人を分母とする割合付き別行であることを個別に明記した。 |
| R-6 | 採用 | `both`を追加し、「具体的制約」と「住宅の暖房構成」が並列対象であることを明示した。`remains a matter for future investigation`は維持し、和文より勧告を強めていない。 |
| R-7 | 採用 | 同一選択肢の訳を`inability to undertake construction work in rented housing`に統一した。英語Figure 1の図中にはこの文章表現がないため画像変更は不要だった。 |
| R-8 | 不採用 | コロン直後に4理由を列挙しており、`following`がなくても関係は明瞭である。400語上限への余裕を優先した。 |
| R-9 | 採用 | Fig. 1 legendで`N`を対応する浴室寒さスコア群の回答者数と定義した。 |
| R-10 | 不採用 | 本稿は和文投稿である。2026年8月5日改訂の和文投稿規定10（8）が和文論文の英文抄録に求めるのは、英文題目、著者ローマ字名、英文所属、Abstract、Keywords、Corresponding Authorであり、英語の論文種別とrunning titleは含まれない。論文種別は投稿依頼文に記載する。英文原稿向け投稿規定のshort running title要件は本稿へ適用しなかった。 |
| R-11 | 不採用 | キーワードの単数形`cold region`は一般的な見出し語として維持した。 |

## R-1の解析値確認

Fig. 1の表示値から、費用系と住宅・設置制約系の重複人数を包含排除で確認した。

| 浴室寒さスコア群 | 費用系 | 住宅・設置制約系 | 統合カテゴリ | 重複 |
| --- | ---: | ---: | ---: | ---: |
| 1-4 | 10 | 6 | 15 | 1 |
| 5-7 | 31 | 21 | 51 | 1 |

したがって、旧文の`does not equal`は両群とも観測値として成立していた。一方、legendでは今回の標本における算術結果よりも複数回答分類の読み方を説明することを優先し、可能性を表す`can exceed`へ変更した。

## 修正後の主要表現

### English Abstract Methods

> Of the 154 respondents, central heating use was analyzed for 145 with non-missing data. Perceived thermal sensation in the bathroom during the coldest winter period (January-February) was rated on a 7-point scale from 1 (very warm) to 7 (very cold). These ratings (hereafter, bathroom coldness scores) were classified a priori into groups of 1-4 and 5-7.

### English Abstract Conclusions

> When measures to address bathroom coldness in cold regions are considered, understanding both the specific constraints that impede equipment installation or use and the heating configuration of the home, in addition to the need for such equipment, remains a matter for future investigation.

### Fig. 1 legend

> The categories shown are not mutually exclusive; accordingly, the sum of the counts for the cost-related and housing/installation-related categories can exceed the count for the combined category. Bars show n/N (%), where N is the number of respondents in the corresponding bathroom coldness score group.

## 語数と変更範囲

- English Abstract: 空白区切り395語
- English Abstract: 小数点を語境界として分割する保守的な正規表現集計399語
- 上限: 400 words以内
- 変更なし: 和文、English Title、English keywords、Table 1の数値、解析ロジック、引用文献、英語Figure 1画像

## 検証結果

- 解析回帰テスト: 10件成功
- markdownlint: 違反0件
- Table 1: 解析CSV、`paper.md`、xlsxの全36行が一致
- DOCX: 13ページ。English Abstract、6列のTable 1、Fig. 1 legend、Figure 1の配置を表示確認
- DOCX: `<30 years`と`≥30 years`が正しく表示されることを確認
- xlsx: 脚注、欠測行、印刷範囲、1ページ出力を確認
- 実行記録: `outputs/runs/20260817_141039_english_recheck_revision/`

## 投稿規定の判断根拠

- 和文投稿規定: <https://www.onki.jp/wp/wp-content/uploads/85ec6e771266b5060ce709533c88013e-2.pdf>
- 英文投稿規定: <https://www.onki.jp/wp/wp-content/uploads/48b30fcc4fe66bafceaa08c21ecdfca2.pdf>
