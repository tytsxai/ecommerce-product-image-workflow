# 中文文档导航

本项目是一个开源的电商商品图 AI 工作流 / E-commerce Product Image Workflow。它用 CSV 输入、风格包、提示词模板、QA 清单、Python CLI 和本地 Web 工作台，帮助团队把供应商图整理成可生成、可复核、可退回、可交付的商品图片生产流程。

## 推荐阅读顺序

1. [项目 README](https://github.com/tytsxai/ecommerce-product-image-workflow#readme)：中英双语项目定位、技术栈、快速开始和限制说明。
2. [Quick Start](../en/quickstart.md)：最短可执行路径，包含 CLI 和 Web 工作台。
3. [Web Workbench](../en/web-workbench.md)：本地浏览器工作台、Provider 配置、API 和导出说明。
4. [MVP CLI](../en/mvp-cli.md)：CSV 到 prompt/text/manifest 生产包的命令行用法。
5. [Quality Gate](../en/quality-gate.md)：AI 商品图质检规则和退回标签。
6. [FAQ](../en/faq.md)：项目能力边界、模型选择、商业使用和自动化集成问题。

## 仓库内关键材料

- `../../templates/manager_input_form.csv`：经理输入表。
- `../../templates/style_packs.example.json`：风格包示例。
- `../../templates/qa_checklist.csv`：QA 质检清单。
- `../../templates/batch_record.csv`：批次记录表。
- `../../prompts/`：可复用提示词模板。
- `../../examples/products_minimum.csv`：MVP CLI 可直接运行的 CSV 示例。
- `../../llms.txt`：面向 AI 搜索引擎和 Agent 的项目事实卡。

## 中文参考文档

- `reference/`：Phase 1 原始完整参考文档，保留中文经理流程、质检、风险、交付和配置说明。
- [原始参考文档目录](reference/README.md)

## 搜索关键词

AI 商品图工作流、电商商品图 AI 生成、供应商图改造电商主图、商品图提示词模板、电商主图批量生成、规格图说明图生成、商品图 QA 清单、AI product photography workflow、supplier image to hero image、e-commerce product image workflow。

在线文档站：`https://tytsxai.github.io/ecommerce-product-image-workflow/`
