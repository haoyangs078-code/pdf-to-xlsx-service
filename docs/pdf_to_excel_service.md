# PDF 结算单 → Excel 服务（对接说明）

面向需求：对方通过 **HTTP 接口上传 PDF**，下载与「宁波宁能电力销售有限公司…现货日清分(售电公司)」**同结构**的 xlsx（多 sheet：基本信息、结算明细、原始表格、PDF全文、备注等）。

---

## 一、本地自测（当前阶段）

### 1. 安装依赖

```bash
cd <项目根目录>
pip install -r requirements.txt
```

### 2. 启动服务（终端 A）

```bash
python scripts/run_pdf_to_excel_service.py
```

默认监听 **`http://127.0.0.1:8765`**。看到 Uvicorn running 即就绪。

### 3. 验证（终端 B）

健康检查：

```bash
curl -sS "http://127.0.0.1:8765/health"
# 期望: {"status":"ok"}
```

用仓库内样本 PDF 转 xlsx（若文件存在）：

```bash
curl -sS -X POST "http://127.0.0.1:8765/v1/pdf-to-xlsx" \
  -F "file=@宁波宁能电力销售有限公司2026年03月28日结算单-现货日清分(售电公司).pdf" \
  -o /tmp/test_out.xlsx
file /tmp/test_out.xlsx
# 期望: Microsoft Excel 2007+ 或 Zip archive（xlsx 为 ZIP）
```

一键冒烟（**需先启动服务**）：

```bash
bash scripts/smoke_pdf_to_excel_service.sh
```

自动化单测（**不启动 HTTP**，测转换与路由逻辑）：

```bash
python -m unittest tests.test_pdf_conversion_http -v
```

浏览器打开 **`http://127.0.0.1:8765/docs`** 可手动试 POST。

### 4. 本地验收标准（建议）

| 步骤 | 预期 |
|------|------|
| `GET /health` | `200`，JSON 含 `"status":"ok"` |
| `POST /v1/pdf-to-xlsx` + 样本 PDF | `200`，文件头为 ZIP（`PK\x03\x04`），Excel 可打开多 sheet |
| `python -m unittest tests.test_pdf_conversion_http` | 全部通过 |

### 5. 若 `POST` 返回 422（解析失败）

先在同一终端看**响应正文**（含 `detail` 原因），例如：

```bash
curl -sS -X POST "http://127.0.0.1:8765/v1/pdf-to-xlsx" \
  -F "file=@宁波宁能电力销售有限公司2026年03月28日结算单-现货日清分(售电公司).pdf"
```

常见情况：

| 现象 | 处理 |
|------|------|
| `detail` 里提到 **openpyxl** | **启动 Uvicorn 用的 Python 环境**里未安装：`pip install openpyxl`（conda 则 `conda install openpyxl` 或在该 env 里 pip） |
| 其它 PDF 解析异常 | 确认 PDF 为**文本型**结算单首页；扫描版/加密版可能失败 |

**注意**：`pip install` 要装到**运行 `python scripts/run_pdf_to_excel_service.py` 的那一个解释器**上（可用 `which python` / `python -c "import openpyxl"` 自检）。

**多 Python 混用（macOS / conda 常见）**：若 `pip install -r requirements.txt` 已执行仍报 `No module named 'pdfplumber'`，说明 **pip 对应的 Python ≠ 启动服务的 Python**。请用下面命令对齐（把路径换成 `which python` 的结果）：

```bash
python -c "import sys; print(sys.executable)"
python -m pip install pdfplumber openpyxl pandas
```

启动脚本在缺少依赖时会打印**当前解释器路径**及建议命令；装好后**重启** Uvicorn 再测。

---

## 二、对外交付物（对方在其机器上部署时用）

**打包清单与是否打 zip**：见 **[pdf_to_excel_交付指南.md](./pdf_to_excel_交付指南.md)**。

简要列表：

| 交付项 | 说明 |
|--------|------|
| **交付指南** | `docs/pdf_to_excel_交付指南.md` |
| **本手册** | `docs/pdf_to_excel_service.md`（接口路径、环境变量、curl 示例） |
| **实现代码** | `core/pdf_conversion/`、`scripts/run_pdf_to_excel_service.py`（须保持目录结构） |
| **依赖（仅本服务）** | 根目录 `requirements-pdf-to-xlsx-service.txt`；全项目则用 `requirements.txt` |
| **测试（可选）** | `tests/test_pdf_conversion_http.py` |

对方需自备：Python 3.9+（建议）、可访问的部署机；若加 `PDF_TO_XLSX_API_KEY`，需同步告知密钥用法（`X-Api-Key`）。

---

## 三、部署与启动（通用）

```bash
cd <项目根目录>
pip install -r requirements.txt
python scripts/run_pdf_to_excel_service.py
```

默认监听 `http://0.0.0.0:8765`。可用环境变量：

| 变量 | 含义 |
|------|------|
| `PDF_TO_XLSX_HOST` | 监听地址，默认 `0.0.0.0` |
| `PDF_TO_XLSX_PORT` | 端口，默认 `8765` |
| `PDF_TO_XLSX_API_KEY` | 若设置，请求必须带 `X-Api-Key` 头 |

## 接口说明

### 健康检查

- `GET /health`
- 响应：`{"status":"ok"}`

### PDF 转 Excel

- `POST /v1/pdf-to-xlsx`
- `Content-Type`: `multipart/form-data`
- 表单字段：`file`（二进制，内容为 PDF）
- 成功：`200`，`Content-Type` 为 Excel 格式，body 为 xlsx 二进制；`Content-Disposition` 带下载文件名
- 失败：`400`（空文件、非 PDF）、`401`（API Key 不匹配）、`422`（PDF 无法解析）

### 鉴权（可选）

若服务端配置了 `PDF_TO_XLSX_API_KEY`，则每次请求需增加：

```http
X-Api-Key: <与服务器环境变量一致的值>
```

## 调用示例（curl）

```bash
curl -sS -X POST "http://127.0.0.1:8765/v1/pdf-to-xlsx" \
  -F "file=@/path/to/结算单.pdf" \
  -o "output.xlsx"
```

带 API Key：

```bash
curl -sS -X POST "http://127.0.0.1:8765/v1/pdf-to-xlsx" \
  -H "X-Api-Key: your-secret" \
  -F "file=@/path/to/结算单.pdf" \
  -o "output.xlsx"
```

## 说明与限制

- 解析逻辑与脚本 `scripts/pdf_settlement_to_excel.py`、核心模块 `core/pdf_conversion/settlement_pdf.py` 一致，**仅处理首页**；版式需与浙江电力结算单样本相近，极端扫描件可能需调整规则。
- 交互式 API 文档：服务启动后访问 `http://<host>:<port>/docs`（Swagger UI）。
