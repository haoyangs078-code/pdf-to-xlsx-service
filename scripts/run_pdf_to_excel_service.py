# -*- coding: utf-8 -*-
"""
启动 PDF→Excel HTTP 服务（项目根目录）::

    python scripts/run_pdf_to_excel_service.py

见 core/pdf_conversion/http_service.py 模块文档。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def _check_conversion_deps() -> None:
    """
    与 pdf_to_excel 使用同一套依赖；缺省时提示用「当前解释器」安装，避免多 Python 混用。
    """
    missing: list[str] = []
    for mod in ("pdfplumber", "openpyxl", "pandas"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        exe = sys.executable
        print(
            "错误：当前运行服务的 Python 缺少模块: "
            + ", ".join(missing)
            + "\n当前解释器: "
            + exe
            + "\n请在本机执行（注意必须用同一个 python）：\n  "
            + f'"{exe}" -m pip install pdfplumber openpyxl pandas',
            file=sys.stderr,
        )
        raise SystemExit(1)


def main() -> None:
    try:
        import uvicorn
    except ImportError:
        print(
            "请先安装: pip install fastapi uvicorn python-multipart",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    _check_conversion_deps()

    host = (os.getenv("PDF_TO_XLSX_HOST") or "0.0.0.0").strip()
    port = int((os.getenv("PDF_TO_XLSX_PORT") or "8765").strip())

    uvicorn.run(
        "core.pdf_conversion.http_service:create_app",
        factory=True,
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
