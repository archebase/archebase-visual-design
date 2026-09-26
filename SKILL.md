---
name: archebase-visual-design
description: "为智域基石设计并审查一致、清晰的品牌视觉。品牌依赖固定为 GitHub archebase/archebase-vi-guide；本 Skill 只增加设计书方法、Design IR 和交付流程。"
version: 1.1.0
author: 杨哲轩, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ArcheBase, Graphic-Design, Visual-Design, Brand, VI]
    related_skills: []
---

# 智域基石平面与视觉设计

将智域基石的商业和技术内容转化为精确、可信、清晰、具基础设施感的视觉系统。先解决内容、层级和关系，再处理风格与装饰；结合系统构成、沟通设计、留白与感官克制，但以智域基石 VI 为最高视觉约束。

## When to Use

- 先解析 GitHub 依赖 `https://github.com/archebase/archebase-vi-guide`。当前兼容基线为 tag `v3.5.4`、commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`；本地 clone 只是缓存，不能成为来源身份。本 Skill 不复制、重建或替代该 VI 权威层。
- 为 ArcheBase / 智域基石设计或审查海报、公众号头图、社媒图、报告封面、活动主视觉、信息图、展板或图像生成 brief。
- 把文章、产品能力、研究结论、数据流程转成视觉方案。
- 将现有素材改造成智域基石风格，或判断是否符合 VI。
- 不用于未经批准修改 Logo、增加品牌色，或编造产品能力、客户、数据与行业地位。

## 不可违反的品牌约束

品牌硬约束来自 GitHub `archebase/archebase-vi-guide`。兼容与审计必须记录仓库 URL、tag 和 commit，而不是机器本地路径；若依赖版本变化，先重新运行其 validators/evals，再更新兼容基线。

## 标准流程

### 1. 建立内容契约

确认受众、核心信息、预期行动、媒介、尺寸、文案状态、事实边界和已有素材。信息不全时可用低风险默认值推进，但必须列出假设，绝不补造事实。

完成标准：能写成一句话——“为 `[受众]` 说明 `[核心信息]`，使其产生 `[理解或行动]`。”

### 2. 定义视觉命题

用一句话说明内容如何转为空间关系，例如：“让分散的物理信号沿数据脊柱汇聚为可供智能行动的结构。”“蓝色科技感”“未来感”“高级感”不是视觉命题。

### 3. 排列层级

按首要信息、支撑信息、证据/数据、来源/日期、CTA 排序。移除颜色和图片后，黑白文本版仍必须有清晰阅读顺序。

### 4. 探索结构

默认比较三种方向（工作约定，不是品牌规定）：

- **稳定型**：强网格、基石模块、水平垂直关系。
- **流动型**：数据脊柱、节点、方向和渐进。
- **场域型**：密度、裁切、图底关系和空间深度。

先描述主导关系、网格和阅读路径，不做微装饰。基础构成方法见 [references/composition-methods.md](references/composition-methods.md)；复杂网格、序列和破格判断见 [references/grid-systems.md](references/grid-systems.md)。

### 5. 构建版式与字体系统

依据内容选择单栏、分栏、模块网格、层级网格或复合结构。为主标题、副标题、正文、标签、数据、图注和 CTA 分配固定语义角色；通过字号、字重、位置、间距和色彩建立层级，不靠频繁换字体。需要深度排版决策时读取 [references/typography-and-layout.md](references/typography-and-layout.md)；需要语义、纪律、适切性与长期品牌资产判断时读取 [references/vignelli-principles.md](references/vignelli-principles.md)。

### 6. 应用颜色

先用 `#1E2124` 与 `#FFFFFF` 完成结构，再用 `#0032FF` 建立品牌主导；辅助蓝组织非文本层次；`#46CFFF` 只用于信号、流向、边线或深底重点。每种颜色必须有功能解释。

### 7. 整合图像与图形

优先真实物理设备、环境局部、传感/空间/行动关系、工程标注、可信数据图和品牌几何母题。避免发光大脑、随机电路板、二进制雨、泛化机器人触屏、伪仪表盘、无意义粒子和默认紫蓝赛博渐变。

### 8. 删减与媒介测试

逐项问：是否传递信息、强化层级、建立关系、增强识别？否则删除。随后在实际尺寸、手机缩略图、灰度、最长文案、缺图状态和最终导出文件中检查。

## 输出合同

完整方案使用：

```markdown
## 设计目标
- 受众：
- 核心信息：
- 预期行动：
- 媒介与尺寸：
- 已知约束：
- 明示假设：

## 核心概念
一句话视觉命题。

## 信息层级
1. 首要信息
2. 支撑信息
3. 证据或数据
4. 来源与 CTA

## 构图方案
- 网格：
- 主导视觉：
- 阅读路径：
- 单元与重复：
- 留白策略：
- 变化方式：

## 品牌应用
- 颜色角色：
- 字体角色：
- 品牌母题：
- 明确禁止项：

## 图像或图形方向
- 主体：
- 视角与场景：
- 图形处理：
- 应避免的俗套：

## 生产规格
- 尺寸与比例：
- 导出格式：
- 渠道限制：
- 可访问性检查：

## 自检结果
- 内容正确性：
- 信息层级：
- 品牌一致性：
- 最终尺寸与对比度：
```

快速建议至少保留：核心概念、层级、颜色角色、字体、构图和禁止项。

## 质量门

交付前逐项通过 [references/critique-checklist.md](references/critique-checklist.md)：

1. **事实正确**：无编造，无伪数据，无未经确认的技术架构暗示。
2. **构图清晰**：三秒内识别主题；只有一个主导视觉；阅读路径连续；对齐可解释。
3. **品牌一致**：精确色值和字体角色；无橙色；至少体现基础、秩序、坐标、数据连接或受控流动之一。
4. **生产可靠**：实际尺寸可读；关键意义不只靠颜色；图像裁切、导出规格和渠道兼容已验证。

规则冲突时优先级：事实与用户内容 → 可读性/渠道 → 品牌硬约束 → 信息层级 → 构图 → 风格 → 装饰。

## 渠道路由

- 微信公众号文章与长图：读取 [references/channel-wechat.md](references/channel-wechat.md)。
- 图像生成：使用 [templates/image-generation-brief.md](templates/image-generation-brief.md)，最终文字尽量在版式阶段添加。
- 新项目启动：使用 [templates/design-brief.md](templates/design-brief.md)。
- 交付制作规范：使用 [templates/visual-spec.md](templates/visual-spec.md)，印刷或多格式交付同时读取 [references/production-preflight.md](references/production-preflight.md)。
- 团队训练、方案探索与评议：读取 [references/exercises-and-critique.md](references/exercises-and-critique.md)。
- 正文、报告、网页和信息密集版式的可读性判断：读取 [references/legibility.md](references/legibility.md)。
- 图像、照片、图示、数据图和图文整合：读取 [references/image-and-information-design.md](references/image-and-information-design.md)。
- 色彩感知、媒介转换和色彩测试：读取 [references/color-theory.md](references/color-theory.md)。
- 无障碍与辅助技术交付：读取 [references/accessibility.md](references/accessibility.md)。
- 记录设计决策与验证链：使用 [templates/decision-trace.md](templates/decision-trace.md)。
- 复杂项目的 Design IR、案例检索和设计空间探索：读取 [references/design-ir-and-j-space.md](references/design-ir-and-j-space.md)，使用 [templates/design-ir.yaml](templates/design-ir.yaml)；embedding 只提供候选，不改变硬约束。
- 品牌依赖与版本锁定：读取 `skill-dependencies.json`；必须使用 GitHub `archebase/archebase-vi-guide` 的锁定 tag/commit，不复制上游 Skill。
- 中间表示、案例检索和设计空间探索：读取 [references/design-ir-and-j-space.md](references/design-ir-and-j-space.md)，并使用 [templates/design-ir.yaml](templates/design-ir.yaml)。

## Verification

交付必须包含可检查的尺寸、颜色、字体角色、层级与导出格式。若生成实际图片、PDF、PPT 或网页，应在目标尺寸打开检查，并明确记录质量门结果；仅写“符合 VI”不算验证。每项重要视觉选择还应能回溯到内容目标、规则来源、适用条件和验证结果。
