# paper.md 英文セクション 校閲差し戻しメモ（GPT宛）

- 作成日: 2026-08-14
- 対象: `paper.md` の English Title / English Abstract / Tables (Table 1) / Figure Legends
- 前提: 和文（和文題名・和文抄録・本文）を正とし、英文はその対訳とする。研究内容・数値の妥当性は本メモの対象外（数値の内部整合は確認済みで矛盾なし）。
- 依頼事項: 下記 A〜C の指摘を反映した英文を再提出してください。D は著者判断が必要な確認事項です。末尾に「反映案（全文）」を付けたので、差分の参考にしてください。

---

## A. 文法・構文上の要修正（優先度：高）

### A-1. Objective 冒頭が懸垂分詞（dangling participle）
- 現行: `Using a convenience sample obtained from a questionnaire survey conducted in Goshogawara City, Aomori Prefecture, the primary objective of this study was to describe, ...`
- 問題: `Using ...` の意味上の主語が `the primary objective`（= 目的が標本を用いる）になっており非文法的。
- 修正案: `Using a convenience sample from a questionnaire survey conducted in Goshogawara City, Aomori Prefecture, we aimed primarily to describe, ...`

### A-2. Conclusions 末尾も同じ懸垂構文
- 現行: `When considering measures to address bathroom coldness in cold regions, understanding not only ... remains an issue for future investigation.`
- 問題: `When considering ...` の意味上の主語が動名詞 `understanding` になる。加えて `not only A but also B and C` の係り方（`the specific constraints ...` と `the heating configuration ...` が並列か否か）が曖昧。
- 修正案: 受動構文＋並列の明示に変更。`When measures to address bathroom coldness in cold regions are considered, it remains an issue for future investigation to examine not only the need for such equipment but also both the specific constraints that impede its installation or use and the heating configuration of the home.`

### A-3. Table 1 脚注：数字で文を開始している
- 現行: `... ; 9 of 154 returned questionnaires had missing data and are shown separately.`
- 問題: 英文では文頭に算用数字を置かない。また `questionnaires had missing data and are shown` は時制が混在。
- 修正案: `...; the nine of the 154 returned questionnaires with missing data are shown separately.`

### A-4. Table 1 脚注：主語と述語が対応していない
- 現行: `Other equipment used to heat the dressing room or bathroom, excluding the bathroom heating dryer and central heating, was a multiple-response item; ...`
- 問題: 「設備（equipment）＝設問項目（item）」となってしまう。複数回答なのは設問。
- 修正案: `Use of other equipment to heat the dressing room or bathroom, excluding the bathroom heating dryer and central heating, was assessed with a multiple-response item; ...`

### A-5. Figure 1 legend：時制混在・省略構文の破綻
- 現行: `The analysis includes 112 respondents who had not installed or did not use a bathroom heating dryer.`
- 問題: 他の記述（Abstract, Table脚注）は過去形で統一されているのに現在形。かつ `had not installed or did not use` は時制不一致で、Abstract の定義（「設置していない者」＋「設置しているが暖房として使用していない者」）と対応が取れていない。
- 修正案: `The analysis included 112 respondents who had not installed a bathroom heating dryer or who had installed one but did not use it for heating.`

### A-6. Abstract Methods：`and ... and` の連鎖で係りが読み取りにくい
- 現行: `... after excluding three with missing information on bathroom heating dryer installation and use and four non-users with missing reasons for non-use; ...`
- 問題: `installation and use` の `and` と除外群を並べる `and` が連続し、区切りが判別できない。`three with missing information` も名詞の省略（three respondents）が硬い。
- 修正案: 能動文に組み替える。`We excluded three respondents with missing data on the installation and use of a bathroom heating dryer and four non-users who did not report a reason for non-use, leaving 147 respondents for the primary analysis; of these, 112 non-users were included in the analysis of reasons.`

---

## B. 語法・明確性の改善（優先度：中）

| # | 箇所 | 現行 | 指摘 | 修正案 |
| --- | --- | --- | --- | --- |
| B-1 | Abstract Methods 末 | `Counts and percentages were described.` | `describe` の直訳。英語では数値は report / present する。 | `Counts and percentages are reported.` |
| B-2 | Abstract Methods | `were grouped post hoc and exploratorily as having "..."` | 副詞 `exploratorily` の連結が不自然。 | `were grouped into an exploratory post hoc category, "cost-related or housing/installation-related constraints."` |
| B-3 | Abstract Objective | `we described central heating use and concurrent use of bathroom heating dryers` | 和文「セントラル暖房との併用」の「〜との」が落ち、何と何の併用か不明。 | `we described the use of central heating and its concurrent use with a bathroom heating dryer` |
| B-4 | Abstract Methods | `difficulty installing the equipment because of the housing structure` | `the equipment` の先行詞が直前になく曖昧。 | `difficulty of installation because of the housing structure`（または `a bathroom heating dryer` と明示） |
| B-5 | Abstract Results | `28/145 respondents (19.3%), of whom 19/28 (67.9%)` | `of whom` の後に分母を再掲するのは冗長。 | `28/145 respondents (19.3%), of whom 19 (67.9%)` |
| B-6 | Abstract Methods | `The central heating analysis included 145 of the 154 respondents who answered that item.` | 定冠詞欠落のため「154人中145人だけを選んだ」とも読める。`that item` も不明確。 | `Analyses of central heating included the 145 of the 154 respondents who answered the central heating item.` |
| B-7 | Table 1 脚注 | `Percentages for all other characteristics use all 147 respondents ...` | 直前の文が過去形（`were calculated`）なのに現在形で時制が揺れる。 | `were calculated with all 147 respondents in the primary analysis as the denominator.` |
| B-8 | Table 1 脚注 | `calculated among 145 respondents with non-missing data` | 特定の145人なので定冠詞が必要。 | `among the 145 respondents with non-missing data` |
| B-9 | Table 1 脚注 | `Coldness scores ranged from 1 (very warm) to 7 (very cold)` | 「実測値の範囲がそうだった」とも読める。尺度の説明であることを明示。 | `Coldness was rated on a 7-point scale from 1 (very warm) to 7 (very cold)` |
| B-10 | Fig. 1 legend | `..., respectively, using the same scale and bar style.` | 分詞の主語が panels か図か曖昧。 | `...; both panels use the same axis scale and bar style.` |
| B-11 | Fig. 1 legend | `should not be summed to obtain the combined category` | 合算されるのはカテゴリではなく人数。 | `should not be summed to obtain the count for the combined category` |
| B-12 | Fig. 1 legend | `comprise reasons 2-5` / `2-3` / `4-5` | 図単独では reason 2〜5 の内容が読者に分からない（図表の自己完結性）。 | 括弧で内容を補う。例: `reasons 2-5 (electricity costs, installation cost, housing structure, and inability to carry out construction work in rented housing)` |
| B-13 | Fig. 1 legend | `"already warm enough; therefore, no bathroom heating dryer is needed."` | 質問紙の選択肢文としては `; therefore,` が不自然。原文「既に十分暖かいので必要がない」に沿った平叙文が自然。 | `corresponds to the response option "The bathroom is already warm enough, so a bathroom heating dryer is not needed."` |
| B-14 | Table 1 表題 | `in the analysis samples` | 複数形 `samples` は不自然。分母（n=147）も表題で示すのが慣例。 | `Table 1. Characteristics and use of heating equipment in the primary analysis sample (n = 147)` |
| B-15 | Table 1 行ラベル | `Stove` | 日本語の「ストーブ」は暖房器具だが、英語の `stove` は第一義が調理用コンロで誤読される。 | `Space heater (stove)` もしくは `Portable space heater` |
| B-16 | Table 1 行ラベル | `Winter bathing frequency` | 和文「冬季の**自宅**入浴頻度」の「自宅」が落ちている。 | `Frequency of bathing at home in winter` |
| B-17 | Table 1 行ラベル | `Used 24 hours` | 「24時間使用（＝終日連続運転）」の意が伝わりにくい。 | `Used 24 h/day (continuous)` |
| B-18 | Table 1 行ラベル | `Tenure` / `Floor heating other than central heating` | いずれも通じるが、`Housing tenure` / `Floor heating not part of the central heating system` の方が明確。 | 任意 |
| B-19 | Abstract 全体 | `the primary objective of this study was` と `we described` / `We conducted` | 非人称と一人称が混在。 | 一人称（we）に統一 |
| B-20 | Fig. 1 legend 末 | `between-group differences and p values were not calculated` | 「差を計算しなかった」より「検定を行わなかった」が実態に即す。 | `no statistical tests of between-group differences were performed` |

---

## C. 表記統一・体裁（優先度：中〜低）

- **C-1 引用符**: Abstract は直線引用符 `"..."`、Figure legend は曲線引用符 `“...”` で不統一。いずれかに統一（投稿規定に指定がなければ直線引用符で統一）。
- **C-2 群名の表記ゆれ**: Abstract `score 5-7 group` / Table 1 `Score 5-7` / Figure legend `coldness 1-4 group` の3通りが混在。`coldness score 5-7 group`（表中は `Coldness score 5-7`）に統一を推奨。
- **C-3 図の呼称**: 英文見出しは `Figure 1`、和文本文中の参照は `Fig. 1`。投稿規定に合わせて一方に統一（和文本文が `Fig. 1` なので `Fig. 1` 推奨）。
- **C-4 `n=50` の空白**: `n = 50`, `n = 62` と前後空白を入れるのが一般的。
- **C-5 `p values`**: 統計記号は斜体（`*P* values` または `*p* values`）。投稿規定の大文字・小文字指定に従う。
- **C-6 数値範囲のダッシュ**: `1-4`, `5-7`, `18-49 years`, `January-February`, `4-6 times/week` などがすべて ASCII ハイフン。英文組版では en dash（–）が標準。和文と共用のファイルなので一括変換の可否は要判断だが、英文セクションのみ en dash に揃えるのが望ましい。
- **C-7 Missing 行の表記**: Central heating の `Missing | 9`（%なし）と Other equipment の `Missing | 8 (5.4)`、Tenure の `Missing | 1 (0.7)` で扱いが異なる。分母が異なるための意図的な差なので、脚注でその旨が読み取れるか再確認（現状の脚注でおおむね説明されている）。

---

## D. 著者確認が必要な事項（和文との整合）

- **D-1 英文題名の「温冷感」**: 和文題名は「浴室の**温冷感**」だが、英文題名は `Perceived Bathroom Coldness`（＝寒さ体感）。本文の変数名は和文で「寒さ体感」なので、題名だけ用語が異なるのは和文側の設計どおりとも読める。
  - 案a（和文題名に忠実）: `... and Perceived Thermal Sensation in the Bathroom in Goshogawara City, Aomori Prefecture`
  - 案b（英文内の用語を統一）: 現行の `Perceived Bathroom Coldness` を維持し、和文題名を「寒さ体感」に合わせる
  - → 和文を正とする方針であれば **案a** を推奨。
- **D-2 責任著者プレースホルダの不一致**: 和文は「氏名、所属、住所、電子メールアドレス」、英文は `[Enter name, affiliation, postal address, telephone number, and email address]` で `telephone number` が英文のみに存在。投稿規定に電話番号が必要かを確認し、和英を揃える。
- **D-3 `bathroom heating dryer` の訳語**: 前報［文献3］で用いた英訳との一致を確認。一般的な代替は `bathroom heating and drying unit` / `bathroom heater-dryer`。既発表と揃えるのが最優先で、本稿内では現行表記で統一されている（問題なし）。
- **D-4 キーワード**: 和英の対応（浴室暖房乾燥機／セントラル暖房／横断研究／寒冷地／青森県）は一致。区切り記号（`;` かカンマか）と `cold region` の単複は投稿規定に従う。

---

## E. 確認したうえで修正不要と判断した点

- 題名のタイトルケース（`Non-installation`, `Non-use` の接頭辞後を小文字にする処理）は Chicago 方式に適合しており妥当。
- Abstract の数値はすべて和文抄録・本文と一致（51/62=82.3%、15/50=30.0%、28/145=19.3%、19/28=67.9%）。Table 1 の各区分の合計・百分率も147／145の分母と整合。
- `a priori` / `post hoc` はいずれも立体（非斜体）で統一されており可。
- `dressing room` / `dressing-room coldness`（複合修飾語のハイフン）は正しく使い分けられている。
- 構造化抄録の見出し `Objective / Methods / Results / Conclusions` は和文（目的／方法／結果／結論）と対応。

---

## F. 反映案（全文・差し替え用）

> 以下は A・B・C の指摘をすべて反映した案。D-1 は案a（`Perceived Thermal Sensation in the Bathroom`）を採用した版。en dash（–）を使用。

### English Title

Reasons for Non-installation or Non-use of Bathroom Heating Dryers and Perceived Thermal Sensation in the Bathroom in Goshogawara City, Aomori Prefecture

### English Abstract

Objective: Using a convenience sample from a questionnaire survey conducted in Goshogawara City, Aomori Prefecture, we aimed primarily to describe, according to perceived bathroom coldness in winter, the reasons reported by respondents who had not installed a bathroom heating dryer or who had installed one but did not use it for heating (hereafter, non-users). Secondarily, we described the use of central heating and its concurrent use with a bathroom heating dryer. Methods: We conducted an anonymous cross-sectional questionnaire survey in Goshogawara City from March 11 to April 30, 2026. Of the 190 questionnaires distributed, 154 were returned. We excluded three respondents with missing data on the installation and use of a bathroom heating dryer and four non-users who did not report a reason for non-use, leaving 147 respondents for the primary analysis; of these, 112 non-users were included in the analysis of reasons. Analyses of central heating included the 145 of the 154 respondents who answered the central heating item. Perceived bathroom coldness in winter (the coldest period, January–February) was rated on a 7-point scale from 1 (very warm) to 7 (very cold) and was categorized a priori into scores of 1–4 and 5–7. Reasons for non-installation or non-use were collected as multiple responses; respondents who selected any of the following reasons—concern about electricity costs, high installation cost, difficulty of installation because of the housing structure, or inability to carry out construction work in rented housing—were grouped into an exploratory post hoc category, "cost-related or housing/installation-related constraints." Counts and percentages are reported. Results: Of the 112 non-users included in the analysis of reasons, 62 were in the coldness score 5–7 group and 50 were in the coldness score 1–4 group. Cost-related or housing/installation-related constraints were selected by 51/62 respondents (82.3%) in the score 5–7 group and by 15/50 (30.0%) in the score 1–4 group. Central heating was used by 28/145 respondents (19.3%), of whom 19 (67.9%) also used a bathroom heating dryer for heating. Conclusions: In this convenience sample from Goshogawara City, some non-users of bathroom heating dryers who perceived their bathrooms as cold reported cost-related or housing/installation-related constraints as reasons for non-installation or non-use. When measures to address bathroom coldness in cold regions are considered, it remains an issue for future investigation to examine not only the need for such equipment but also both the specific constraints that impede its installation or use and the heating configuration of the home.

### Table 1（表題・行ラベル・脚注のみ）

**Table 1. Characteristics and use of heating equipment in the primary analysis sample (n = 147)**

変更する行ラベル:
- `Winter bathing frequency` → `Frequency of bathing at home in winter`
- `Stove` → `Space heater (stove)`
- `Used 24 hours` → `Used 24 h/day (continuous)`
- `Tenure` → `Housing tenure`
- `Floor heating other than central heating` → `Floor heating not part of the central heating system`
- `Perceived bathroom coldness | Score 5-7` → `Perceived bathroom coldness | Coldness score 5–7`（脱衣所行も同様）
- 年齢・築年・入浴頻度の範囲表記はすべて en dash（`18–49 years`, `4–6 times/week` など）

脚注:

Values are n (%). Percentages for central heating use were calculated among the 145 respondents with non-missing data; the nine of the 154 returned questionnaires with missing data are shown separately. Percentages for all other characteristics were calculated with all 147 respondents in the primary analysis as the denominator. Use of other equipment to heat the dressing room or bathroom, excluding the bathroom heating dryer and central heating, was assessed with a multiple-response item; therefore, percentages do not sum to 100%, and missing responses are shown separately. Coldness was rated on a 7-point scale from 1 (very warm) to 7 (very cold); only the coldness score 5–7 group is shown for each coldness item.

### Figure Legend

**Fig. 1. Reasons for non-installation or non-use of a bathroom heating dryer, by perceived bathroom coldness**

The analysis included 112 respondents who had not installed a bathroom heating dryer or who had installed one but did not use it for heating. The left and right panels show the coldness score 1–4 group (n = 50) and the coldness score 5–7 group (n = 62), respectively; both panels use the same axis scale and bar style. Reasons were collected as multiple responses; therefore, percentages do not sum to 100%. "No need" (reason 1) corresponds to the response option "The bathroom is already warm enough, so a bathroom heating dryer is not needed." Cost-related or housing/installation-related constraints comprise reasons 2–5 (electricity costs, installation cost, housing structure, and inability to carry out construction work in rented housing); cost-related reasons comprise reasons 2 and 3; and housing/installation-related reasons comprise reasons 4 and 5. The cost-related and housing/installation-related categories were not mutually exclusive; therefore, their counts should not be summed to obtain the count for the combined category. Bars show the observed n/N (%) within each group. Confidence intervals are not shown, and no statistical tests of between-group differences were performed.

---

## G. 反映時の注意

- 上記の反映案は **英文セクションのみ** の変更案であり、和文本文・和文抄録の内容変更は含まない。
- D-1 を案b（現行 `Perceived Bathroom Coldness` を維持）とする場合、F の題名のみ差し替えれば他は流用可。
- 図中のラベル（PNG画像 `deliverables/figures/onki_short_report_figure1_reasons_by_bathroom_coldness_en.png`）に凡例と同じ用語が焼き込まれている場合、C-2 の用語統一は図の再作成が必要になる。本メモでは画像内テキストは未確認。
