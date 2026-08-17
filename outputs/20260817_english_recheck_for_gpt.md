# 英文再点検（第2巡）指摘メモ

- 作成日: 2026-08-17
- 対象: `paper.md` の English Title、English Abstract、Table 1、Fig. 1 legend
- 参照: `outputs/20260817_english_review_response_for_claude.md`（Codexの対応判断メモ）、`outputs/20260814_english_review_for_gpt.md`（第1巡レビュー）
- 参照コンテキスト: 現在の `paper.md` と上記対応メモのみ
- 前提: 前回メモの基本方針（和文題名・和文抄録・和文本文を正本とし、英文は内容と断定・推定の強さを一対一で対応させる）をそのまま引き継ぐ

## 総評

第1巡で指摘した文法・構文上の問題は解消済みと確認した。`should` を含む規範表現も除去され、Abstract末文は和文「今後の検討課題となる」と強さが対応している。対応判断の前提（和文正本、用語資産、温冷感と寒さ解析群の区別、ASCIIハイフン規約）はいずれも妥当であり、意図的不採用とされた項目に英文上の重大な問題は残っていない。

一方、今回の照合で **1件の内容上の要修正**（Fig. 1 legendの重複説明が、原稿内で確認できる範囲を超えて断定している）と、**5件の推奨修正**（概念の橋渡し、分母・欠測記述の語義、係り受けの曖昧性、語句不統一）を検出した。いずれも和文に新たな主張を追加せず、英文側の精度を和文に合わせる方向の修正である。

数値は全件再検算した。Table 1の全カテゴリの人数・割合（147分母および145分母）、Abstractの 147 / 112 / 145 / 28 / 19 / 51/62 / 15/50、和文本文の112分母の各割合はすべて整合しており、修正不要である。

## 優先度別の指摘

### R-1 必須: Fig. 1 legendの重複説明が検証範囲を超えて断定している

- 該当: [paper.md:149](paper.md#L149)
- 現行

  > Because the cost-related and housing/installation-related categories were not mutually exclusive, the sum of their counts does not equal the count for the combined category.

- 問題: `does not equal` は「両サブカテゴリを重複選択した回答者が実在する」という経験的主張である。この命題は、費用系と住宅・設置制約系の重複が0人であれば偽になる。原稿中で重複が確認できるのは浴室寒さ5-7群のみ（[paper.md:76](paper.md#L76) の「費用系31人、住宅・設置制約系21人、1人が両方」→ 31+21-1=51）であり、legendが説明する2パネルのうち1-4群については重複人数が原稿のどこにも示されていない。よって、現行文は左パネルについて未検証の断定になっている。
  第1巡の `should not be summed` を規範表現として避けた判断自体は妥当だが、置き換え先が逆方向に踏み込んでいる。
- 提案（可能性の記述に戻し、かつ和文「複数回答であるため…重複を許容した」（[paper.md:36](paper.md#L36)）に対応させる）

  > The categories shown are not mutually exclusive; accordingly, the sum of the counts for the cost-related and housing/installation-related categories can exceed the count for the combined category.

- 補足利得: 主語を「図に示した分類全体」に一般化することで、「不要」と制約系分類の合算も同時に抑止できる。和文本文（[paper.md:36](paper.md#L36), [paper.md:80](paper.md#L80)）は「不要」と「障壁あり」の非排他性にも言及しているが、現行legendは費用系と住宅・設置制約系の関係しか述べていない。
- 副次的解消: 現行の `were not mutually exclusive`（過去）と `does not equal`（現在）の時制混在も、提案文（`are` / `can exceed`）で解消する。
- 語数: +3語程度（legendは語数制限が緩いため影響は小さい）

### R-2 推奨: Abstractで thermal sensation から coldness score への橋渡しがない

- 該当: [paper.md:113](paper.md#L113) Methods
- 現行

  > Perceived thermal sensation in the bathroom during the coldest winter period (January-February) was rated on a 7-point scale from 1 (very warm) to 7 (very cold). Ratings were classified a priori into bathroom coldness score groups of 1-4 and 5-7.

- 問題: 前回メモの前提「測定概念＝`perceived thermal sensation`、派生解析群＝`bathroom coldness score` 群」という整理は妥当だが、Abstract本文にはその対応関係を述べる語がない。読者は `bathroom coldness score` を、7件法とは別に作成された第2の変数と読む余地がある。これは前回メモの確認依頼3に直接対応する箇所である。
- 提案（最小の語数増で定義を明示）

  > Ratings (hereafter, bathroom coldness score) were classified a priori into groups of 1-4 and 5-7.

- 備考: `hereafter` はObjectiveの `(hereafter, non-users)` と同じ体裁であり、新規の表記様式を持ち込まない。和文抄録は「1-4群と5-7群に区分した」で変数名を与えていないため、この追記は和文にない主張を足すのではなく、和文では暗黙の同一性を英文で明示するものである。
- 語数: +2語

### R-3 推奨: Table 1脚注が行ラベルと同じ用語で書かれていない

- 該当: [paper.md:143](paper.md#L143) 脚注末文、[paper.md:140-141](paper.md#L140-L141) 行ラベル
- 現行

  > Perceived thermal sensation in the bathroom and dressing room was rated on a 7-point scale from 1 (very warm) to 7 (very cold); for each room, only the derived coldness score 5-7 group is shown.

- 問題: 表の行ラベルは `Perceived bathroom coldness` / `Perceived dressing-room coldness` であり、脚注の主語 `Perceived thermal sensation` と字面が一致しない。`derived` の一語で派生関係を示唆してはいるが、何から何が派生したかは書かれていない。表を単独で読む読者（確認依頼4）にとっては、脚注と行の対応付けが推測に委ねられる。
- 提案

  > Perceived bathroom coldness and perceived dressing-room coldness were derived from perceived thermal sensation, which was rated for each room on a 7-point scale from 1 (very warm) to 7 (very cold); only the coldness score 5-7 group is shown.

- 効果: R-2と合わせて、Abstract・Table 1の双方で「測定概念→派生群」の関係が明示され、用語不統一との誤読を防げる。

### R-4 推奨: Abstractの central heating の分母記述に係り受けの曖昧性が残る

- 該当: [paper.md:113](paper.md#L113) Methods
- 現行

  > Central heating analyses included 145 of 154 respondents with non-missing data on that item.

- 問題2点。
  1. `145 of 154 respondents with non-missing data` は、修飾句が `154 respondents` に係ると読める。その場合「非欠測の154人のうち145人」となり、実際（154部中145人が非欠測）と食い違う。第1巡で提案した定冠詞付きの形（`the 145 of the 154`）は冗長さを理由に不採用とされたが、冗長性の回避と引き換えに曖昧性が残った。
  2. `that item` の先行詞となる名詞 `item` がAbstract内に存在しない。直前の主語は `Central heating analyses` であり、`item` は和文「同項目」の直訳として機能しているが、英文単独では指示先が明示されていない。
- 提案（和文「回収した154部のうち同項目への回答が得られた145人を対象とした」に対応）

  > Analyses of central heating use included the 145 respondents with non-missing responses to this item among the 154 returned questionnaires.

- 最小修正案（語数を抑える場合）

  > Central heating analyses included the 145 of the 154 respondents with non-missing data on this item.

- 語数: 推奨案で+5語、最小案で+3語

### R-5 推奨: Table 1脚注の "shown separately" が同一脚注内で二義になっている

- 該当: [paper.md:143](paper.md#L143)
- 問題: 脚注は `shown separately` を2回使うが、指す内容が異なる。
  - セントラル暖房の Missing 9: 割合を付さない別行として表示（[paper.md:133](paper.md#L133)）
  - その他暖房設備の Missing 8: 割合 5.4 を付した別行として表示（[paper.md:139](paper.md#L139)）
  同じ語で異なる扱いを説明しているため、表を単独で読むと「なぜ一方だけ割合がないのか」が脚注から解決できない。分母の説明（確認依頼4）で唯一残っている実質的な穴である。
- 提案（2文をそれぞれ具体化）

  > For central heating use, 145 of the 154 returned questionnaires had non-missing data; the nine missing responses are shown in a separate row without a percentage.

  > ... was assessed with a multiple-response item; therefore, percentages do not sum to 100%, and missing responses are shown in a separate row, with the percentage based on the 147 respondents.

- 備考: 表題が `(n = 147)` である一方、セントラル暖房行の合計が 145 + 9 = 154 となる点は、現行脚注の第1文で分母が回収154部側であることが読み取れるため、追加の説明は不要と判断した。前回メモC-7の整理を維持してよい。

### R-6 推奨: Abstract末文の並列が読み違いを招く

- 該当: [paper.md:113](paper.md#L113) Conclusions
- 現行

  > ... understanding the specific constraints that impede equipment installation or use and the heating configuration of the home, in addition to the need for such equipment, remains a matter for future investigation.

- 問題: `constraints that impede equipment installation or use and the heating configuration of the home` は、`impede` の目的語が `equipment installation or use` と `the heating configuration of the home` の2つであるとも読める。和文（[paper.md:84](paper.md#L84)）は「導入・使用を妨げる具体的制約」と「住宅の暖房構成」を並置しており、暖房構成は「妨げられる対象」ではない。文末まで読めば正しい解釈に落ち着くが、一度誤って解析される構文である。
- 提案（`both` を挿入して並列の範囲を確定させる。語順・語調は現行のまま）

  > When measures to address bathroom coldness in cold regions are considered, understanding both the specific constraints that impede equipment installation or use and the heating configuration of the home, in addition to the need for such equipment, remains a matter for future investigation.

- 語数: +1語
- 断定の強さ: 変化しない。`remains a matter for future investigation` の維持に賛成する。`remains` が「従前から未解決」を含意し、和文「今後の検討課題となる」の将来形とわずかにずれる点は認識したが、勧告性は生じておらず、和文結論（[paper.md:84](paper.md#L84)）とも整合するため変更不要と判断した。

### R-7 推奨: 同一選択肢の英訳が2箇所で異なる

- 該当: [paper.md:113](paper.md#L113) と [paper.md:149](paper.md#L149)
- 現行
  - Abstract: `inability to undertake construction work in rented housing`
  - Fig. 1 legend: `inability to carry out construction work in rented housing`
- 問題: いずれも和文の理由5「賃貸で工事できない」（[paper.md:36](paper.md#L36)）の訳であり、同一原文に対する訳語が抄録と図で異なる。他の3理由（電気代・設置費用・住宅構造）はlegend側が短縮ラベルであるため差異が説明可能だが、この項目のみ両方がフルフレーズで動詞だけが違う。
- 提案: Abstractが正式な定義文であるため、legend側を `undertake` に統一する。逆方向の統一でも可。

### R-8 任意: `at least one of four reasons`

- 該当: [paper.md:113](paper.md#L113)
- 直後にコロンで4項目を列挙するため意味は通るが、`at least one of the following four reasons` とすると列挙との接続が明確になる。+1語。

### R-9 任意: Fig. 1 legendの `N` が未定義

- 該当: [paper.md:149](paper.md#L149)
- 現行 `Bars show the observed n/N (%) within each group.` の `N` は群の人数（50または62）を指すが、legend内で定義されていない。`Bars show n/N (%), where N is the number of respondents in the group.` とすれば図単独で解決する。前段で各群のnを示しているため、対応不要と判断してもよい。

### R-10 確認: English Title Page に和文Title Pageと対応しない欠落がある

- 該当: [paper.md:3-10](paper.md#L3-L10) と [paper.md:107-109](paper.md#L107-L109)
- 和文Title Pageは 論文種別・和文題名・著者・所属・責任著者・ランニングタイトル の6項目、English側は Authors・Affiliations・Corresponding author の3項目である。前回メモD-2でtelephone numberを除いて和文と対応させた方針に照らすと、`Article type` と `Running title` の英語欄が欠けている点も同じ扱いの対象になる。
- 対応: 投稿規程で英文ランニングタイトルが必要かを確認し、必要なら和文ランニングタイトル「浴室暖房乾燥機の未設置・未使用理由と浴室の温冷感」に対応する英語表記と、`Article type: Short report` を追加する。規程上不要であれば現行維持でよいが、その旨を対応メモに記録しておくと次巡で再指摘されない。

### R-11 任意: キーワードの単複

- 該当: [paper.md:115](paper.md#L115)
- Abstract本文は `cold regions`（複数）、キーワードは `cold region`（単数）である。キーワードを単数形で立てるのは一般的な慣例であり、前回メモD-4の判断（変更不要）を覆す必要はない。投稿先がキーワードの表記形を指定している場合のみ調整する。

## 前回メモの確認依頼への回答

1. **文法・構文上の問題**: 重大な誤りは残っていない。残存するのは読み違いを誘発する構文2件（R-6の並列、R-4の係り受け）と、指示先が明示されない `that item`（R-4）のみである。
2. **和文より強い断定・推定・勧告**: 規範表現（`should`、`must`、`need to` 等）は全廃されており、Objective/Methods/Results/Conclusionsのいずれにも和文を超える推定はない。唯一の例外がR-1で、勧告性ではなく**事実の断定**の方向で検証範囲を超えている。Abstract末文の `remains a matter for future investigation`、Conclusionsの `some non-users ... reported`（和文「〜した者が観察された」）はいずれも適切な強さである。
3. **`perceived thermal sensation` と `perceived bathroom coldness` の区別**: 概念設計は妥当だが、現行稿は両者を結ぶ一文を欠くため、読者が別変数と誤読する余地がある。R-2（Abstract）とR-3（Table 1脚注）の2箇所を直せば、測定概念と派生解析変数の関係が英文単独で完結する。
4. **Table 1とFig. 1 legendの単独理解**: 分母（147、145/154、群別50・62）と複数回答の扱いは明示されており、派生群も脚注・legendで説明されている。残る誤解の源はR-5（欠測表示の語義が二義）とR-1（重複の説明）である。この2件で単独理解の要件は満たされる。
5. **意図的不採用・別解とした項目**: 英文上の重大な問題はない。個別の判断は次節に記す。

## 現状維持を支持する項目（再指摘は不要）

- **ASCIIハイフン（C-6）**: `1-4`、`5-7`、`January-February` の維持に同意する。repo規約が優先すべき理由として十分であり、en dashへの置換は投稿先の組版工程で処理される。最終投稿版でen dashに変換するか否かの方針だけ、どこかに一行残しておけば次巡で再燃しない。
- **`bathroom heating dryer`（D-3）**: 文献3および `translation/glossary.csv` との一貫性を優先する判断に同意する。
- **`Perceived Thermal Sensation` を題名に用いる判断（D-1）**: 和文題名「浴室の温冷感」と一対一で対応しており妥当。題名末尾が `in the Bathroom in Goshogawara City` と前置詞句を重ねる点は、和文題名にない副題を追加せずに解消する手段がないため、現行維持を支持する。
- **`Fig. 1` と `### Figure 1` の使い分け（C-3）**: Markdown構造上の役割が異なるため問題ない。
- **タイトルケース、`a priori` / `post hoc`、`dressing room` と `dressing-room` の使い分け、抄録の4区分構造**: 現行のままでよい。
- **`After data collection` と `exploratory post hoc` の併記**: 標識がやや重複するが、和文「回答回収後に探索的に」との一対一対応を優先する判断に同意する。変更不要。
- **`Counts and percentages are reported.` の現在時制**: 抄録の慣例に沿っており、他文の過去時制との混在は許容範囲。

## Codex側での検証依頼

1. **Abstract語数**: 当方の集計では空白区切りで392語（区分見出し `Objective:` 等を除くと388語）であり、前回メモの396語と4語の差がある。集計方法の違い（`51/62` や `5-7` の分割、見出しの計上有無）と思われるが、投稿規程の上限に対する余裕を確認したい。上記の推奨修正をすべて採用した場合の増分は+9〜11語で、およそ401〜403語となる。上限400語の場合は、R-4を最小修正案（+3語）に切り替えるか、Objectiveの `from a questionnaire survey` などで調整余地がある。
2. **1-4群における重複人数**: 費用系と住宅・設置制約系を重複選択した回答者数を、浴室寒さ1-4群についても解析結果から確認されたい。重複が両群で存在することが確認できれば、R-1はより強い表現（`exceeds`）も選択可能になる。確認できない場合は提案どおり `can exceed` を採用する。
3. **英語版Figure 1の図中ラベル**: legendが `reason 1`、`reasons 2-5`、`reasons 2 and 3`、`reasons 4 and 5` と番号で参照しているため、図中の凡例・軸ラベルがこの番号体系と対応しているか（あるいは番号なしでもlegendの括弧内説明で対応が取れるか）を確認されたい。R-7の訳語統一を適用する場合、図中に該当文言があれば同時に更新が必要である。
4. **DOCX出力**: Table 1の `&lt;30 years`（[paper.md:129](paper.md#L129)）が `<30 years` として正しく出力されるかを、今回の再修正後のDOCXでも確認されたい。
5. **回帰確認**: 上記修正はいずれも英文の文言のみで、解析ロジック・数値・和文本文には影響しない。Table 1の数値36行、Abstract主要数値、markdownlintが従前どおりであることの確認で足りる。

## 想定される変更範囲

| 箇所 | 行 | 指摘ID | 区分 |
| --- | --- | --- | --- |
| Fig. 1 legend | [149](paper.md#L149) | R-1 | 必須 |
| English Abstract Methods | [113](paper.md#L113) | R-2, R-4, R-7, R-8 | 推奨・任意 |
| English Abstract Conclusions | [113](paper.md#L113) | R-6 | 推奨 |
| Table 1脚注 | [143](paper.md#L143) | R-3, R-5 | 推奨 |
| Fig. 1 legend | [149](paper.md#L149) | R-7, R-9 | 推奨・任意 |
| English Title Page | [107-109](paper.md#L107-L109) | R-10 | 確認 |
| English keywords | [115](paper.md#L115) | R-11 | 任意 |

和文題名、和文抄録、和文本文、引用文献、Table 1の数値、English Titleについては変更を要する箇所を認めなかった。
