#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
import unicodedata

# ===== 列名别名与清洗 =====
CSV_COL_ALIASES = {
    "组分面积": ["组分面积", "面积", "Area", "组分 Area", "组分Area"],
    "基峰信噪比": ["基峰信噪比", "基峰 S/N", "S/N", "信噪比", "基峰信噪比值"],
    "匹配因子": ["匹配因子", "匹配分数", "匹配score"],
    "基峰解卷积的面积": ["基峰解卷积的面积", "基峰解卷积面积", "解卷积面积", "去卷积面积", "DeconvArea"],
    "组分 RI": ["组分 RI", "组分RI", "RI", "Retention Index"],
    "谱库 RI":["谱库 RI", "谱库RI"]
}

def clean_header(name: str) -> str:
    """NFKC 规范化 + 去 BOM/零宽/不换行空格 + 合并多空格"""
    s = unicodedata.normalize("NFKC", str(name))
    for ch in ("\ufeff", "\u200b", "\u200c", "\u00a0"):
        s = s.replace(ch, " ")
    s = " ".join(s.strip().split())
    return s

def resolve_csv_columns(df: pd.DataFrame) -> dict:
    
    norm_map = {clean_header(c): c for c in df.columns}
    mapping = {}
    for std, aliases in CSV_COL_ALIASES.items():
        for a in aliases:
            key = clean_header(a)
            if key in norm_map:
                mapping[std] = norm_map[key]
                break
    return mapping


EXCEL_KEY_DEFAULT = "high a"        
INSERT_AFTER_COL = "high y"        
CSV_VALUE_COLS: List[str] = ["基峰信噪比", "匹配因子", "基峰解卷积的面积", "组分 RI", "谱库 RI"]


def read_csv_utf8(path: Path, enc: str = "utf-8-sig") -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding=enc)
    except UnicodeDecodeError as e:
        raise RuntimeError(f"该 CSV 不是 {enc} 编码：{path}") from e

def to_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")

def cents_key_from_float(series: pd.Series) -> pd.Series:
    vals = to_numeric(series)
    cents = np.round(vals * 100.0).astype("float")
    return pd.Series(cents, index=series.index).astype("Int64")

def ensure_required_columns(df: pd.DataFrame, cols: List[str], df_name: str):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise RuntimeError(f"{df_name} 缺少列：{miss}；现有列：{list(df.columns)}")

def next_available_path(base: Path) -> Path:
    if not base.exists():
        return base
    i = 1
    while True:
        cand = base.with_name(f"{base.stem}({i}){base.suffix}")
        if not cand.exists():
            return cand
        i += 1

# ===== 合并一次 =====
def merge_once(df_base: pd.DataFrame,
               df_csv: pd.DataFrame,
               excel_key_col: str,
               insert_after_col: str,
               update_policy: str = "fillna",
               verbose: bool = True) -> pd.DataFrame:
    
 
    df_b = df_base.copy()
    df_b.columns = [clean_header(c) for c in df_b.columns]

    df_c = df_csv.copy()
    df_c.columns = [clean_header(c) for c in df_c.columns]

 
    ensure_required_columns(df_b, [excel_key_col, insert_after_col], "Excel基表")

 
    mapping = resolve_csv_columns(df_c)
    if "组分面积" not in mapping:
        raise RuntimeError("CSV 缺少用于匹配的键列【组分面积】（或其别名），无法合并。")

    value_cols_present = [c for c in CSV_VALUE_COLS if c in mapping]
    value_cols_missing = [c for c in CSV_VALUE_COLS if c not in mapping]
    if verbose:
        print(f"[DBG] 可用列: {value_cols_present} | 缺失列(跳过): {value_cols_missing}")

  
    key_left = cents_key_from_float(df_b[excel_key_col])
    key_right = cents_key_from_float(df_c[mapping["组分面积"]])

    df_b["__key__"] = key_left
    df_c["__key__"] = key_right


    if "__key__" in df_c.columns:
        df_c = df_c.drop_duplicates(subset=["__key__"], keep="first")

    new_cols_created = []  
    for col in value_cols_present:
        src_col = mapping[col] 
       
        right_map = df_c.set_index("__key__")[src_col]
       
        incoming = df_b["__key__"].map(right_map)

        if col in df_b.columns:
            if update_policy == "overwrite":
                
                df_b[col] = incoming.where(incoming.notna(), df_b[col])
            else:
              
                df_b[col] = df_b[col].where(df_b[col].notna(), incoming)
        else:
           
            df_b[col] = incoming
            new_cols_created.append(col)

  
    if new_cols_created:
        cols = list(df_b.columns)
        remaining = [c for c in cols if c not in new_cols_created]
        if insert_after_col in remaining:
            pos = remaining.index(insert_after_col) + 1
            cols_new = remaining[:pos] + new_cols_created + remaining[pos:]
            df_b = df_b.reindex(columns=cols_new)

    df_b = df_b.drop(columns=["__key__"])

    return df_b




def main():
    ap = argparse.ArgumentParser(description="combine CSV to Excel")
    ap.add_argument("--excel", default=r".\The Excel file path output in Step 1" ,help=".xlsx" )
    ap.add_argument("--csv-dir", default=r".\CSV file output from unknown substance analysis software", help="A folder containing multiple CSVs, merge them all sorted by filename")
    ap.add_argument("--excel-key-col", default=EXCEL_KEY_DEFAULT,
                    help=f"Excel（{EXCEL_KEY_DEFAULT}）")
    ap.add_argument("--encoding", default="utf-8-sig", choices=["utf-8-sig", "utf-8"],
                    help="CSV （ utf-8-sig）")
    ap.add_argument("--output", default=r".\Output file path of step 2", help="Output file path of step 2")
    ap.add_argument("--reuse-output", action="store_true",
                    help="The output file already exists")
    ap.add_argument("--no-increment", action="store_true",
                    help="-reuse-output")
    ap.add_argument("--update-policy", choices=["fillna", "overwrite"], default="fillna",
                    help="Update strategy when the target column already exists")
    ap.add_argument("--verbose", action="store_true", help="Print the column names and mappings of each CSV to make it easier to troubleshoot")
    args = ap.parse_args()

    excel_path = Path(args.excel)
    out_path = Path(args.output)


    base_path = out_path if (args.reuse_output and out_path.exists()) else excel_path
    try:
        df_base = pd.read_excel(base_path, engine="openpyxl")

        df_base.columns = [clean_header(c) for c in df_base.columns]
    except Exception as e:
        print(f"[Error] ：{base_path} -> {e}", file=sys.stderr)
        sys.exit(1)


    csv_dir = Path(args.csv_dir)
    if not csv_dir.is_dir():
        print(f"[Error] ：{csv_dir}", file=sys.stderr)
        sys.exit(1)
    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        print(f"[Error] ：{csv_dir}", file=sys.stderr)
        sys.exit(1)


    current = df_base
    for csv_path in csv_files:
        try:
            df_c = read_csv_utf8(csv_path, args.encoding)

            df_c.columns = [clean_header(c) for c in df_c.columns]
            if args.verbose:
                print(f"[DBG] {csv_path.name} ：", [repr(c) for c in df_c.columns])
        except Exception as e:
            print(f"[Warn]  {csv_path.name}：{e}", file=sys.stderr)
            continue

        try:
            current = merge_once(current, df_c, args.excel_key_col, INSERT_AFTER_COL, args.update_policy)
            print(f"[Info] ：{csv_path.name}")
        except Exception as e:
            print(f"[Warn]  {csv_path.name}：{e}", file=sys.stderr)


    if out_path.exists() and not args.no_increment and not args.reuse_output:
        out_path = next_available_path(out_path)
    try:
        with pd.ExcelWriter(out_path, engine="openpyxl") as w:
            current.to_excel(w, index=False, sheet_name="Sheet1")
        print(f"[OK] output：{out_path.resolve()}")
    except Exception as e:
        print(f"[Error] output failed：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
