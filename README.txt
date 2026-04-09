PDF 结算单 -> Excel HTTP 服务（独立仓库）

部署：
  python -m pip install -r requirements-pdf-to-xlsx-service.txt
  python scripts/run_pdf_to_excel_service.py

文档：docs/ 下 md。浏览器调试：http://127.0.0.1:8765/docs

测试（需先安装依赖）：
  PYTHONPATH=. python -m unittest tests.test_pdf_conversion_http -v
