# 英文レビュー対応結果と現在稿の再確認依頼

- 作成日: 2026-08-17
- 対象: `paper.md` の English Title、English Abstract、Table 1、Figure legend
- 元レビュー: `outputs/20260814_english_review_for_gpt.md`
- 現在稿: commit `1e743fbaebf2bfc8cd0958f916c21a0a276af59b`
- 基本方針: 和文題名・和文抄録・和文本文を正本とし、英文は内容、限定、断定・推定の強さを一対一で対応させる

## Claudeへの再確認依頼

前回レビューの各指摘について、文法上の問題は原則として解消し、語法・表記については和文との対応、投稿先の体裁、文献3および既存翻訳コーパス、repo固有のMarkdown規約を踏まえて採否を判断した。

その後、修正後の英文を和文と文単位で再点検したところ、Abstract末文の `should examine` が、和文の「今後の検討課題となる」よりも規範的で強いと判断した。このため、現在稿では将来研究への勧告ではなく、未解決事項の提示となるよう再調整している。

以下について、現在稿を改めて確認してほしい。

1. 文法・構文上の問題が残っていないか。
2. 和文より断定、推定、勧告の強さが増している箇所がないか。
3. `perceived thermal sensation` と `perceived bathroom coldness` の概念上の区別が明瞭か。
4. Table 1とFigure legendが単独で理解でき、分母、複数回答、派生群の説明に誤解がないか。
5. 下記の「意図的に不採用または別解とした項目」について、なお英文上の重大な問題があるか。

## 対応判断の前提

### 和文正本

英文の内容判断では、現在の和文題名、和文抄録、方法、結果を正本とした。英文だけに残っていた旧情報や、和文にない推定・追加解釈は採用しない方針とした。

### 用語資産

文献3の英文原稿と「入浴統計」repoの翻訳資産を参照した。特に、`translation/glossary.csv` では「浴室暖房乾燥機」に `bathroom heating dryer` が採用されているため、本稿でもこの表現を維持した。

### 温冷感と寒さ解析群

質問項目は、1 `very warm`、4 中立、7 `very cold` の双極7件法である。このため、測定概念全体は `perceived thermal sensation`、その回答から作成した解析群は `bathroom coldness score 1-4 group` と `bathroom coldness score 5-7 group` とした。

題名と尺度説明で `thermal sensation`、群別解析で `coldness score` を用いることは用語不統一ではなく、測定概念と派生解析変数の区別である。

### 表記規約

本repoの `docs/rules/markdown_generation_rules.md` は、期間・数値範囲にASCIIハイフンを使用するよう定めている。このため、英文組版上はen dashが一般的であることを承知した上で、`1-4`、`5-7`、`January-February` などはASCIIハイフンを維持した。

## A 文法・構文上の指摘への対応

| ID | 判断 | 現在の対応と理由 |
| --- | --- | --- |
| A-1 | 趣旨採用 | 懸垂分詞を解消し、現在は `We used a convenience sample ... primarily to describe ...` とした。Claude案の逐語採用ではないが、標本を使用する主体を `we` として文法上の問題を解消した。さらに「理由の内訳」に対応させるため、現在は `describe the distribution of reasons` としている。 |
| A-2 | 趣旨採用後に再調整 | `When measures ... are considered` の受動節により懸垂構文を解消した。ただし、初回反映時の `should examine` は和文より強い勧告になるため、現在は `remains a matter for future investigation` に変更した。並列対象も、設備の必要性、具体的制約、住宅の暖房構成の3点が読めるようにした。 |
| A-3 | 代替表現で採用 | 現在は `For central heating use, 145 of the 154 returned questionnaires had non-missing data; the nine missing responses are shown separately.` とした。数字による文開始と、questionnaire自体を「shown」とする不自然さを同時に解消した。 |
| A-4 | 採用 | `Use of other equipment ... was assessed with a multiple-response item` とし、複数回答なのは設備ではなく設問であることを明確にした。 |
| A-5 | 採用 | `The analysis included 112 respondents who had not installed ... or who had installed one but did not use it for heating.` とし、時制と不使用者の定義をAbstractに合わせた。 |
| A-6 | 採用後に明確化 | 能動文 `We excluded three respondents ... and four non-users ...` を採用した。その後、`installation and use` が別々の欠測項目にも読めるため、現在は `bathroom heating dryer installation/use status` とした。 |

## B 語法・明確性の指摘への対応

| ID | 判断 | 現在の対応と理由 |
| --- | --- | --- |
| B-1 | 採用 | `Counts and percentages are reported.` とした。 |
| B-2 | 採用 | `we created an exploratory post hoc category` とし、不自然な `exploratorily` を除いた。`After data collection` を併記し、和文の「回答回収後に探索的に」と対応させた。 |
| B-3 | 採用 | `central heating use and its concurrent use with a bathroom heating dryer` とし、併用対象を明示した。 |
| B-4 | 採用 | `difficulty of installation because of housing structure` とし、先行詞が不明な `the equipment` を除いた。 |
| B-5 | 採用 | `28/145 respondents (19.3%), of whom 19 (67.9%)` とし、冗長な分母の再掲を除いた。 |
| B-6 | 代替表現で採用 | `Central heating analyses included 145 of 154 respondents with non-missing data on that item.` とした。直前の主語がcentral heating analysesであるため、`that item` はcentral heating itemを指す。Claude案の `the 145 of the 154` より簡潔な形を選択した。 |
| B-7 | 採用 | `Percentages for all other characteristics were calculated with all 147 respondents ... as the denominator.` とした。 |
| B-8 | 代替表現で採用 | Central heatingについては、145件の非欠測と9件の欠測を1文で明示した。 |
| B-9 | 趣旨採用 | 実測範囲ではなく尺度であることを明記した。測定概念を反映し、`Perceived thermal sensation ... was rated on a 7-point scale ...; ... only the derived coldness score 5-7 group is shown.` とした。 |
| B-10 | 採用 | `both panels use the same axis scale and bar style` とした。 |
| B-11 | 趣旨採用後に再調整 | 初回は `count for the combined category` を採用した。その後、`should not be summed` も規範表現であるため、現在は `the sum of their counts does not equal the count for the combined category` という算術上の事実記述にした。 |
| B-12 | 採用 | reasons 2-5、2-3、4-5の内容をlegend内に記載し、図単独で理解できるようにした。 |
| B-13 | 採用 | `The bathroom is already warm enough, so ... is not needed.` とした。 |
| B-14 | 採用 | `Table 1. Characteristics and use of heating equipment in the primary analysis sample (n = 147)` とした。Central heatingの分母145と欠測9は脚注で別途説明した。 |
| B-15 | 採用 | `Space heater (stove)` を採用し、調理器具との誤読を避けつつ原選択肢との対応も残した。 |
| B-16 | 採用 | `Frequency of bathing at home in winter` とした。 |
| B-17 | 採用 | `Used 24 h/day (continuous)` とした。 |
| B-18 | 採用 | `Housing tenure` と `Floor heating not part of the central heating system` を採用した。 |
| B-19 | 採用 | ObjectiveとMethodsの研究行為は `we` に統一した。ResultsとConclusionsは観察事実を主語とする英文としている。 |
| B-20 | 採用 | `no statistical tests of between-group differences were performed` とした。 |

## C 表記統一・体裁への対応

| ID | 判断 | 現在の対応と理由 |
| --- | --- | --- |
| C-1 | 採用 | Markdown原稿では直線引用符に統一した。DOCX生成時には文書処理系により表示上の引用符が変換される場合がある。 |
| C-2 | 採用 | Abstractとlegendは `bathroom coldness score 1-4 group` / `5-7 group`、Table 1は `Coldness score 5-7` に統一した。 |
| C-3 | 一部採用 | 正式なlegendと和文本文中の参照は `Fig. 1` とした。`## Figures` 配下の `### Figure 1` は画像配置用の構造見出しとして残している。 |
| C-4 | 採用 | `n = 50`、`n = 62` とした。英語図内も同じ空白規則に更新した。 |
| C-5 | 対応不要 | `p values` を整形するのではなく、実際の解析に合わせて `no statistical tests ... were performed` としたため、該当する統計記号がなくなった。 |
| C-6 | 意図的に不採用 | repo規約に従い、数値範囲はASCIIハイフンを維持した。 |
| C-7 | 確認済み | Central heatingは回収154件中の非欠測145件を分母とし、欠測9件を割合なしで示す。他項目は主要解析147人を分母とするため、Missing行の表示差は意図的であり、脚注で説明した。 |

## D 著者判断事項への対応

| ID | 判断 | 現在の対応と理由 |
| --- | --- | --- |
| D-1 | 案aを採用 | English Titleは `Perceived Thermal Sensation in the Bathroom` とした。尺度全体は暖かい-中立-寒いを含むため `thermal sensation`、解析群は寒さ方向の派生分類であるため `bathroom coldness score` を使用する。Methodsで両者の関係を明示した。 |
| D-2 | 採用 | 英文の責任著者欄からtelephone numberを除き、和文の氏名、所属、住所、電子メールアドレスと対応させた。 |
| D-3 | 現行維持 | 文献3と既存用語集に合わせて `bathroom heating dryer` を維持した。一般的な代替語より、同一研究系列内の一貫性を優先した。 |
| D-4 | 変更不要 | 5つの和文キーワードと英語キーワードは対応している。英語はセミコロン区切りを維持した。 |

## E 修正不要との指摘

前回レビューで修正不要とされた次の事項は維持した。

- English Titleのタイトルケース。
- 147、112、145、51/62、15/50、28/145、19/28などの人数、分母、割合。
- `a priori` と `post hoc` の扱い。
- `dressing room` と複合修飾語 `dressing-room coldness` の使い分け。
- Objective、Methods、Results、Conclusionsの構造。

## 初回対応後のニュアンス再調整

### Abstract末文

初回のClaude対応では、懸垂構文と並列関係を解消する過程で、次の勧告表現を使用した。

> Future investigations of measures to address bathroom coldness in cold regions should examine three issues: ...

しかし、和文は「今後の検討課題となる」として断定を丸めており、`should examine` は英文だけを読んだ場合に将来研究への勧告として一段強い。このため、現在稿では次のようにした。

> When measures to address bathroom coldness in cold regions are considered, understanding the specific constraints that impede equipment installation or use and the heating configuration of the home, in addition to the need for such equipment, remains a matter for future investigation.

この表現では、`remains a matter for future investigation` が「今後の検討課題となる」に対応し、研究実施を要求せず、未解決事項として提示する。

### 理由の内訳

和文の「理由の内訳」をより正確に反映するため、`describe reasons` から `describe the distribution of reasons` に変更した。

### 設置・使用状況

`installation and use` は設置と使用という2変数にも読めるため、質問票上の1つの状態項目であることを示す `installation/use status` に変更した。

### Figure legendの規範表現

`their counts should not be summed` は読者への指示としては正しいが、現在稿ではより客観的な `the sum of their counts does not equal ...` に変更した。

## 現在のEnglish Title

Reasons for Non-installation or Non-use of Bathroom Heating Dryers and Perceived Thermal Sensation in the Bathroom in Goshogawara City, Aomori Prefecture

## 現在のEnglish Abstract

Objective: We used a convenience sample from a questionnaire survey in Goshogawara City, Aomori Prefecture, primarily to describe the distribution of reasons reported by respondents who had not installed a bathroom heating dryer or had installed one but did not use it for heating (hereafter, non-users), stratified by perceived bathroom coldness in winter. Secondarily, we described central heating use and its concurrent use with a bathroom heating dryer. Methods: We conducted an anonymous cross-sectional questionnaire survey in Goshogawara City from March 11 to April 30, 2026. Of 190 distributed questionnaires, 154 were returned. We excluded three respondents with missing data on bathroom heating dryer installation/use status and four non-users who did not report a reason for non-use, leaving 147 respondents for the primary analysis; 112 non-users were included in the analysis of reasons. Central heating analyses included 145 of 154 respondents with non-missing data on that item. Perceived thermal sensation in the bathroom during the coldest winter period (January-February) was rated on a 7-point scale from 1 (very warm) to 7 (very cold). Ratings were classified a priori into bathroom coldness score groups of 1-4 and 5-7. Reasons for non-installation or non-use were collected as multiple responses. After data collection, we created an exploratory post hoc category, "cost-related or housing/installation-related constraints," for respondents selecting at least one of four reasons: concern about electricity costs, high installation cost, difficulty of installation because of housing structure, or inability to undertake construction work in rented housing. Counts and percentages are reported. Results: Among 112 non-users, 62 were in the bathroom coldness score 5-7 group and 50 were in the bathroom coldness score 1-4 group. Cost-related or housing/installation-related constraints were selected by 51/62 respondents (82.3%) in the bathroom coldness score 5-7 group and by 15/50 (30.0%) in the bathroom coldness score 1-4 group. Central heating was used by 28/145 respondents (19.3%), of whom 19 (67.9%) also used a bathroom heating dryer for heating. Conclusions: In this convenience sample from Goshogawara City, some non-users of bathroom heating dryers who perceived their bathrooms as cold reported cost-related or housing/installation-related constraints as reasons for non-installation or non-use. When measures to address bathroom coldness in cold regions are considered, understanding the specific constraints that impede equipment installation or use and the heating configuration of the home, in addition to the need for such equipment, remains a matter for future investigation.

English keywords: bathroom heating dryer; central heating; cross-sectional study; cold region; Aomori Prefecture

## 現在のTable 1関連表現

### Table 1表題

Table 1. Characteristics and use of heating equipment in the primary analysis sample (n = 147)

### 主要な更新済みラベル

- Housing tenure
- Frequency of bathing at home in winter
- Used 24 h/day (continuous)
- Space heater (stove)
- Floor heating not part of the central heating system
- Perceived bathroom coldness / Coldness score 5-7
- Perceived dressing-room coldness / Coldness score 5-7

### Table 1脚注

Values are n (%). For central heating use, 145 of the 154 returned questionnaires had non-missing data; the nine missing responses are shown separately. Percentages for all other characteristics were calculated with all 147 respondents in the primary analysis as the denominator. Use of other equipment to heat the dressing room or bathroom, excluding the bathroom heating dryer and central heating, was assessed with a multiple-response item; therefore, percentages do not sum to 100%, and missing responses are shown separately. Perceived thermal sensation in the bathroom and dressing room was rated on a 7-point scale from 1 (very warm) to 7 (very cold); for each room, only the derived coldness score 5-7 group is shown.

## 現在のFigure legend

### Fig. 1 legend

Fig. 1. Reasons for non-installation or non-use of a bathroom heating dryer, by perceived bathroom coldness

The analysis included 112 respondents who had not installed a bathroom heating dryer or who had installed one but did not use it for heating. The left and right panels show the bathroom coldness score 1-4 group (n = 50) and the bathroom coldness score 5-7 group (n = 62), respectively; both panels use the same axis scale and bar style. Reasons were collected as multiple responses; therefore, percentages do not sum to 100%. "No need" (reason 1) corresponds to the response option "The bathroom is already warm enough, so a bathroom heating dryer is not needed." Cost-related or housing/installation-related constraints comprise reasons 2-5 (electricity costs, installation cost, housing structure, and inability to carry out construction work in rented housing); cost-related reasons comprise reasons 2 and 3; and housing/installation-related reasons comprise reasons 4 and 5. Because the cost-related and housing/installation-related categories were not mutually exclusive, the sum of their counts does not equal the count for the combined category. Bars show the observed n/N (%) within each group. Confidence intervals are not shown, and no statistical tests of between-group differences were performed.

## 検証記録

- English Abstract: 396 words
- 解析回帰テスト: 10件成功
- markdownlint: 違反0件
- Table 1: 解析CSV、`paper.md`、xlsxの全36行が一致
- 主要数値: 147、112、145、28、19、51/62、15/50を維持
- DOCX: 13ページ。English Title、Abstract、Table 1、Figure legend、Figure 1を表示確認
- 和文本文、引用文献、解析ロジック、「入浴統計」repo: 変更なし

## 変更履歴

- `3596e51`: 英語題名・抄録・Table 1を和文正本に同期
- `faf2db5`: Claude英文レビューを反映し、用語、Table 1、Figure legend、英語Figure 1を更新
- `1e743fb`: 和文との断定・推定ニュアンスを再点検し、Abstract末文とFigure legendの規範表現を調整
