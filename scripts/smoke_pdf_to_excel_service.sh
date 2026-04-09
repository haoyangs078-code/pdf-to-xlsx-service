#!/usr/bin/env bash
# 本地冒烟：需已启动 PDF→Excel 服务（默认 http://127.0.0.1:8765）
# 用法：在项目根目录执行  bash scripts/smoke_pdf_to_excel_service.sh
# 可选：BASE_URL=http://127.0.0.1:9999 bash scripts/smoke_pdf_to_excel_service.sh

set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:8765}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SAMPLE_PDF="${ROOT}/宁波宁能电力销售有限公司2026年03月28日结算单-现货日清分(售电公司).pdf"
OUT="${TMPDIR:-/tmp}/smoke_pdf_to_xlsx_$$.xlsx"

echo "== GET ${BASE_URL}/health"
curl -sS -f "${BASE_URL}/health" | head -c 200
echo ""

if [[ -f "${SAMPLE_PDF}" ]]; then
  echo "== POST ${BASE_URL}/v1/pdf-to-xlsx (sample PDF)"
  HTTP_CODE="$(curl -sS -o "${OUT}" -w "%{http_code}" -X POST "${BASE_URL}/v1/pdf-to-xlsx" \
    -F "file=@${SAMPLE_PDF}")"
  if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "HTTP ${HTTP_CODE}（期望 200）。服务端返回："
    cat "${OUT}"
    echo ""
    echo "常见原因：运行服务的 Python 环境未安装 openpyxl，请在该环境中执行: pip install openpyxl"
    exit 1
  fi
  echo "Wrote: ${OUT}"
  python3 -c "p=open('${OUT}','rb').read(4); exit(0 if p[:2]==b'PK' else 1)" && echo "OK: output looks like xlsx (ZIP PK header)"
else
  echo "SKIP: sample PDF not found at ${SAMPLE_PDF}"
fi

echo "Done."
