# -*- coding: utf-8 -*-
"""
电力结算类 PDF（首页表格）解析为 Excel。

输出多 sheet：基本信息、结算明细、原始表格、PDF全文、备注（与宁波宁能样本一致）。
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd


def _parse_header_meta(text: str) -> List[tuple[str, str]]:
    """从全文前几行提取标题、日期、计量单位等。"""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    rows: List[tuple[str, str]] = []
    for ln in lines[:8]:
        if "计量单位" in ln:
            rows.append(("计量单位", re.sub(r"^计量单位[：:]\s*", "", ln)))
            continue
        if re.match(r"^\d{4}年\d{1,2}月\d{1,2}日$", ln):
            rows.append(("日期", ln))
            continue
        if "清分单" in ln or "结算单" in ln:
            rows.append(("单据名称", ln))
            continue
        if ln.startswith("售电公司名称"):
            parts = ln.split(None, 1)
            rows.append(("售电公司名称", parts[1] if len(parts) > 1 else ""))
            continue
        if ln.startswith("实际用电量"):
            m = re.search(r"实际用电量\s+([\d.\-]+)", ln)
            rows.append(("实际用电量", m.group(1) if m else ln))
            continue
    return rows


def _normalize_detail_table(raw: List[List[Any]]) -> pd.DataFrame:
    """
    将 pdfplumber 提取的二维表转为明细 DataFrame。

    列：一级分类、二级分类、结算项目、结算电量、结算电价、结算费用
    """
    if not raw or len(raw) < 4:
        return pd.DataFrame()

    records: List[dict[str, Any]] = []
    header_row = None
    start_idx = 0
    for i, row in enumerate(raw):
        if row and row[0] == "结算项目明细":
            header_row = row
            start_idx = i + 1
            break

    if header_row is None:
        start_idx = 0

    cat1: Optional[str] = None
    cat2: Optional[str] = None

    for row in raw[start_idx:]:
        if not any(x is not None and str(x).strip() for x in row):
            continue
        c0 = row[0] if len(row) > 0 else None
        c1 = row[1] if len(row) > 1 else None
        c2 = row[2] if len(row) > 2 else None
        c3 = row[3] if len(row) > 3 else None
        c4 = row[4] if len(row) > 4 else None
        c5 = row[5] if len(row) > 5 else None

        if c0 and str(c0).strip():
            cat1 = str(c0).strip()
        if c1 is not None and str(c1).strip():
            cat2 = str(c1).strip()

        name = ""
        if c2 is not None and str(c2).strip():
            name = str(c2).strip()
        elif cat2 and c3 is not None:
            name = cat2

        if c3 is None and c4 is None and c5 is None:
            continue

        label = (c0 or "") + (c1 or "") + (c2 or "")
        if "小计" in label or "合计" in label or "偏差" in label:
            name = (c2 or c1 or c0 or "").strip() or name

        records.append(
            {
                "一级分类": cat1 or "",
                "二级分类": cat2 or "",
                "结算项目": name
                if name
                else (str(c1).strip() if c1 else ""),
                "结算电量": c3,
                "结算电价": c4,
                "结算费用": c5,
            }
        )

    return pd.DataFrame(records)


def _require_openpyxl() -> None:
    """pandas 写 xlsx 依赖 openpyxl；缺失时给出可操作的报错。"""
    try:
        import openpyxl  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "缺少 Python 包 openpyxl。请在运行本服务的同一环境中执行: pip install openpyxl"
        ) from e


def _write_workbook(writer: pd.ExcelWriter, text: str, raw: List[List[Any]]) -> None:
    meta_rows = _parse_header_meta(text)
    meta_df = pd.DataFrame(meta_rows, columns=["项目", "内容"])

    detail_df = _normalize_detail_table(raw)
    if detail_df.empty and raw:
        detail_df = pd.DataFrame(raw)

    raw_df = pd.DataFrame(raw) if raw else pd.DataFrame()

    remark = ""
    if "备注" in text:
        remark = text[text.index("备注") :]

    meta_df.to_excel(writer, sheet_name="基本信息", index=False)
    if not detail_df.empty:
        detail_df.to_excel(writer, sheet_name="结算明细", index=False)
    if not raw_df.empty:
        raw_df.to_excel(writer, sheet_name="原始表格", index=False, header=False)
    pd.DataFrame({"全文文本": [text]}).to_excel(writer, sheet_name="PDF全文", index=False)
    if remark:
        pd.DataFrame({"备注": [remark]}).to_excel(writer, sheet_name="备注", index=False)


def pdf_to_excel(pdf_path: Path, xlsx_path: Path) -> None:
    """从本地 PDF 路径生成 xlsx 文件。"""
    import pdfplumber

    pdf_path = pdf_path.resolve()
    xlsx_path = xlsx_path.resolve()
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[0]
        text = page.extract_text() or ""
        tables = page.extract_tables() or []
        raw = tables[0] if tables else []

    _require_openpyxl()
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        _write_workbook(writer, text, raw)


def pdf_bytes_to_xlsx_bytes(pdf_bytes: bytes) -> bytes:
    """
    将 PDF 二进制转为 xlsx 二进制（内存中完成，供 HTTP 接口使用）。

    Args:
        pdf_bytes: PDF 文件内容

    Returns:
        xlsx 文件字节
    """
    import pdfplumber

    buf_in = io.BytesIO(pdf_bytes)
    with pdfplumber.open(buf_in) as pdf:
        page = pdf.pages[0]
        text = page.extract_text() or ""
        tables = page.extract_tables() or []
        raw = tables[0] if tables else []

    _require_openpyxl()
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        _write_workbook(writer, text, raw)
    return out.getvalue()
