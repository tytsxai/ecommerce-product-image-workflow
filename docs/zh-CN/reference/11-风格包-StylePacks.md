---
title: 风格包（Style Packs）
topic: 风格包配置结构、示例与禁用项
tags:
  - 主题/AI与智能体
  - 主题/电商
  - 形态/配置
summary: >
  将“背景/构图/光线/色调/道具/禁用项”封装成可选择的风格包，让经理无需写复杂提示词即可稳定产出差异化背景。
created: 2025-12-22
updated: 2025-12-26
stage: draft
visibility: internal
owner: me
ai_include: true
source: ""
---

# 风格包（Style Packs）

## 1) 风格包的目标
- 让经理只做“选择题”：选风格包 → 一键生成全部图片。
- 降低复刻风险：同一风格包也应内置多个背景变体，避免“同一套背景反复套用”。
- 与品类解耦：风格包描述背景与光影，不描述会改变产品形态的内容。

## 2) 配置结构（建议字段）
- `pack_id`：唯一标识（如 `minimal_white`）
- `name`：给经理看的名称
- `scene_type`：studio / indoor / outdoor / lifestyle
- `palette`：主色/辅色（建议与品牌色兼容）
- `lighting`：softbox / daylight / side light / rim light
- `props_allowlist`：可用道具清单
- `props_blocklist`：禁用道具清单
- `composition_rules`：构图规则（留白方向、产品摆放区域）
- `background_variants`：至少 3 个变体（材质/色调/构图不同）
- `negative_rules`：强制避免项（避免让模型改产品）

变体命名建议（便于复盘，不强制）
- `background_variants` 用稳定 ID：如 `mw_v1_purewhite`、`mw_v2_lightgradient`、`mw_v3_papertexture`
- 批次记录建议写入所用变体 ID：见 [19-生成批次记录-经理填写.md](19-生成批次记录-经理填写.md)

## 3) 推荐起步风格包（示例）
### A) `minimal_white`（干净主图/规格图友好）
- scene：studio
- palette：white / light gray / brand accent
- lighting：soft, even
- 背景变体：纯白、浅灰渐变、细微纸纹
- 禁用：强纹理、复杂道具、强反射地面
- negative_rules（示例）："do not change product shape/structure/color; keep logos/patterns unchanged; do not add/remove parts"

### B) `lifestyle_warm`（生活方式场景图）
- scene：indoor lifestyle
- palette：warm neutral（米色/浅木色）
- lighting：warm daylight
- 道具：杯子、书、植物（按品类裁剪）
- 禁用：可引发误导的“功效场景”
- negative_rules（示例）：同上；另加 "avoid hands/people holding the product unless explicitly required"

### C) `premium_dark`（高端暗调）
- scene：studio / premium interior
- palette：charcoal / deep navy + subtle highlight
- lighting：rim light / controlled highlights
- 禁用：过度反光导致产品材质跑偏
- negative_rules（示例）：同上；另加 "avoid mirror-like surfaces that distort edges"

## 4) 与模板联动
- `showcase`：风格包主导背景与道具变化。
- `spec/howto`：风格包提供“简洁背景变体”，文字层由模板渲染保证一致性。

