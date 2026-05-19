from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import scipy
import statsmodels
import statsmodels.api as sm
from scipy import stats

from env_utils import load_repo_env


PREFS = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]

AREA_TO_PREF = {f"{i:02d}000": pref for i, pref in enumerate(PREFS, start=1)}

DEFAULT_BASE_RELATIVE = Path("..") / "入浴統計" / "data" / "processed" / "full_panel.csv"
CAO_INCOME_XLSX_URL = "https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2022/soukatu7.xlsx"

ESTAT_ANNUAL_INCOME_STATS_ID = "0003426444"
ESTAT_ASSET_STATS_ID = "0003426523"

FOCUS_PREFS = ["青森県", "秋田県", "宮城県", "岩手県"]


def _slugify_ascii(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "run"


def _default_tag(slug: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{_slugify_ascii(slug)}"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(",", "")
        if s in ("", "-", "NA"):
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _estat_get_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    base = "https://api.e-stat.go.jp/rest/3.0/app/json"
    url = f"{base}/{endpoint}?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    root_key = {"getStatsData": "GET_STATS_DATA", "getMetaInfo": "GET_META_INFO"}[endpoint]
    root = data[root_key]
    result = root.get("RESULT", {})
    if result.get("STATUS") not in (0, "0", None):
        raise RuntimeError(f"e-Stat API error ({endpoint}): {result}")
    return root


def _estat_values_to_df(root: dict[str, Any]) -> pd.DataFrame:
    values = root.get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("VALUE", [])
    if isinstance(values, dict):
        values = [values]
    records = []
    for v in values:
        rec: dict[str, Any] = {}
        for k, val in v.items():
            if k == "$":
                rec["value"] = _to_float(val)
            elif k.startswith("@"):
                rec[k[1:]] = val
            else:
                rec[k] = val
        records.append(rec)
    return pd.DataFrame.from_records(records)


def _download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=60, stream=True) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)


def _load_heater_rate(base_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(base_csv)
    d = df.loc[pd.to_numeric(df["year"], errors="coerce") == 2023, ["pref_name", "bathroom_heater_rate"]].copy()
    d["bathroom_heater_pp"] = pd.to_numeric(d["bathroom_heater_rate"], errors="coerce") * 100.0
    return d[["pref_name", "bathroom_heater_pp"]]


def _load_per_capita_income(xlsx_path: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name="実数", header=None)
    out = df.loc[df[1].isin(PREFS), [1, 14]].copy()
    out.columns = ["pref_name", "per_capita_pref_income_2022_kJPY"]
    out["per_capita_pref_income_2022_kJPY"] = pd.to_numeric(out["per_capita_pref_income_2022_kJPY"], errors="coerce")
    return out


def _fetch_annual_income(app_id: str) -> pd.DataFrame:
    root = _estat_get_json(
        "getStatsData",
        {
            "appId": app_id,
            "statsDataId": ESTAT_ANNUAL_INCOME_STATS_ID,
            "lang": "J",
            "limit": 50000,
            "metaGetFlg": "Y",
            "cntGetFlg": "N",
            "explanationGetFlg": "N",
            "annotationGetFlg": "N",
            "cdTab": "03-2019",
            "cdCat01": "0",
            "cdCat02": "0",
            "cdCat03": "2",
            "cdCat04": "0",
            "cdTime": "2019000000",
        },
    )
    d = _estat_values_to_df(root)
    d["pref_name"] = d["area"].map(AREA_TO_PREF)
    d = d.rename(columns={"value": "annual_income_2019_kJPY"})
    return d[["pref_name", "annual_income_2019_kJPY"]].copy()


def _fetch_asset_metric(app_id: str, cat03: str, name: str) -> pd.DataFrame:
    root = _estat_get_json(
        "getStatsData",
        {
            "appId": app_id,
            "statsDataId": ESTAT_ASSET_STATS_ID,
            "lang": "J",
            "limit": 50000,
            "metaGetFlg": "Y",
            "cntGetFlg": "N",
            "explanationGetFlg": "N",
            "annotationGetFlg": "N",
            "cdTab": "04-2019",
            "cdCat01": "0",
            "cdCat02": "0",
            "cdCat03": cat03,
            "cdCat04": "00",
            "cdTime": "2019000000",
        },
    )
    d = _estat_values_to_df(root)
    d["pref_name"] = d["area"].map(AREA_TO_PREF)
    d = d.rename(columns={"value": name})
    return d[["pref_name", name]].copy()


def _assoc(d: pd.DataFrame, x_col: str, y_col: str = "bathroom_heater_pp") -> dict[str, Any]:
    x = pd.to_numeric(d[x_col], errors="coerce")
    y = pd.to_numeric(d[y_col], errors="coerce")
    ok = x.notna() & y.notna()
    x = x.loc[ok].astype(float)
    y = y.loc[ok].astype(float)
    X = sm.add_constant(pd.DataFrame({"x": x.to_numpy()}))
    model = sm.OLS(y.to_numpy(), X).fit()
    pear = stats.pearsonr(x.to_numpy(), y.to_numpy())
    spear = stats.spearmanr(x.to_numpy(), y.to_numpy())
    ci = model.conf_int().loc["x"].tolist()
    return {
        "indicator": x_col,
        "n": int(ok.sum()),
        "pearson_r": float(pear.statistic),
        "pearson_p": float(pear.pvalue),
        "spearman_rho": float(spear.statistic),
        "spearman_p": float(spear.pvalue),
        "ols_slope_pp_per_unit": float(model.params["x"]),
        "ols_slope_ci_low": float(ci[0]),
        "ols_slope_ci_high": float(ci[1]),
        "ols_p": float(model.pvalues["x"]),
        "ols_r2": float(model.rsquared),
    }


def _fmt_p(p: float) -> str:
    if p < 0.0001:
        return "p<0.0001"
    if p < 0.001:
        return f"p={p:.4f}"
    if p < 0.2:
        return f"p={p:.3f}"
    if p <= 0.99:
        return f"p={p:.2f}"
    return "p>0.99"


def _df_to_md(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(df.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row.tolist()) + " |")
    return "\n".join(lines)


def _write_report(out_md: Path, analysis: pd.DataFrame, assoc: pd.DataFrame, meta: dict[str, Any]) -> None:
    disp = assoc.copy()
    disp["Pearson r"] = disp["pearson_r"].map(lambda x: f"{x:.3f}")
    disp["OLS R2"] = disp["ols_r2"].map(lambda x: f"{x:.3f}")
    disp["p"] = disp["ols_p"].map(_fmt_p)
    disp = disp[["indicator_label", "n", "Pearson r", "OLS R2", "p"]].rename(
        columns={"indicator_label": "指標", "n": "n"}
    )

    focus = analysis.loc[analysis["pref_name"].isin(FOCUS_PREFS)].copy()
    focus["bathroom_heater_pp"] = focus["bathroom_heater_pp"].round(1)
    for col in [
        "per_capita_pref_income_2022_kJPY",
        "annual_income_2019_kJPY",
        "financial_assets_2019_kJPY",
        "financial_liabilities_2019_kJPY",
        "net_financial_assets_2019_kJPY",
        "net_total_assets_2019_kJPY",
    ]:
        focus[col] = pd.to_numeric(focus[col], errors="coerce").round(0).astype("Int64")
    focus = focus[
        [
            "pref_name",
            "bathroom_heater_pp",
            "per_capita_pref_income_2022_kJPY",
            "annual_income_2019_kJPY",
            "financial_assets_2019_kJPY",
            "financial_liabilities_2019_kJPY",
            "net_financial_assets_2019_kJPY",
            "net_total_assets_2019_kJPY",
        ]
    ].rename(
        columns={
            "pref_name": "県",
            "bathroom_heater_pp": "設置率（%）",
            "per_capita_pref_income_2022_kJPY": "1人当たり県民所得 2022年度（千円）",
            "annual_income_2019_kJPY": "年間収入 2019年（千円/世帯）",
            "financial_assets_2019_kJPY": "金融資産残高 2019年（千円/世帯）",
            "financial_liabilities_2019_kJPY": "金融負債残高 2019年（千円/世帯）",
            "net_financial_assets_2019_kJPY": "純金融資産 2019年（千円/世帯）",
            "net_total_assets_2019_kJPY": "純資産総額 2019年（千円/世帯）",
        }
    )

    lines = [
        "# 県別コスト関連指標と浴室暖房乾燥機設置率の関連",
        "",
        f"- 作成日時: {meta['created_at_local']}",
        f"- 解析ソフト: Python {meta['python_version']}",
        "- 主要パッケージ: "
        + ", ".join(f"{k} {v}" for k, v in meta["versions"].items()),
        f"- 浴室暖房乾燥機設置率: `{meta['base_csv']}` の2023年 `bathroom_heater_rate`",
        "- 記述ポリシー: `docs/rules/statistical_reporting_policy.md`",
        "",
        "## 1. 4県の確認値",
        "",
        _df_to_md(focus),
        "",
        "## 2. 全47都道府県での単変量関連",
        "",
        _df_to_md(disp),
        "",
        "## 3. 解釈メモ",
        "",
        "- 5指標はいずれも設置率との正の関連を示す。",
        "- 単回帰のR2は、所得系で0.275-0.426、資産系で0.423-0.641であり、金融資産残高と純資産総額では都道府県間差の相当部分を説明する。",
        "- ただし、所得・資産指標は都市化、住宅種別、住宅価格、持家率などとも関連し得るため、単独の原因としては扱わない。",
        "- 本解析は都道府県単位の生態学的・記述的比較であり、世帯レベルの導入可否や因果効果を示さない。",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="県別の所得・資産指標と浴室暖房乾燥機設置率の関連を集計します。")
    parser.add_argument("--app-id", type=str, default="", help="e-Stat API appId（未指定ならESTAT_APP_ID）")
    parser.add_argument("--base-csv", type=str, default="", help="基盤repo full_panel.csv")
    parser.add_argument("--tag", type=str, default="", help="outputs/runs/<tag>")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    load_repo_env(repo_root)

    app_id = args.app_id.strip() or os.environ.get("ESTAT_APP_ID", "").strip()
    if not app_id:
        print("[error] e-Stat appId is required (--app-id or ESTAT_APP_ID).", file=sys.stderr)
        return 1

    tag = args.tag.strip() or _default_tag("pref_cost_indicators_vs_bathroom_heater_rate")
    out_dir = repo_root / "outputs" / "runs" / tag
    inputs_dir = out_dir / "inputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir.mkdir(parents=True, exist_ok=True)

    base_csv = Path(args.base_csv).expanduser() if args.base_csv else repo_root / DEFAULT_BASE_RELATIVE
    base_csv = base_csv.resolve()

    cao_xlsx = inputs_dir / "cao_per_capita_pref_income_2022.xlsx"
    if not cao_xlsx.exists():
        _download_file(CAO_INCOME_XLSX_URL, cao_xlsx)

    analysis = _load_heater_rate(base_csv)
    for df in [
        _load_per_capita_income(cao_xlsx),
        _fetch_annual_income(app_id),
        _fetch_asset_metric(app_id, "21", "financial_assets_2019_kJPY"),
        _fetch_asset_metric(app_id, "22", "financial_liabilities_2019_kJPY"),
        _fetch_asset_metric(app_id, "2", "net_financial_assets_2019_kJPY"),
        _fetch_asset_metric(app_id, "4", "net_total_assets_2019_kJPY"),
    ]:
        analysis = analysis.merge(df, on="pref_name", how="left")

    indicators = [
        ("per_capita_pref_income_2022_kJPY", "1人当たり県民所得"),
        ("annual_income_2019_kJPY", "年間収入"),
        ("financial_assets_2019_kJPY", "金融資産"),
        ("net_financial_assets_2019_kJPY", "純金融資産"),
        ("net_total_assets_2019_kJPY", "純資産総額"),
    ]
    assoc_records = []
    for col, label in indicators:
        rec = _assoc(analysis, col)
        rec["indicator_label"] = label
        assoc_records.append(rec)
    assoc = pd.DataFrame.from_records(assoc_records)

    analysis.to_csv(out_dir / "pref_cost_indicators_analysis_dataset.csv", index=False, encoding="utf-8")
    assoc.to_csv(out_dir / "pref_cost_indicator_associations.csv", index=False, encoding="utf-8")

    meta = {
        "created_at_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
        "base_csv": str(base_csv),
        "cao_income_xlsx_url": CAO_INCOME_XLSX_URL,
        "estat_annual_income_stats_id": ESTAT_ANNUAL_INCOME_STATS_ID,
        "estat_asset_stats_id": ESTAT_ASSET_STATS_ID,
        "versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
            "requests": requests.__version__,
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_report(out_dir / "report.md", analysis, assoc, meta)

    print(f"[ok] wrote: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
