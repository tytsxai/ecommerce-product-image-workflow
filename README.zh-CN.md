# 电商商品图片生成工作流（Phase 1：图片）

[English README](README.md)

一个面向非技术团队的可落地工作流：把供应商图转为可上架、可品牌化、可复核的图片资产。

## 目标

- 保持产品本体一致（结构/颜色/比例）
- 背景与构图明显不同（避免复刻）
- 文字输出可控（默认图片内文案英文）
- 具备质检、退回、留痕机制

## 仓库内容

- `docs/en/`：英文开源文档入口
- `docs/zh-CN/`：中文说明与原始参考文档
- `templates/`：可直接使用的表单、清单、风格包模板
- `prompts/`：经理可复制的提示词模板
- `examples/`：示例输入

## 快速使用

1. 查看 `docs/en/quickstart.md`（对外开源推荐入口）
2. 填写 `templates/manager_input_form.csv`
3. 选择 `templates/style_packs.example.json` 中的风格包
4. 按 `templates/qa_checklist.csv` 验收
5. 用 `templates/batch_record.csv` 记录批次

## 开源维护建议

- 以模板和流程为主，不提交敏感业务素材
- 所有新增规则都要同步更新 QA 清单与批次记录字段
- 外部贡献优先采用 PR + Issue 模板
