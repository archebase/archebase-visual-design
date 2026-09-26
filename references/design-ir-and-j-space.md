# 设计中间表示与 J-space 式设计空间

## 目标

把设计 brief、设计规则、视觉案例和评审结果表示为可解释对象，再用 embedding 支持检索和探索。不要把设计知识压缩成一个不可追溯的向量。

## 可解释 IR

每条记录至少保存：`id`、`kind`（brief/rule/case/asset/critique/constraint/concept）、`content_goal`、`visual_claim`、`features`（layout/grid/hierarchy/typography/color/imagery/density/motion/channel）、`relations`（supports/contrasts/requires/conflicts_with/derived_from/validated_by）、适用范围、`source_id`、`locator`、`license`、`evidence_level`、`conditions`、`anti_patterns`、`validation`、`status` 和 `embedding_ref`。向量只是索引引用，不是解释。

## 向量与检索

- brief、规则和图注使用文本 embedding；版式截图、信息图、海报和页面使用多模态 embedding。
- 每次索引记录模型、版本、模态、维度、归一化方式、时间和索引 ID；模型更换时版本化，禁止静默混用。
- 流程：结构化 brief → 硬过滤 VI/渠道/授权/事实范围 → embedding 召回规则、案例和反例 → 按任务、网格、阅读路径、密度、媒介和受众重排 → 输出来源、适用条件、冲突项和验证建议 → 人工方向批准。
- embedding 不能自动批准设计、推断事实或覆盖正式 VI。
- 任何检索候选进入方案前，先使用 `/Users/zhexuany/Books/archebase-design-ir/validate_candidate.py` 检查声明的色彩、字体、Logo、事实、素材权利、无障碍和生产字段；该检查不替代像素级对比度、实际尺寸或人工审核。
- 已有 SVG/PNG 等实际交付物时，再使用 `/Users/zhexuany/Books/archebase-design-ir/inspect_svg.py` 或 `inspect_raster.py` 做文件级检查；文件级检查仍不等同于完整视觉或法律验收。
- 需要一次性验收候选元数据和实际文件时，使用 `/Users/zhexuany/Books/archebase-design-ir/preflight.py`；非零退出即停止交付流程。
- 轴坐标当前是 `proposed seed labels`；使用前需通过本机项目文件 `/Users/zhexuany/Books/archebase-design-ir/JSPACE-CALIBRATION.md` 的独立标注和验证，不能把人工初始值当作客观审美测量。

## J-space

第一版使用人工定义、可复核的对立轴，而不是把 PCA/UMAP 坐标当作设计意义：

- `stable ↔ fluid`：稳定结构 ↔ 受控流动。
- `sparse ↔ dense`：稀疏留白 ↔ 信息密度。
- `abstract ↔ concrete`：抽象概念 ↔ 具体物理证据。
- `static ↔ processual`：静态状态 ↔ 时间/流程表达。
- `literal ↔ interpretive`：直接说明 ↔ 隐喻解释。
- `technical ↔ expressive`：工程说明 ↔ 表达性探索。

轴分数是正负描述的相对相似度，只作导航标签。新增轴必须有定义、正负 anchor、至少 3 个正例、3 个负例、失败案例和人工复核。

## 评估与版权

建立 brief→规则、brief→案例、brief→反例、案例→来源的金标准集，测 Recall@k、硬约束误召回率、来源完整率、人工相关性、跨模态检索质量、品牌漂移率和建议可解释率。每次更换模型都回归测试。向量库保留来源、授权和删除记录；不得发布可替代受版权保护原文的 embedding 集合。