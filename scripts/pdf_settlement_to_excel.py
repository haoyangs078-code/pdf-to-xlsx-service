# -*- coding: utf-8 -*-
"""
将电力结算类 PDF（单页表格）解析为 Excel。

用法（项目根目录）:
  python scripts/pdf_settlement_to_excel.py
  python scripts/pdf_settlement_to_excel.py -i "某文件.pdf" -o "输出.xlsx"
  python scripts/pdf_settlement_to_excel.py --layout single_sheet -i "某文件.pdf" -o "单表.xlsx"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main() -> int:
    from core.pdf_conversion.settlement_pdf import pdf_to_excel
    root = Path(__file__).resolve().parents[1]
    default_pdf = root / "宁波宁能电力销售有限公司2026年03月28日结算单-现货日清分(售电公司).pdf"
    parser = argparse.ArgumentParser(description="PDF 结算单转 Excel")
    parser.add_argument("-i", "--input", type=Path, default=default_pdf, help="输入 PDF 路径")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出 xlsx（默认与 PDF 同目录同名）",
    )
    parser.add_argument(
        "--layout",
        choices=("settlement", "single_sheet"),
        default="settlement",
        help="settlement=多 sheet 结算样式；single_sheet=通用单表（全页表格合并）",
    )
    args = parser.parse_args()
    pdf_path = args.input
    if not pdf_path.is_file():
        print(f"文件不存在: {pdf_path}", file=sys.stderr)
        return 1
    out = args.output
    if out is None:
        out = pdf_path.with_suffix(".xlsx")

    pdf_to_excel(pdf_path, out, layout=args.layout)
    print(f"已生成: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
