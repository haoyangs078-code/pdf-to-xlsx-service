# -*- coding: utf-8 -*-
"""PDF→Excel HTTP 服务与转换逻辑测试。"""

from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class TestPdfConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._sample_pdf = project_root / (
            "宁波宁能电力销售有限公司2026年03月28日结算单-现货日清分(售电公司).pdf"
        )

    def test_pdf_bytes_to_xlsx_roundtrip_structure(self) -> None:
        from core.pdf_conversion.settlement_pdf import pdf_bytes_to_xlsx_bytes

        if not self._sample_pdf.is_file():
            self.skipTest("样本 PDF 不存在")
        pdf_bytes = self._sample_pdf.read_bytes()
        xlsx_bytes = pdf_bytes_to_xlsx_bytes(pdf_bytes)
        self.assertTrue(xlsx_bytes.startswith(b"PK"))
        with zipfile.ZipFile(__import__("io").BytesIO(xlsx_bytes)) as z:
            names = z.namelist()
        self.assertTrue(any("sheet" in n.lower() for n in names))

    def test_health_endpoint(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("未安装 fastapi")
        from core.pdf_conversion.http_service import create_app

        client = TestClient(create_app())
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_convert_sample_pdf(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("未安装 fastapi")
        if not self._sample_pdf.is_file():
            self.skipTest("样本 PDF 不存在")

        from core.pdf_conversion.http_service import create_app

        client = TestClient(create_app())
        with self._sample_pdf.open("rb") as f:
            r = client.post(
                "/v1/pdf-to-xlsx",
                files={"file": ("sample.pdf", f, "application/pdf")},
            )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.content.startswith(b"PK"))

    def test_api_key_required_when_set(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("未安装 fastapi")
        import os

        from core.pdf_conversion.http_service import create_app

        os.environ["PDF_TO_XLSX_API_KEY"] = "secret-test"
        try:
            client = TestClient(create_app())
            r = client.post(
                "/v1/pdf-to-xlsx",
                files={"file": ("x.pdf", b"%PDF-1.4\n", "application/pdf")},
            )
            self.assertEqual(r.status_code, 401)
        finally:
            os.environ.pop("PDF_TO_XLSX_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
