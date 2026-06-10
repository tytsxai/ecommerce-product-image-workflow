# 电商商品图 AI 工作流 / E-commerce Product Image Workflow

面向电商团队的开源 AI 商品图生产工作流。

Open-source AI product photography workflow for e-commerce teams.

[![文档站](https://img.shields.io/badge/文档-GitHub%20Pages-0969da?logo=github)](https://tytsxai.github.io/ecommerce-product-image-workflow/)
[![版本](https://img.shields.io/github/v/release/tytsxai/ecommerce-product-image-workflow)](https://github.com/tytsxai/ecommerce-product-image-workflow/releases)
[![许可证](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English README](README.md) · [在线文档](https://tytsxai.github.io/ecommerce-product-image-workflow/) · [快速开始](docs/en/quickstart.md) · [Web 工作台](docs/en/web-workbench.md) · [MVP CLI](docs/en/mvp-cli.md) · [FAQ](docs/en/faq.md) · [llms.txt](llms.txt)

这是一个面向电商运营、内容团队、创意供应商和自动化工程师的开源项目。它提供一套模型无关、可落地的 **AI 商品图生产工作流**：用 CSV 输入表、风格包、提示词模板、质检清单、Python CLI 和本地 Web 工作台，把供应商图和商品资料整理成可生成、可复核、可退回、可导出的商品图片生产包。

English summary: an open-source, model-agnostic workflow and local toolset for e-commerce product image production, supplier image transformation, prompt package generation, QA review, retry, and export.

## 项目事实速览 / At a Glance

| 项目 | 说明 |
| --- | --- |
| 项目类型 | 开源工作流规格 + 本地工具集，服务于 AI-assisted e-commerce product image production |
| 核心用途 | 把 supplier product photos 和商品资料转成 prompt package、可控文字源、QA 记录、可重跑任务和可导出的商品图资产 |
| 适合用户 | 电商运营、内容团队、创意外包、自动化工程师、构建 AI product photography pipeline 的开发者 |
| 当前包含 | Python MVP CLI、CSV/JSON 模板、风格包、提示词生产包、本地 FastAPI + SQLite 后端、React/Vite Web 工作台、QA 审核和 ZIP 导出 |
| 可直接运行的 Provider | `local_mock` 用于离线演示和测试；`generic_http` 用于兼容的图像生成 HTTP API |
| 不包含 | 模型权重、托管 SaaS 生图服务、marketplace 自动发布、法律或商业授权保证 |
| 技术栈 | Python 3.9+、FastAPI、SQLite、Pillow、React、Vite、TypeScript、CSV、JSON、Markdown、Pytest |
| 许可与状态 | MIT；alpha 阶段本地工具，适合验证、扩展和接入生产 Provider 前的参考实现 |

## 解决什么问题

很多电商团队并不是缺少一个 AI 生图模型，而是缺少一套稳定流程：

- 供应商图风格混乱，直接上架缺少品牌感。
- 同一批 SKU 多人处理时，风格、命名、质检口径不一致。
- AI 生成容易改变商品形状、颜色、比例、材质。
- 规格图和说明图里的文字容易乱码、错字、错单位。
- 生成结果缺少 manifest、QA 记录和批次留痕，后续返工成本高。

这个仓库把流程拆成可执行的表单、模板、代码和审核节点，而不是只给一段提示词。

## 适合谁使用

- 跨境电商、独立站、Amazon、Shopify、Shopee、Temu、Etsy 等商品内容团队。
- 需要把 supplier product photos 转成 branded hero images、spec cards、how-to images 的运营团队。
- 负责批量出图、质检、退回、交付的设计或内容外包团队。
- 想把 AI image generation 接入 n8n、Make、Zapier、ComfyUI、自研系统的开发者。

## 核心功能

- **经理输入表 / Manager intake CSV**：商品 ID、英文名称、尺寸、规格、步骤、风格包、供应商图路径。
- **风格包 / Style packs**：复用背景、光线、构图、色彩和负面约束，降低提示词漂移。
- **Prompt 生产包**：为每个商品生成 showcase、spec、how-to 三类图片提示词。
- **可控文字源**：规格图和说明图使用英文 text source，配合本地模板渲染，减少模型乱写文字。
- **QA 质检门**：商品变形、背景过于接近原图、非英文文字、规格错误、步骤含义漂移都可一票退回。
- **批次留痕**：生成 `batch_manifest.json`、每个商品的 `manifest.json`、`qa_review.csv`、source image 引用和可选哈希。
- **本地 Web 工作台**：FastAPI + SQLite + React/Vite，支持创建批次、添加商品、上传源图、选择 Provider、异步生成、审核、重跑和 ZIP 导出。
- **Provider 抽象**：内置 `local_mock`、`generic_http`，并提供 OpenAI Images、Replicate、ComfyUI 集成模板。

## 技术栈

- Python 3.9+
- FastAPI、SQLite、Pillow
- React、Vite、TypeScript
- CSV、JSON、Markdown
- Pytest

## 快速开始

### 方式一：用 CLI 生成商品图生产包

```bash
python3 -m pip install -e .

python3 -m mvp_image_workflow inspect \
  --input examples/products_minimum.csv

python3 -m mvp_image_workflow generate \
  --input examples/products_minimum.csv \
  --out out_mvp \
  --batch-id 2026-05A

python3 -m mvp_image_workflow validate --out out_mvp
```

安装后也可以使用命令别名：

```bash
ecommerce-image-workflow inspect --input examples/products_minimum.csv
```

生成结果包括：

- `batch_manifest.json`：批次级记录。
- `qa_review.csv`：每张预期交付图片一行。
- `operator_runbook.md`：给运营执行和交付用的说明。
- 每个商品自己的 prompts、texts、showcase/spec/howto 目录、source 引用和 `manifest.json`。

如果 CSV 包含 `source_image_paths` 或 `supplier_image_paths`，可以加 `--copy-source-images` 复制本地供应商图并记录哈希。

### 方式二：启动本地 Web 工作台

```bash
python3 -m pip install -e ".[web]"
cd frontend
npm install
npm run build
cd ..
python3 -m ecommerce_product_image_workflow.web
```

默认地址：

```text
http://127.0.0.1:8787
```

如需指定本地数据、上传文件、导出包和 SQLite 的存储位置：

```bash
EPI_WORKFLOW_HOME=/path/to/local/state python3 -m ecommerce_product_image_workflow.web
```

如果只是本地体验，不需要 API Key，Web 工作台里选择 `local_mock` Provider 即可。已有兼容生图接口时，再使用 `generic_http`，它默认期望接口返回 base64 图片字段。

## 典型使用场景

- 供应商图改造电商主图。
- 批量生成商品图 prompt package。
- 为 spec image / how-to image 准备稳定英文文案和渲染源。
- 给 AI 生成商品图建立 QA checklist 和 batch record。
- 在正式接入 n8n、Make、Zapier、ComfyUI 或内部系统前做本地 PoC。

## 限制与注意事项

- 这个仓库不提供模型权重，也不提供托管生图服务。
- CLI 本身不调用图像模型，只生成 prompts、texts、manifest、QA 文件和交付结构。
- Web 工作台可以使用 `local_mock` 或兼容的 `generic_http` Provider；`openai_images`、`replicate`、`comfyui_http` 当前更接近集成模板，需要按你的生产接口扩展或配置。
- 当前 Phase 1 只覆盖图片资产，不覆盖视频、3D、AR 或 marketplace 自动发布。
- 这不是法律意见。模型授权、字体授权、素材授权、平台政策和本地法规仍需自行确认。
- AI 商品图必须经过人工质检。流程能降低风险，但不能保证模型永远保持商品形状、颜色、材质和比例。

## 文档入口

- [Quick Start](docs/en/quickstart.md)
- [Web Workbench](docs/en/web-workbench.md)
- [MVP CLI](docs/en/mvp-cli.md)
- [End-to-End Workflow](docs/en/workflow.md)
- [Quality Gate](docs/en/quality-gate.md)
- [Risk & Compliance](docs/en/compliance.md)
- [FAQ](docs/en/faq.md)
- [中文文档导航](docs/zh-CN/README.md)
- [AI 搜索与 Agent 读取入口 llms.txt](llms.txt)

面向 AI 搜索引擎和 coding agent 的最短事实卡是 [llms.txt](llms.txt)，里面包含项目标准摘要、可执行命令、适用场景、可引用页面和明确限制。

## 搜索关键词

`AI 商品图工作流`、`电商商品图 AI 生成`、`供应商图改造电商主图`、`商品图提示词模板`、`商品图 QA 清单`、`电商主图批量生成`、`AI product photography workflow`、`supplier image to hero image`、`e-commerce product image workflow`、`brand-consistent product images`。

## 许可证

MIT，见 [LICENSE](LICENSE)。
