---
name: archebase-visual-design
description: "ArcheBase/智域基石 海报、头图、社媒、信息图、报告封面的设计方法与评审；含参考图保真与佩戴几何；品牌事实以vi-guide为准；构图、网格、字体层级、色彩角色、可读性、无障碍、生产检查、Design IR。本 Skill 只做设计方法层、不复制上游资产。"
license: Proprietary
platforms: [macos, linux]
compatibility: "需要文件系统型 Skill loader；Python 3 运行 evals 脚本；可选 rsvg-convert/librsvg 校验 Logo 渲染；Design IR store 由环境变量 ARCHEBASE_DESIGN_IR、同级目录或按 pin clone GitHub archebase/archebase-design-ir 解析，身份不可核对时按待确认停止相关路由。"
metadata:
  version: 1.2.0
  author: 杨哲轩, Hermes Agent
  hermes:
    tags: [ArcheBase, Graphic-Design, Visual-Design, Brand, VI]
    related_skills: [archebase-vi-guide, archebase-wechat-editor]
---

# 智域基石平面与视觉设计

将智域基石的商业和技术内容转化为精确、可信、清晰、具基础设施感的视觉系统。先解决内容、层级和关系，再处理风格与装饰；结合系统构成、沟通设计、留白与感官克制，但以智域基石 VI 为最高视觉约束。

## Dependency contract

- `archebase-vi-guide` is the required base skill for ArcheBase-branded work; this skill is an optional design-method companion, not a replacement.
- Minimum complete installation: `archebase-vi-guide`. Recommended installation for posters, covers, infographics and visual design critique: install both skills.
- When both are available, load `archebase-vi-guide` first. It selects the mode and route, owns brand facts, official assets, Guide evidence, channel rules and the final release verdict. This skill then handles content contracts, visual propositions, hierarchy, composition, grid, color application, legibility and design critique.
- If `archebase-vi-guide` is missing or its pinned identity cannot be verified, block the ArcheBase brand route. Do not invent or reconstruct brand facts, colors, typography, Logo choices or VI approval from memory, local files or this skill.
- If the user explicitly requests non-branded design, this skill may continue as a general design-method exercise, but it must not use ArcheBase assets or claim VI compliance.

## When to Use

- For ArcheBase work, use this skill after `archebase-vi-guide` has selected the mode and route.
- Use it for posters, WeChat covers, social graphics, report covers, event key visuals, infographics, image-generation briefs and visual design reviews when composition and information design require method-layer support.
- Do not use it as the sole authority for official colors, Logo assets, Guide page evidence, channel hard rules or release decisions.
- Before design, confirm the upstream identity: tag `v3.5.4`, commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`. Resolve the GitHub dependency and verify `git rev-parse HEAD`; a local checkout is only a cache.
- For official color, typography, Logo or Guide-page questions, route to `archebase-vi-guide` instead of answering from this skill.

## 不可违反的品牌约束

品牌硬约束来自 GitHub `archebase/archebase-vi-guide`。兼容与审计必须记录仓库 URL、tag 和 commit，而不是机器本地路径。以下为硬边界，任一不通过即停止交付：

- 公开名称只用 `ArcheBase`；`archebase` 仅用于 GitHub 组织、仓库和技术路径；不得引入未批准的 lockup 或域名命名（上游 `references/asset-governance.md`）。
- Logo 只用 `智域基石 Logo V2` 交付的资产，不得重绘、重新配色、拉伸或加效果；圆形或可能被圆形裁切的表面使用 `方圆通用` 变体，不得由 `方形` 缩放或遮罩生成；渐变 Logo 必须用 `rsvg-convert`/浏览器渲染或直接使用捆绑 PNG，不得使用 ImageMagick 内部 SVG 渲染器（上游 `references/logo-asset-resolver.md`）。
- 品牌色只有上游 `tokens/archebase.tokens.json` 的五个 token；不得新增品牌色。白色/浅色表面是应用默认，不是品牌 token。
- 不得编造产品能力、客户、数据、指标、行业地位或技术架构，也不得使用未经确认的公开宣称。
- 客户数据与个人隐私未确认时不得对外交付；第三方素材在内部默认按已获授权处理，本 Skill 不维护许可台账；对外发布前由发布方确认授权。
- 版本漂移处理：依赖 tag/commit 变化后，先运行上游 `scripts/` 下九个确定性校验器（`validate_logo_bundle.py`、`validate_asset_integrity.py`、`validate_guide_evidence.py`、`validate_guide_pages.py`、`validate_modes.py`、`validate_tokens.py`、`validate_asset_reference.py`、`check_release_report.py`、`check_doc_links.py`）以及本 Skill 的 `evals/check_brand_facts.py`，全部通过后再更新兼容基线；上游 `evals/evals.json` 没有 runner，不要把它当作可执行套件。

## 标准流程

### 0. 选择方法边界

涉及引用方法、跨渠道系统、创意偏离或 ArcheBase 调性判断时，先读取 [references/method-fit.md](references/method-fit.md)。涉及官方 VI PDF 的视觉判断、页面证据转译或 `vi-guide` 与本 Skill 的协作时，同时读取 [references/vi-method-fit.md](references/vi-method-fit.md)。这些文件只筛选和转译设计方法，不覆盖 `archebase-vi-guide` 的品牌事实、官方资产、渠道硬规则或发布 verdict。

### 1. 建立内容契约

确认受众、核心信息、预期行动、媒介、尺寸、文案状态、事实边界和已有素材。信息不全时可用低风险默认值推进，但必须列出假设，绝不补造事实。

完成标准：能写成一句话——“为 `[受众]` 说明 `[核心信息]`，使其产生 `[理解或行动]`。”

### 2. 定义视觉命题

用一句话说明内容如何转为空间关系，例如：“让分散的物理信号沿数据脊柱汇聚为可供智能行动的结构。”“蓝色科技感”“未来感”“高级感”不是视觉命题。

### 3. 排列层级

按首要信息、支撑信息、证据/数据、来源/日期、CTA 排序。某一层不适用时写 `N/A` 并注明由哪一层承担该功能（例如封面无 CTA 时，入口由主标题承担），不得留空。移除颜色和图片后，黑白文本版仍必须有清晰阅读顺序。

### 4. 探索结构

默认比较三种方向（工作约定，不是品牌规定）：

- **稳定型**：强网格、基石模块、水平垂直关系。
- **流动型**：数据脊柱、节点、方向和渐进。
- **场域型**：密度、裁切、图底关系和空间深度。

先描述主导关系、网格和阅读路径，不做微装饰。基础构成方法见 [references/composition-methods.md](references/composition-methods.md)；复杂网格、序列和破格判断见 [references/grid-systems.md](references/grid-systems.md)。

### 5. 构建版式与字体系统

依据内容选择单栏、分栏、模块网格、层级网格或复合结构。为主标题、副标题、正文、标签、数据、图注和 CTA 分配固定语义角色；通过字号、字重、位置、间距和色彩建立层级，不靠频繁换字体。需要深度排版决策时读取 [references/typography-and-layout.md](references/typography-and-layout.md)；需要语义、纪律、适切性与长期品牌资产判断时读取 [references/vignelli-principles.md](references/vignelli-principles.md)。

### 6. 应用颜色

颜色事实、色值、比例和语义角色以 `archebase-vi-guide` 为准。模式决定颜色自由度：

- `strict`：只使用上游已批准的五个品牌 token；不新增品牌色。
- `guided`：默认使用品牌 token；任何非 token 颜色都必须标为渠道/活动扩展色，并记录偏离理由。
- `creative`：允许为活动或渠道使用扩展色，但不得称为官方品牌色，不得修改官方 Logo，并需由 `archebase-vi-guide` 执行对应模式的发布门禁。
- `off`：不执行 ArcheBase 品牌色规则，也不得宣称 VI 合规。

五个品牌 token 的色值、角色、比例与中性级完整定义见 [references/brand-system.md](references/brand-system.md)（上游 `tokens/archebase.tokens.json`；Guide p.28，evidence `color.ratio`）：`AB_BLUE_1 #0032FF` 主导结构，`AB_BLUE_2 #7172FA` 支撑层次，`AB_BLUE_3 #619AFD` 次级数据层，`AB_BLUE_4 #46CFFF` 信号/流向/深底重点，`AB_CHARCOAL #1E2124` 中性深色与深色场。先用中性深色与白色表面完成结构，再用主品牌蓝建立主导；每种颜色必须有功能解释。白色/浅色表面是应用默认，不是品牌 token。

### 7. 整合图像与图形

优先真实物理设备、环境局部、传感/空间/行动关系、工程标注、可信数据图和品牌几何母题。避免发光大脑、随机电路板、二进制雨、泛化机器人触屏、伪仪表盘、无意义粒子和默认紫蓝赛博渐变。

当题目要求把**真实器件**（设备、穿戴件、工装）放进人或环境中且不得重绘时，先按 [references/spatial-fidelity.md](references/spatial-fidelity.md) 建立参考契约与几何不变式（一张参考图一个角色、不可变特征、不得复现项、姿态前提、遮挡策略），用 [templates/spatial-fidelity-spec.json](templates/spatial-fidelity-spec.json) 登记并过 Gate G。姿态与几何矛盾时改姿态，不改措辞；不得为展示部件而旋转、抬起或放大器件，也不得把生成的品牌字标当作印刷终稿。

### 8. 删减与媒介测试

逐项问：是否传递信息、强化层级、建立关系、增强识别？否则删除。随后按以下默认值检查（本 Skill 工作默认值，渠道或供应商规范优先）：

- **实际尺寸**：按最终交付尺寸与观看距离检查；以视觉角 ≥ 0.2° 作为检查起点而非标准（来源见 [references/legibility.md](references/legibility.md)，其中明确它不是推荐标准）；手持 40cm、桌面 60cm、展板按实际距离换算，换算公式 `所需毫米 ≈ 2 × 距离 × tan(0.1°)`。
- **缩略图**：短边 ≥ 320px 时主题与唯一主导视觉仍可辨认；正文级小字不可辨可以接受，主导视觉或主题不可辨则不通过。
- **灰度**：去掉颜色后层级仍成立。相邻的**不同明度层级** 8-bit 明度差 ≥ 20（同一颜色只靠字号/字重区分层级时不适用此条，改判尺寸差 ≥ 1.3× 且在灰度下仍可分辨）；结构线与底色的明度差 ≥ 8，否则该结构在灰度下等于消失。8-bit 明度按 Rec.709 luma 计算，须在说明里写明换算口径。
- **最长文案**：按已给文案字符数 ×1.5 或渠道提供的最长变体（取更严者）重排，不得溢出、不得覆盖关键对象、不得触发非预期换行。
- **缺图状态**：去掉图片后版面仍成立——不得留空框、占位灰块或塌陷的间距。
- **印刷**：出血、安全区、最小字号与最小线宽见 [references/production-preflight.md](references/production-preflight.md) 的默认值，供应商规范优先。

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

## VI 协作状态
- VI 模式：
- VI 路由：
- 已采用的官方证据：
- 由 vi-guide 保留的待确认事项：
- 本方案的设计方法判断：
- 是否存在有意偏离：

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
- 参考角色与不可变特征：
- 空间不变式与复核位置：
- 姿态前提：
- 遮挡策略：

## 生产规格
- 尺寸与比例：
- 导出格式：
- 渠道限制：
- 可访问性检查：

## 自检结果
- 内容正确性：
- 信息层级：
- 品牌一致性：
- 参考保真与空间自洽：
```

快速建议至少保留：核心概念、层级、颜色角色、字体、构图和禁止项。

## 发布责任

- 本 Skill 输出设计方法与设计 QA；`archebase-vi-guide` 输出官方品牌证据、资产选择、渠道硬规则、claims/rights/export QA 与最终品牌发布 verdict。
- 两个 Skill 同时可用时，先由 `archebase-vi-guide` 选择 mode 和 route，再由本 Skill 进行方法层设计；制作和渲染后回到 `archebase-vi-guide` 过最终门禁。
- 本 Skill 不单独输出“VI 合规”或“可发布”结论。

## 质量门

交付前逐项通过 [references/critique-checklist.md](references/critique-checklist.md)（其 Gate A–G 与本处 1–7 一一对应，两份都必须通过）：

1. **事实正确**：无编造，无伪数据，无未经确认的技术架构暗示。
2. **构图清晰**：三秒内识别主题；只有一个主导视觉；阅读路径连续；对齐可解释。
3. **品牌一致**：使用当前模式允许的精确色值和字体角色；在 `strict`/`guided` 模式下检查适合内容的本 Skill 自定母题，`creative` 模式允许记录后的有意偏离；官方品牌事实与资产规则以 `archebase-vi-guide` 为准。
4. **生产可靠**：实际尺寸可读；关键意义不只靠颜色；图像裁切、导出规格和渠道兼容已验证。
5. **无障碍**：按项目声明并记录的 WCAG 版本与等级实测对比度；语义结构、替代文本、字幕，且不只用颜色编码关键含义。
6. **来源与素材记录**：每个素材与检索候选都有来源、用途和采用/淘汰理由；无法追溯来源的素材未进入交付。
7. **参考保真与空间自洽**：题目含真实器件参考图时适用（否则记 `N/A`）——器件未被重绘、简化或替换；每条几何不变式都有复核位置与提示词对应句且状态为 `pass`；姿态与不变式自洽；遮挡按已声明策略允许；生成像素重建的品牌字标未作为印刷终稿（见 [references/spatial-fidelity.md](references/spatial-fidelity.md)）。

规则冲突时先过 gate 再做偏好取舍。Gate（任一不通过即停止交付，彼此不分先后）：①事实与用户内容（含参考图保真与空间自洽；器件被重绘或几何不自洽一并计入本条）②品牌硬边界（Logo 完整性、公开名称、隐私与客户数据、禁用项）③可读性/渠道能力/无障碍。Gate 全部通过后，取舍顺序为：信息层级 → 构图与网格 → 品牌视觉偏好（色彩角色、字体角色、母题）→ 风格 → 装饰。

## 渠道路由

- 微信公众号文章与长图：读取 [references/channel-wechat.md](references/channel-wechat.md)。
- 图像生成：使用 [templates/image-generation-brief.md](templates/image-generation-brief.md)，最终文字尽量在版式阶段添加。
- 新项目启动：使用 [templates/design-brief.md](templates/design-brief.md)。
- 交付制作规范：使用 [templates/visual-spec.md](templates/visual-spec.md)，印刷或多格式交付同时读取 [references/production-preflight.md](references/production-preflight.md)。
- 团队训练、方案探索与评议：读取 [references/exercises-and-critique.md](references/exercises-and-critique.md)。
- 正文、报告、网页和信息密集版式的可读性判断：读取 [references/legibility.md](references/legibility.md)。
- 图像、照片、图示、数据图和图文整合：读取 [references/image-and-information-design.md](references/image-and-information-design.md)。
- 参考图保真与佩戴几何（器件不得重绘、佩戴与接触关系必须可信、需要多轮迭代）：读取 [references/spatial-fidelity.md](references/spatial-fidelity.md)，并用 [templates/spatial-fidelity-spec.json](templates/spatial-fidelity-spec.json) 登记规格。
- 色彩感知、媒介转换和色彩测试：读取 [references/color-theory.md](references/color-theory.md)。
- 无障碍与辅助技术交付：读取 [references/accessibility.md](references/accessibility.md)。
- 品牌色、字体、Logo 角色与母题定义：读取 [references/brand-system.md](references/brand-system.md)（品牌事实的唯一重述处）。
- VI Guide PDF 视觉判断与双 Skill 协作：读取 [references/vi-method-fit.md](references/vi-method-fit.md)；它是方法转译层，不是第二个品牌权威。
- 设计方法反刍与一般方法适配：读取 [references/method-fit.md](references/method-fit.md)；当需要判断引用方法是否适合 ArcheBase 调性、跨渠道系统或创意偏离边界时，必须先读此文件。
- 来源与不可推断边界：读取 [references/source-boundaries.md](references/source-boundaries.md)；素材只记录来源与用途，不在此维护许可台账。
- 检索候选记录：使用 [templates/retrieval-record.json](templates/retrieval-record.json)；交付前按 [templates/candidate-record.json](templates/candidate-record.json) 记录候选并交给 `validate_candidate.py`。
- 记录设计决策与验证链：使用 [templates/decision-trace.md](templates/decision-trace.md)。
- 复杂项目的 Design IR、案例检索和设计空间探索：读取 [references/design-ir-and-j-space.md](references/design-ir-and-j-space.md)，使用 [templates/design-ir.yaml](templates/design-ir.yaml)；embedding 只提供候选，不改变硬约束。Store 身份：内部仓库 `https://github.com/archebase/archebase-design-workspace` 的 `ir/`（需访问权限；无权限时该路由按 `待确认` 停止，其余工作不受影响）（pin 见 `skill-dependencies.json` 的 `design-ir-store`，不在本文重复）；解析顺序为环境变量 `ARCHEBASE_DESIGN_IR` → 工作区 `archebase-design-workspace/ir` → 兼容旧布局 `archebase-design-ir` → 按 pin clone；先建索引（`ir/build_index.py`），身份不可核对时停止该路由并记 `待确认`。
- 品牌依赖与版本锁定：读取 `skill-dependencies.json`；必须使用 GitHub `archebase/archebase-vi-guide` 的锁定 tag/commit，不复制上游 Skill。
- 评估本设计方法 Skill 是否改善结果：入口与指标口径见 [evals/README.md](evals/README.md)，运行 `python3 evals/run_visual_design_benchmark.py` 与 `python3 evals/check_brand_facts.py`；[evals/visual-guide-ab-benchmark.md](evals/visual-guide-ab-benchmark.md) 是尚未执行的 A/B 协议，不得当作已有结果或效果证明。

## Verification

交付必须包含可检查的尺寸、颜色、字体角色、层级与导出格式。若生成实际图片、PDF、PPT 或网页，应在目标尺寸打开检查，并明确记录质量门结果；仅写“符合 VI”不算验证。每项重要视觉选择还应能回溯到内容目标、规则来源、适用条件和验证结果。

可运行的自检：`python3 evals/check_brand_facts.py` 校验本 Skill 重述的品牌事实与上游一致（含五色 token、比例、中性级、字体、公开名称），`python3 evals/check_routing.py` 校验路由用例与 `description` 索引一致，`python3 evals/check_spatial_spec.py --spec <spec.json>` 校验参考图保真与佩戴几何规格（`--self-test` 用内置正反例证明该检查可失败），`python3 evals/run_visual_design_benchmark.py` 跑检索/设计空间回归。它们都读 `ARCHEBASE_VI_GUIDE` / `ARCHEBASE_DESIGN_IR` 或同级目录，缺失时明确报 `待确认` 而不是静默通过。
