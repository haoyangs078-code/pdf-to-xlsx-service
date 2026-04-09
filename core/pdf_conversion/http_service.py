# -*- coding: utf-8 -*-
"""
PDF 结算单 → Excel 的 HTTP 服务（供对接方调用）。

启动（项目根目录）::

    pip install fastapi uvicorn python-multipart
    python scripts/run_pdf_to_excel_service.py

环境变量（可选）::

    PDF_TO_XLSX_API_KEY   若设置，则请求须带 Header: X-Api-Key: <值>
    PDF_TO_XLSX_HOST      默认 0.0.0.0
    PDF_TO_XLSX_PORT      默认 8765
"""

from __future__ import annotations

import os
import re
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response

from core.pdf_conversion.settlement_pdf import pdf_bytes_to_xlsx_bytes


def _expected_api_key() -> Optional[str]:
    raw = (os.getenv("PDF_TO_XLSX_API_KEY") or "").strip()
    return raw or None


def create_app() -> FastAPI:
    app = FastAPI(
        title="PDF 结算单转 Excel",
        description="上传电力结算类 PDF（首页为表格），返回与宁波宁能样本结构一致的 xlsx。",
        version="1.0.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/v1/pdf-to-xlsx",
        summary="PDF 转 Excel",
        response_class=Response,
        responses={
            200: {
                "content": {
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
                },
                "description": "xlsx 二进制",
            }
        },
    )
    async def convert_pdf_to_xlsx(
        file: UploadFile = File(..., description="结算单 PDF"),
        x_api_key: Optional[str] = Header(default=None, alias="X-Api-Key"),
    ) -> Response:
        expected = _expected_api_key()
        if expected is not None and x_api_key != expected:
            raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Key")

        fname = (file.filename or "upload.pdf").strip()
        if not fname.lower().endswith(".pdf"):
            fname = fname + ".pdf"

        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="空文件")
        if len(raw) < 5 or not raw.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="内容不是 PDF（应以 %PDF 开头）")

        try:
            xlsx_bytes = pdf_bytes_to_xlsx_bytes(raw)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"PDF 解析失败: {e!s}",
            ) from e

        base = fname.rsplit("/", 1)[-1].rsplit(".", 1)[0] + ".xlsx"
        # Starlette 响应头须为 latin-1；中文文件名用 RFC 5987 filename*（仅 ASCII）
        ascii_fallback = re.sub(r"[^\x20-\x7e]", "_", base) or "converted.xlsx"
        if len(ascii_fallback) > 120:
            ascii_fallback = "converted.xlsx"
        cd = (
            f'attachment; filename="{ascii_fallback}"; '
            f"filename*=UTF-8''{quote(base)}"
        )
        return Response(
            content=xlsx_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": cd},
        )

    return app
