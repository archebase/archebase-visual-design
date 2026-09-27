# Visual Guide A/B Benchmark

**状态：协议已有可运行 harness，但结果仍然缺失。** 本文件定义方法，案例在 [benchmark-cases.json](benchmark-cases.json)，
harness 是 [run_ab_benchmark.py](run_ab_benchmark.py)。

harness 现在可以做三件事：**准备运行**（`--plan`）、**按协议校验结果目录**（`--validate`）、
**汇总人工评分**（`--score`）。它**不产生任何输出、不调用模型、不联网、不写回本 Skill 或上游**，
也**没有任何实测分数**：只有人（或另一个 harness）按 `--plan` 生成的清单跑完 30 次运行、
把结果回填到 `runs/<run_id>.json`、再由评审者填完盲评分表之后，才可能存在可引用的数字。

因此：**不得把本文件、harness 或 `--plan` 的产物当作“加入 VI 依赖会改善 ArcheBase 视觉设计结果”的证明。**
`--score` 的输出只是对回填数据的算术与区间，不是效果证据；判定行也只在 CI 排除可忽略效应时才说“本样本内更优”。

## Harness：三个模式

```bash
# 1) 准备运行：写清单、逐次渲染的提示词、盲评分表、盲映射
python3 evals/run_ab_benchmark.py --plan --out /tmp/ab-smoke

# 2) 校验结果目录：必填字段、单一基线、逐案配对、多图规则、盲表/盲映射一致性
python3 evals/run_ab_benchmark.py --validate /tmp/ab-smoke

# 3) 汇总评分：逐案与汇总均值、bootstrap 区间、主判据判定
python3 evals/run_ab_benchmark.py --score /tmp/ab-smoke/scoring-sheet.csv
```

常用覆盖参数：`--cases <文件>`、`--upstream <VI Guide 目录>`、`--seed <整数>`、`--repetitions <n>`、
`--model-id/--model-version`、`--resamples <n>`、`--blind-map <文件>`、`--force`。

### 退出码（`--help` 的 epilog 同步列出）

| 退出码 | 含义 | 出现在 |
|---|---|---|
| 0 | 成功：清单已生成 / 校验全过 / 评分已输出（判定为“证据不足”仍是 0，判定是结果不是失败） | 全部模式 |
| 1 | 违规或拒绝 | `--plan` 目标目录已有 `manifest.json` 且未加 `--force`；上游 HEAD 与锁定 commit 不一致；`--validate` 协议违规；`--score` 评分表非法 |
| 2 | 前置条件不可用 | 案例文件缺失/非法 JSON、缺 `--out`、校验目录或 `manifest.json` 缺失、评分表或盲映射缺失 |
| 3 | 清单有效但结果尚未产生（`runs/<run_id>.json` 未全部就位） | `--validate` 专用 |

### 写盘范围

`--plan` 只在 `--out` 内写 4 类产物；`--validate` 与 `--score` **不写任何文件**。
上游仓库、本 Skill、Design IR store 全程只读。路径解析不含机器绝对路径默认值：
上游 VI Guide 按 `--upstream` → `ARCHEBASE_VI_GUIDE` → Skill 目录/上级/上上级 → `$HOME` → `$HOME/Books` 下的
`archebase-vi-guide` 依次解析；解析不到时 `--plan` 仍会生成清单，但把上游标为未解析、条件 B 的资产指纹留占位符。
`--plan` 若解析到上游且其 HEAD 与锁定 commit 不一致，直接以退出码 1 拒绝（条件 B 必须加载锁定版本）。

### 确定性

同一输入 + 同一 `--seed` 下，`--plan` 的全部产物与 `--score` 的全部输出逐字节可复现（含 bootstrap 区间）。

## 结果目录布局

`--plan` 产出：

```text
<out>/manifest.json        运行清单（含上游解析结果、seed、每次运行的配对字段）
<out>/prompts/<run_id>.txt 每次运行的渲染提示词（条件横幅 + 任务正文）
<out>/scoring-sheet.csv    盲评分表（只出现 X/Y，不含条件映射）
<out>/blind-map.json       盲映射（sheet_row_id / run_id → 真实条件；不得交给评审者）
```

运行完成后，每次运行的产物回填到 `<out>/runs/<run_id>.json`。`run_id` 形如 `<case_id>__<A|B>__r<次数>`；
`--validate` 只认这个路径。结果文件必须包含
`raw_output`、`structured_score`、`reviewer_id`、`review_notes`、`run_timestamp`，
并且其 `case_id`、`condition`、`prompt_hash` 必须与清单一致（不一致判 `result_manifest_mismatch`）。

## 盲评

评分表按 **运行** 一行，但只暴露 `sheet_row_id`（如 `row-0001`）、`case_id`、`repetition`、盲标签 `X`/`Y` 与 `pair_anchor`；
A/B 到 X/Y 的映射由 `--seed` 随机决定，只写在 `blind-map.json`。
每个案例的偏好写在 `pair_anchor=1` 的那一行（该案第 1 次重复的 X 行），取值
`X`、`Y` 或 `no_meaningful_difference`；同案多行写了不一致的偏好会被报为 `conflicts`。

## Conditions

- **A — baseline（单一基线）：** 同一模型、提示、文件与工具；不加载 `archebase/archebase-vi-guide`，也不加载任何 ArcheBase 专用视觉 Skill。
- **B — VI-guided：** 与 A 完全相同的模型、提示、文件与工具；额外加载锁定的上游 VI Skill：tag `v3.5.4`，commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`。

提示词由 harness 渲染：条件横幅只陈述“本次加载了什么”，不含任何假设方向或预期优劣；A/B 的
**任务正文逐字节相同**，因此 `prompt_hash`（sha256 of 任务正文）两侧一致、可用于配对校验，
而 `rendered_prompt_sha256`（sha256 of 含横幅的完整文件）两侧不同。

保持模型、温度、工具权限、提示顺序与任务输入不变；随机化条件顺序；生成随机时每案至少 3 次重复。

### 单一基线（single baseline）

- A 只能有一条基线：同一模型标识与版本、同一输入文件清单、同一工具权限。不得为不同案例更换基线，也不得把多次基线重采样拼成一个更宽松的“基线”。
  `--validate` 对每个 condition 检查 `(model_id, model_version)` 只有一组，否则报 `baseline_drift` 并列出所有相关 `run_id`。
- 逐案配对比较：同一 `case_id` 的 A 与 B 必须使用同一 `prompt_hash`、同一 `input_files`/`asset_manifest_version`、同一上游 tag/commit。
  `--validate` 逐重复比对 `prompt_hash`、`input_files`、`upstream_vi_tag`、`upstream_vi_commit`，不一致报 `pairing_mismatch` 并给出两侧取值。
- 基线漂移（模型版本、工具集或输入文件变化）时丢弃该案已有结果并重跑，不得跨基线聚合。

### 多图输入与多图输出（multi-image）

- 案例提供多张参考图或要求产出多图（封面组、幻灯片序列、图表组）时，运行前必须固定：图像数量、顺序、每张图的文件清单与哈希。
  案例用 `images` 字段声明槽位（`"none"`、`"single"`、整数或列表）；`--plan` 把它规范成
  `image_set = {count, order[], per_image_hashes[]}`，未固定的图以 `<place:sha256:...>` 占位符标记。
- 同一案例 A/B 两侧的图像数量与顺序必须一致；不一致的结果不得比较（`--validate` 报 `multi_image_mismatch`）。
- 评分口径二选一并事先声明：逐图评分后取均值，或整组整体评分。人工偏好比较必须使用同一组图（可整组呈现），不得只挑其中最好的一张。
- 多图案例的 `raw_output` 必须完整保存整组图与其顺序，缺失任何一张即该次运行作废。
  `--validate` 检查 `raw_output`（列表）或 `raw_output.images` 的项数是否 ≥ `image_set.count`，不足则记入
  `invalidated_runs` 并把目录判为 `FAIL`。

## Required artifacts

每次运行存：

```text
case_id
condition
model_id / model_version
prompt_hash                  # 任务正文 sha256，A/B 相同（配对校验用）
input_files / asset_manifest_version
image_set                    # 多图案例：图像数量、顺序、逐图哈希
upstream_vi_tag / commit
raw_output                   # 多图案例包含整组图与其顺序
structured_score
reviewer_id
review_notes
run_timestamp
```

`--plan` 阶段即可校验的字段（`PLAN_REQUIRED_FIELDS`）：
`run_id`、`case_id`、`condition`、`model_id`、`model_version`、`prompt_hash`、`input_files`、
`asset_manifest_version`、`image_set`、`upstream_vi_tag`、`upstream_vi_commit`。

仅在结果文件里校验的字段（`RUN_RESULT_REQUIRED_FIELDS`）：
`raw_output`、`structured_score`、`reviewer_id`、`review_notes`、`run_timestamp`。

harness 为可核对性额外记录、协议原列表之外的字段：

- `rendered_prompt_sha256`：含条件横幅的完整提示词文件哈希（A/B 不同）。
- `loaded_vi_guide`：该次运行是否加载上游、解析到哪个目录、从哪种候选位置解析到、tag/commit；A 侧为 `null`。
- `repetition`、`family`、`condition_name`、`prompt_file`、`seed`。
- `asset_manifest_version` 的取值口径：A（不加载 VI 资产）固定为 `none`；B 为锁定上游
  `tokens/archebase.tokens.json` + `assets/logo-manifest.json` + `assets/logo-checksums.json` 的内容指纹
  `sha256:<16 位>`。因为两侧本就不同，它**不**参与 A/B 配对校验。

`--validate` 把仍为占位符（`<place:...>`）的字段汇总成 `pending_placeholders` 计数，不视为缺字段；
字段缺失（缺失或空值）才报 `missing_field` 并指明 `run_id` 与字段名。

## Task families

1. **Brand retrieval:** identify official color/font/logo evidence and cite the source.
2. **Artifact review:** find brand, asset, rights, claim and release blockers in a proposed design.
3. **Route selection:** choose strict/guided/creative/off and the correct deck/social/web/image route.
4. **Design brief:** produce a visual direction without inventing brand facts.
5. **Asset handling:** choose an approved logo variant and reject redraw/recolor/regeneration.
6. **Release decision:** return `可发布`、`修复后复审` 或 `阻塞，待确认` with owner/impact.

当前案例文件覆盖家族 1、2、3、5、6；家族 4（design brief）尚无案例。

## Case provenance

[benchmark-cases.json](benchmark-cases.json) 的案例来源必须逐条可见：

- `brand-evidence-01`、`artifact-review-01`、`mode-route-01` 是上游 `evals/evals.json` 中 eval 1–3 的转写（上游该文件同样只有 prompt 与 expectations、没有 runner，本仓库不复制其期望文本）。
- 上游 eval 4（审计 46 页实现：逐页记录可加载、pp.37–46 视为视觉参考而非强制模板、创意模式不得暗示严格 VI 通过）**未纳入本协议**，需要单独补案例后再谈四案覆盖。
- `logo-resolution-01` 与 `release-01` 是本协议新增案例，不是上游 eval 的转写。

所以不存在“上游 eval 提示词作为回归子集”这回事：四个上游 eval 只转写三个。现在
`run_ab_benchmark.py --plan` 会消费这份案例文件，但**只生成运行清单，不执行、不评分**。

## Primary metrics

Score every output blind to condition:

| 指标（协议名） | 评分表列名 | 取值 | 方向 |
|---|---|---|---|
| Brand correctness | `brand_correctness` | 0–5 | higher |
| Evidence grounding | `evidence_grounding` | 0–5 | higher |
| Hard-boundary safety | `hard_boundary_safety` | 0–5 | higher |
| Route/asset correctness | `route_asset_correctness` | 0–5 | higher |
| Actionability | `actionability` | 0–5 | higher |
| False-positive rate | `false_positive_rate` | 0–1 | lower |
| Unsupported-claim rate | `unsupported_claim_rate` | 0–1 | lower |
| Release-blocker recall | `blockers_detected` / `blockers_seeded` | 0–1（由两列算出） | higher |
| Human preference | `human_preference` | `X`/`Y`/`no_meaningful_difference` | 计数 |

- **Brand correctness (0–5):** official evidence, colors, typography, logo and naming.
- **Evidence grounding (0–5):** page/source citations and no unsupported precision.
- **Hard-boundary safety (0–5):** catches logo, rights, claims, public-name, asset and export blockers.
- **Route/asset correctness (0–5):** selects the right playbook and approved asset.
- **Actionability (0–5):** concrete decisions, QA steps, owners and verdict.
- **False-positive rate:** incorrect claimed VI violations or invented rules.
- **Unsupported-claim rate:** factual or brand assertions without evidence.
- **Release-blocker recall:** fraction of seeded blockers detected。`blockers_seeded` 由 `--plan` 从案例的
  `seeded_blockers` 预填，评审者只填 `blockers_detected`（必须 ≤ `blockers_seeded`）。
- **Human preference:** blinded pairwise preference, with “no meaningful difference”.

Primary success criterion: B must improve release-blocker recall and evidence grounding without increasing false positives or unsupported claims.

## Secondary metrics

- Response length and time to verdict.
- Number of unresolved items correctly surfaced.
- Correct use of creative mode: creative latitude must not be mistaken for strict VI approval.
- Reproducibility across repetitions.

（`--score` 当前不计算 secondary metrics；只报告 primary metrics、运行计数与人类偏好计数。）

## Analysis

Report per-case and aggregate means with bootstrap confidence intervals. Do not claim improvement from one prompt or from an unblinded comparison. A result is practically useful only if the confidence interval excludes a negligible effect on the chosen primary metrics.

`--score` 的具体口径：

- 聚合为**案等权**：先算每案每条件的均值，再跨案取均值；`delta = B − A`。
- 区间为**配对 bootstrap**：以案例为重采样单位（不是以运行），10k 次（`--resamples` 可改），
  纯 Python、按 `--seed`（默认取盲映射里的 seed）可复现，报最近秩 95% 区间。
- 可忽略效应阈值（`NEGLIGIBLE_EFFECT`，写入输出）：`release_blocker_recall` 0.10、`evidence_grounding` 0.50、
  `false_positive_rate` 0.02、`unsupported_claim_rate` 0.02。
- 判定行：只有当两个提升指标的 95% CI **下界都大于**各自阈值，且两个不得增加指标的 95% CI
  **上界都小于**各自阈值时，才输出“本样本内 B 更优”，并附“不构成普遍结论、不代表已发布可用”；
  否则输出“证据不足，不得声称 B 提升或未恶化”，并逐项给出原因（含未排除可忽略效应的指标）。
- 每案每条件有效重复 < 3（`repetitions_per_case`，`--plan` 写入盲映射）时，判定强制为“证据不足”并在
  `run_counts.insufficient_repetitions` 逐案列出 A/B 计数；`--score` 只统计填了分数的行，
  未填行计入 `rows_without_scores`。

## 本 harness 不能做什么

- 不产生输出、不调用模型、不联网；它准备运行并分析人工评分，因此**当前不存在任何可引用的分数、均值或置信区间**。
- 不是因果证明：`--score` 只是对已回填数据的算术；判定行不跨越样本，也不替代盲评纪律。
- 不做显著性以外的统计建模；人类偏好只计数、不做检验。
- 不校验上游 VI Guide 内容本身是否正确，也不度量渲染产物与人类视觉质量。
