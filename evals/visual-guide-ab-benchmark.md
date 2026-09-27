# Visual Guide A/B Benchmark

**状态：尚未执行的协议，无实测结果。** 本文件只定义方法，案例在 [benchmark-cases.json](benchmark-cases.json)。

仓库内没有任何 runner 消费本文件或 `benchmark-cases.json`；截至本版本不存在可引用的分数、均值或置信区间。
不得把本文件（或它引用的任何数字）当作“加入 VI 依赖会改善 ArcheBase 视觉设计结果”的证明。
可运行的入口见 [README.md](README.md)。

## Conditions

- **A — baseline（单一基线）：** 同一模型、提示、文件与工具；不加载 `archebase/archebase-vi-guide`，也不加载任何 ArcheBase 专用视觉 Skill。
- **B — VI-guided：** 与 A 完全相同的模型、提示、文件与工具；额外加载锁定的上游 VI Skill：tag `v3.5.4`，commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`。

保持模型、温度、工具权限、提示顺序与任务输入不变；随机化条件顺序；生成随机时每案至少 3 次重复。

### 单一基线（single baseline）

- A 只能有一条基线：同一模型标识与版本、同一输入文件清单、同一工具权限。不得为不同案例更换基线，也不得把多次基线重采样拼成一个更宽松的“基线”。
- 逐案配对比较：同一 `case_id` 的 A 与 B 必须使用同一 `prompt_hash`、同一 `input_files`/`asset_manifest_version`、同一上游 tag/commit。
- 基线漂移（模型版本、工具集或输入文件变化）时丢弃该案已有结果并重跑，不得跨基线聚合。

### 多图输入与多图输出（multi-image）

- 案例提供多张参考图或要求产出多图（封面组、幻灯片序列、图表组）时，运行前必须固定：图像数量、顺序、每张图的文件清单与哈希。
- 同一案例 A/B 两侧的图像数量与顺序必须一致；不一致的结果不得比较。
- 评分口径二选一并事先声明：逐图评分后取均值，或整组整体评分。人工偏好比较必须使用同一组图（可整组呈现），不得只挑其中最好的一张。
- 多图案例的 `raw_output` 必须完整保存整组图与其顺序，缺失任何一张即该次运行作废。

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

所以不存在“上游 eval 提示词作为回归子集”这回事：四个上游 eval 只转写三个，且没有任何东西在执行它们。

## Primary metrics

Score every output blind to condition:

- **Brand correctness (0–5):** official evidence, colors, typography, logo and naming.
- **Evidence grounding (0–5):** page/source citations and no unsupported precision.
- **Hard-boundary safety (0–5):** catches logo, rights, claims, public-name, asset and export blockers.
- **Route/asset correctness (0–5):** selects the right playbook and approved asset.
- **Actionability (0–5):** concrete decisions, QA steps, owners and verdict.
- **False-positive rate:** incorrect claimed VI violations or invented rules.
- **Unsupported-claim rate:** factual or brand assertions without evidence.
- **Release-blocker recall:** fraction of seeded blockers detected.
- **Human preference:** blinded pairwise preference, with “no meaningful difference”.

Primary success criterion: B must improve release-blocker recall and evidence grounding without increasing false positives or unsupported claims.

## Secondary metrics

- Response length and time to verdict.
- Number of unresolved items correctly surfaced.
- Correct use of creative mode: creative latitude must not be mistaken for strict VI approval.
- Reproducibility across repetitions.

## Analysis

Report per-case and aggregate means with bootstrap confidence intervals. Do not claim improvement from one prompt or from an unblinded comparison. A result is practically useful only if the confidence interval excludes a negligible effect on the chosen primary metrics.

## Required artifacts

Each run stores:

```text
case_id
condition
model_id / model_version
prompt_hash
input_files / asset_manifest_version
image_set            # 多图案例：图像数量、顺序、逐图哈希
upstream_vi_tag / commit
raw_output           # 多图案例包含整组图与其顺序
structured_score
reviewer_id
review_notes
run_timestamp
```
