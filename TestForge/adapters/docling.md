# Docling 适配

## 用途

把 PDF/DOCX/PPTX/XLSX/图片解析成结构化 Markdown/JSON，保留标题、表格、阅读顺序。适合 PRD、合同、规范、标准表格。

## 安装

```bash
pip install docling
# 或使用服务端
pip install docling-serve
docling-serve run --host 0.0.0.0 --port 5001
```

## 在 TestForge 中启用

1. 安装 Docling。
2. 在 `testforge.config.json` 中把 PDF/DOCX 加入 `inputs.docs`，例如：
   ```json
   "docs": ["requirements/**/*.pdf", "requirements/**/*.docx"]
   ```
3. 运行：
   ```bash
   python testforge/testforge.py pack
   ```
   `extract_text()` 会自动优先使用 Docling；失败再回退 pypdf/python-docx。

## 推荐做法

- 解析后按标题/表格切块，不要固定长度硬切。
- 保留 `source_refs`（文件名 + 标题/表格 ID）。
- 对关键表格做人工抽检；合并单元格/跨页表格仍可能出错。
- 中文扫描件可对比 MinerU；Docling 的 MIT 许可更适合商用。

## 输出

- `.testforge/context/context.json` 中 `extractor: "docling"` 的条目。
- `context.md` 中保留 Markdown 表格。
