# PDF 转 Excel 服务 — 交付与打包说明

本文说明：**如何把「PDF 结算单 → xlsx」HTTP 服务交给对方部署**，以及**你是否需要打压缩包、包里放什么**。

更细的接口说明、自测步骤见同目录：**[pdf_to_excel_service.md](./pdf_to_excel_service.md)**。

---

## 对方拿到以后要做什么（最短路径）

1. 解压到任意目录（见下文「目录结构」）。
2. 进入**包含 `core` 与 `scripts` 的那一层**（即项目根目录）。
3. 创建虚拟环境或 conda，安装依赖：
   ```bash
   python -m pip install -r requirements-pdf-to-xlsx-service.txt
   ```
4. 启动服务：
   ```bash
   python scripts/run_pdf_to_excel_service.py
   ```
5. 浏览器打开 **http://127.0.0.1:8765/docs** 调试，或用 `curl`（见 `pdf_to_excel_service.md`）。

**注意**：必须在**项目根目录**执行 `python scripts/...`，以便 `import core.pdf_conversion` 能解析到本地的 `core` 包。

---

## 你应该怎么发给对方

### 方式 A：推荐 — 给 Git 仓库（或整仓 zip）

若对方能访问你们的代码仓库：**直接给仓库地址**，对方 `git clone` 后按「最短路径」操作即可。  
这样不会漏文件，也方便你们后续更新。

若不能访问 Git：**把整个 `trading_workflow_agent` 工程打成 zip** 发过去也可以（体积较大，但最省事）。

### 方式 B：精简压缩包（只含本服务相关代码）

若对方**不能**收整仓，可打一个**最小包**，需保持 **Python 包路径**不变，建议包含：

| 路径 | 说明 |
|------|------|
| `core/__init__.py` | 包标识 |
| `core/pdf_conversion/__init__.py` |  |
| `core/pdf_conversion/settlement_pdf.py` | PDF 解析与写 xlsx |
| `core/pdf_conversion/http_service.py` | FastAPI 路由 |
| `scripts/run_pdf_to_excel_service.py` | 启动入口 |
| `scripts/smoke_pdf_to_excel_service.sh` | 可选，本地冒烟 |
| `tests/test_pdf_conversion_http.py` | 可选，对方可跑单测 |
| `requirements-pdf-to-xlsx-service.txt` | **精简依赖列表**（根目录） |
| `docs/pdf_to_excel_service.md` | 接口与运维说明 |
| `docs/pdf_to_excel_交付指南.md` | 本文件 |

**不要**只发「几个孤立的 `.py`」而删掉 `core/` 目录结构，否则 `from core.pdf_conversion...` 会导入失败。

在 macOS / Linux 上从**仓库根目录**打包示例：

```bash
cd /path/to/trading_workflow_agent

zip -r pdf-to-xlsx-service-minimal.zip \
  core/__init__.py \
  core/pdf_conversion \
  scripts/run_pdf_to_excel_service.py \
  scripts/smoke_pdf_to_excel_service.sh \
  tests/test_pdf_conversion_http.py \
  requirements-pdf-to-xlsx-service.txt \
  docs/pdf_to_excel_service.md \
  docs/pdf_to_excel_交付指南.md
```

对方解压后目录应类似：

```text
某文件夹/
  core/
    __init__.py
    pdf_conversion/
      ...
  scripts/
    run_pdf_to_excel_service.py
    ...
  requirements-pdf-to-xlsx-service.txt
  docs/
    ...
```

在 **`某文件夹`** 下执行 `python scripts/run_pdf_to_excel_service.py`。

---

## 压缩包里一般要不要带 `.txt`？

- **`requirements-pdf-to-xlsx-service.txt`（推荐）**：只含本服务依赖，安装快、冲突少。  
- **完整 `requirements.txt`**：若对方要跑整个 trading 项目再带上；**仅部署 PDF 服务不必强带**。

不必单独再写一份「说明 txt」：用 **`docs/pdf_to_excel_service.md` + 本 `交付指南.md`** 即可；若对方只收 Word，可自行把这两份 md 转成 PDF/Word。

---

## 接口「网站」怎么用

- 服务本质是 **HTTP API**，不是传统门户网站。  
- 浏览器访问 **http://&lt;主机&gt;:8765/docs** 可查看文档并 **Try it out** 上传 PDF。  
- 生产对接常用：**curl**、对方后端 **HTTP 客户端**、或 **Python requests**（示例见 `pdf_to_excel_service.md`）。

---

## 可选：安全与环境变量

| 变量 | 含义 |
|------|------|
| `PDF_TO_XLSX_HOST` / `PDF_TO_XLSX_PORT` | 监听地址与端口 |
| `PDF_TO_XLSX_API_KEY` | 若设置，请求需带请求头 `X-Api-Key` |

对方若部署在公网，建议配置 API Key 并配合防火墙 / 反向代理。

---

## 小结

| 问题 | 建议 |
|------|------|
| 要不要压缩包？ | **要**就给「整仓 zip」或上文「精简 zip」；**或**只给 Git 地址。 |
| 包里必须有 md 吗？ | **建议带** `docs/pdf_to_excel_service.md` 与本 `交付指南.md`。 |
| 依赖用哪个文件？ | 仅本服务：**`requirements-pdf-to-xlsx-service.txt`**。 |
| 只发 py 脚本够不够？ | **不够**，必须保留 **`core/pdf_conversion/` 包结构**。 |
