# 设计中间表示与 J-space 式设计空间

## 目标

把设计 brief、设计规则、视觉案例和评审结果表示为可解释对象，再用 embedding 支持检索和探索。不要把设计知识压缩成一个不可追溯的向量。

## Store 定位与证据边界

Design IR store 是品牌事实的**派生消费者**，不是品牌权威：store 的记录、坐标、检索结果都不得作为 VI 证据引用；品牌事实一律回到 `skill-dependencies.json` 锁定的 VI 依赖（GitHub `archebase/archebase-vi-guide`）。store 记录里的 `license` 只是输入元数据，不构成任何授权判定；本 Skill 不维护许可台账。

按以下顺序解析 store 根目录，禁止硬编码任何本机绝对路径：

1. 环境变量 `ARCHEBASE_DESIGN_IR` 指向的目录。
2. 工作区仓库 `archebase-design-workspace` 的 `ir/` 子目录：本 Skill 的 `../archebase-design-workspace/ir`，以及 `$HOME/Books/archebase-design-workspace/ir`。
3. 兼容旧布局：同级目录 `archebase-design-ir`（相对本文件即 `../../archebase-design-ir`）。
4. 从 GitHub `archebase/archebase-design-workspace` clone，按 `skill-dependencies.json` 的 commit 检出，使用其中的 `ir/`（**内部仓库，需访问权限**）。
5. 以上都不可达时停止该路由并报告 `待确认`，不得凭记忆、猜测或另一台机器的路径继续。该路由是本 Skill 的可选依赖：品牌事实、构图/字体/颜色/无障碍方法与其余检查都不依赖 store，无权限时其余工作照常进行。

store 的身份必须可核对：`git -C <store 所在仓库> rev-parse HEAD` 必须等于 `skill-dependencies.json` 中 `design-ir-store` 的 pin；不一致时按 `待确认` 停止，不得用旧缓存当语料。store 是构建产物依赖：索引缺失时先在 `ir/` 下运行 `python3 build_index.py`。

解析成功后，下文提到的工具与数据文件都按 store 相对名引用：`design-ir-schema.yaml`、`build_index.py`、`records.jsonl`、`axes.json`、`query.py`、`jspace.py`、`validate_jspace.py`、`validate_candidate.py`、`inspect_svg.py`、`inspect_raster.py`、`preflight.py`、`JSPACE-CALIBRATION.md`。

## 可解释 IR

每条记录的结构以 store 的 `design-ir-schema.yaml` 为准，可填写的单条记录模板见 [../templates/design-ir.yaml](../templates/design-ir.yaml)。记录保存：`id`、`kind`、`content_goal`、`visual_claim`、`features`（layout/grid/hierarchy/typography/color/imagery/density/motion/channel）、`relations`（supports/contrasts/requires/conflicts_with/derived_from/validated_by）、`scope`、`brand`、`application`、`excludes`、`source`（`source_id`/`locator`/`license`/`evidence_level`）、`conditions`、`anti_patterns`、`validation`、`embedding_ref`、`status`、`created_at`、`updated_at`。`kind` 枚举为 brief/rule/case/asset/critique/constraint/concept，另有 `anti_pattern`（store 已存在该 kind，`jspace.py` 默认排除它）。向量只是索引引用，不是解释。

入索引是另一层结构：`build_index.py` 读 `records.jsonl` 的扁平记录，`records` 表有 12 个 NOT NULL 列——`id`、`kind`、`title`、`text`、`tags_json`、`channel_scope_json`、`status`、`evidence_level`、`source_id`、`locator`、`license`、`hard_constraints_json`。其中 `title`、`text`、`tags`、`channel_scope`、`hard_constraints` 是索引列，不在 schema 中，由记录派生；映射规则写在 [../templates/design-ir.yaml](../templates/design-ir.yaml) 头部。

## 向量与检索

- brief、规则和图注使用文本 embedding；版式截图、信息图、海报和页面使用多模态 embedding。
- 每次索引记录模型、版本、模态、维度、归一化方式、时间和索引 ID；模型更换时版本化，禁止静默混用。
- 流程：结构化 brief → 硬过滤 VI/渠道/授权/事实范围 → embedding 召回规则、案例和反例 → 按任务、网格、阅读路径、密度、媒介和受众重排 → 输出来源、适用条件、冲突项和验证建议 → 人工方向批准。
- embedding 不能自动批准设计、推断事实或覆盖正式 VI。
- 检索运行记录用 [../templates/retrieval-record.json](../templates/retrieval-record.json)；`query.py` 只输出 `query`/`channel`/`results`/`count`，硬拒绝候选被静默丢弃，因此逐候选的采用或淘汰理由必须自己补记。
- 任何检索候选进入方案前，先按 [../templates/candidate-record.json](../templates/candidate-record.json) 填写候选记录，并交给 store 的 `validate_candidate.py` 检查声明的色彩、字体、Logo、事实、素材权利、无障碍和生产字段；该检查不替代像素级对比度、实际尺寸或人工审核。
- 已有 SVG/PNG 等实际交付物时，再用 store 的 `inspect_svg.py` 或 `inspect_raster.py` 做文件级检查；文件级检查仍不等同于完整视觉或法律验收。
- 需要一次性验收候选元数据和实际文件时，使用 store 的 `preflight.py`；非零退出即停止交付流程。
- 轴坐标当前是 `proposed seed labels`；使用前需按 store 的 `JSPACE-CALIBRATION.md` 做独立标注和验证，不能把人工初始值当作客观审美测量。

## J-space

第一版使用人工定义、可复核的对立轴，而不是把 PCA/UMAP 坐标当作设计意义。轴 ID 与方向取自 store 的 `axes.json`，六个轴必须齐全（`validate_jspace.py` 逐条校验，`jspace.py` 拒绝未知轴）：

- `structural_stability`（稳定结构 ↔ 受控流动；负向 `fluid` → 正向 `stable`）
- `density`（稀疏留白 ↔ 信息密度；负向 `sparse` → 正向 `dense`）
- `physical_literalness`（抽象概念 ↔ 具体物理证据；负向 `abstract` → 正向 `concrete`）
- `processuality`（静态状态 ↔ 时间/流程表达；负向 `static` → 正向 `processual`）
- `literalness`（直接说明 ↔ 解释性隐喻；负向 `literal` → 正向 `interpretive`）
- `expressiveness`（工程说明 ↔ 表达性探索；负向 `technical` → 正向 `expressive`）

坐标存在 `axes.json` 的 `coordinates[<record id>]`，不写入记录本身；每个轴的分数是 [-1,1] 内的有限数值，`uncertainty` 与 `evidence` 也按轴各记一个标量或一条说明，不是区间。轴分数是正负描述的相对相似度，只作导航标签。新增轴必须有定义、正负 anchor、至少 3 个正例、3 个负例、失败案例和人工复核。

## 评估与版权

建立 brief→规则、brief→案例、brief→反例、案例→来源的金标准集，测 Recall@k、硬约束误召回率、来源完整率、人工相关性、跨模态检索质量、品牌漂移率和建议可解释率。每次更换模型都回归测试。向量库保留来源与删除记录；不得发布可替代受版权保护原文的 embedding 集合。第三方素材在内部默认按已获授权处理，本 Skill 不维护许可台账；对外发布前由发布方确认授权。
