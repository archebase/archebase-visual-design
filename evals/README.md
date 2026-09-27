# evals — 本 Skill 的可运行自检

本目录只有两个可运行脚本，其余文件是案例数据与**尚未执行**的评测协议。

```text
check_brand_facts.py           品牌事实一致性（本 Skill ↔ 上游 VI Guide）
run_visual_design_benchmark.py 检索 + 设计空间回归（读 Design IR store）
visual-design-benchmark.json   上面 runner 的案例数据（唯一被 runner 消费的文件）
benchmark-cases.json           A/B 协议案例（无 runner，见“未执行的协议”）
visual-guide-ab-benchmark.md   A/B 协议正文（无结果、未执行）
```

## 运行

两个脚本都只读、确定性、无网络；路径解析基于脚本自身位置，因此从任意工作目录调用都可以（下列命令在 Skill 根目录执行）：

```bash
python3 evals/check_brand_facts.py              # 退出码 0 一致 / 1 有分歧 / 2 上游不可达
python3 evals/run_visual_design_benchmark.py    # 默认退出码 0（报告模式）；--strict 在状态为 FAIL 时退出 1
```

路径解析顺序（都不含机器绝对路径默认值）：

- 上游 VI Guide：`ARCHEBASE_VI_GUIDE` → Skill 目录/上级目录/上上级目录 → `$HOME` → `$HOME/Books` 下的 `archebase-vi-guide`；
- Design IR store：`ARCHEBASE_DESIGN_IR` → 同样的候选位置下的 `archebase-design-ir`。

解析不到时报 `待确认` 并以退出码 2 停止——不得用记忆或臆造数据替代。可用 `--upstream` / `--skill` / `--store` / `--cases` 显式覆盖。

## check_brand_facts.py

把本 Skill 重述的品牌事实与上游 `tokens/archebase.tokens.json`、`assets/guide-evidence.json`、`references/visual-grammar.md`、`references/asset-governance.md` 逐项对账，输出逐项表格（判定 / 项 / 上游 / 本 Skill / 位置）。任一 FAIL 即退出码 1。

能检测：

- **不存在于上游的色值**：`#RRGGBB` 若既不是上游五个 token（上游 `tokens/archebase.tokens.json`；`references/visual-grammar.md:5-9`），也没有在同一行声明渠道/非品牌来源，判 FAIL；在唯一品牌重述处 `references/brand-system.md` 以品牌色板口径出现时，即使标注来源也判 FAIL。
- **上游有、本 Skill 缺或错**：五色 token 与色值的配对、色板“只有五个 token 且无白色 token”的声明、色彩比例（`AB_BLUE_1` 50%、`AB_BLUE_2` 25%、`AB_BLUE_3` 10%、`AB_BLUE_4` 5%，标注合计 90%，剩余 10% 未指派——上游 `assets/guide-evidence.json` id `color.ratio`，Guide p.28）、中性档位（`#1E2124` 背景 100%/5%、文字 100%/70%/50%——上游 id `neutral.background`，Guide pp.30-31；id `neutral.text`，Guide p.32）、字体族与展示字重（上游 `tokens/archebase.tokens.json` 的 `type`；id `typography.specimens`，Guide pp.6/10/14/26）、批准公开名称（上游 `references/asset-governance.md:126`；id `naming.examples`，Guide pp.33-36）。
- **比例重分配**：任何文件里 `AB_BLUE_n` 附近的百分数与上游不符。
- **引用可追溯**：`id`/`evidence` 引用的 evidence id 必须存在于上游；引用行的页码必须落在该证据的 Guide 页码内。
- **上游 待确认 项被臆造**：Logo 安全区/最小尺寸的数值断言（未标 `待确认`）——上游 `tokens/archebase.tokens.json` 的 `unconfirmed`（`logo_clear_space`、`logo_minimum_size`）与 `references/logo-asset-resolver.md:45`。
- **公开名称写法**：未批准写法（大小写错误、全大写独立出现、加空格/连字符/下划线、`AI` 后缀等）判 FAIL；否定语句里列举的示例不算声明，URL、路径、环境变量（`ARCHEBASE_DESIGN_IR` 等）与技术标识不误判。

不能检测（已确认的边界，不要据此声称更宽的一致性）：

- 角色语义、组件级配额、中性合成公式等上游本身就是 `待确认` 的内容，本脚本只能查“是否被编造成事实”，不能裁定其正确值。
- 色值以外的视觉质量、Logo 渲染、栅格化工具链、字体授权与许可判定。
- 文本语义改写：把事实换成另一种等价表述可以躲过存在性检查；百分比配对用的是近距离启发式，不是语义解析。
- WARN 行（如渠道 CSS 的浅色 tint `#F3F5FF`、表头反白 `#FFFFFF` 等，来源 `assets/archebase-wechat-safe.css`）只表示“非品牌 token，已声明来源”，不阻断；它们不是品牌色板的一部分（核心品牌色仍只有五个：上游 `tokens/archebase.tokens.json`）。
- 第三方素材授权不在本目录度量范围；本 Skill 不维护许可台账，也不给出任何清权结论。

## run_visual_design_benchmark.py

对 Design IR store 跑两组检查，输出 JSON。

**检索组**：逐案调用 `query.py`，两次调用分别取 `--limit k`（计分窗口）与 `--limit pool_limit`（完整排序）。每案报告 `k`、`pool`、`discriminating`、`first_rank`、`reciprocal_rank`、`expected_ranks_in_pool`、断言明细。

- 断言只有两种：`expect_within_k`（期望记录至少一项落在 top-k）与 `must_not_be_first`（反例：首位不得是某个错误规则）。
- 可证伪性规则写进输出：含 `expect_within_k` 的案例要求 `pool > k`；纯反例要求 `pool >= 2`。不满足的案例不计分，并计入 `integrity_failures`（状态 FAIL）。
- `status` 三值：`PASS`（无失败）、`PASS_WITH_KNOWN_FAILURES`（只剩 `known_failing` 案例的已知失败）、`FAIL`（出现 regression / 不可证伪案例 / 设计空间不变量失败）；`--strict` 只在 `FAIL` 时退出码 1。
- `k_default` 为 5，逐案可覆盖；`--k N` 覆盖全部案例。历史版本硬编码 `--limit 5` 且用 `--kind case` 把池压到 2 条，Hit@5 恒为 1；现在 `kind` 过滤若存在也会连同池大小一起报告。
- 指标：`hit_at_k`、`mrr_at_k`（只统计可证伪正例）、`decoy_pass_rate`。`known_failing` 标记的案例是当前已知缺陷：它们失败属预期，从 pass 翻成 fail 才计入 `regressions`。

**设计空间组**：逐案调用 `jspace.py`，断言与 `jspace.py` 语义一致的可证伪不变量，而不是“首位等于 axes.json 锚点”：

- 返回向量的轴集合必须等于 `axes.json` 的全部六个轴（对完整池逐条检查），坐标必须与 `axes.json` 一致；
- 报告距离必须与复算距离一致（单目标绝对差、多目标欧氏距离，容差 5e-5 对应 4 位小数输出），且窗口内距离不递减；
- `count == min(k, pool)`，`pool >= 2`；
- `pairwise`：按 `axes.json` 的锚点极性声明成对顺序（如 `structural_stability` 正端锚点必须排在负端锚点之前）。

## 当前实测（2026-09-27，12 条记录的语料）

```bash
python3 evals/run_visual_design_benchmark.py
```

| 案例 | 渠道 | k | pool | 期望失败模式 / 结果 |
|---|---|---|---|---|
| retrieval-01…10 | wechat_cover/report/slides/web/poster | 5 | 7–9 | 池 > k，可证伪；当前首位命中 7 例、`rule:grid:modular` 与 `rule:color:perception`/`case:fluid:signal` 为第 2 |
| decoy-02-image | slides | 5 | 10 | 当前 `rule:accessibility:semantic` 抢先，已知缺陷 |
| decoy-03-logo | web | 5 | 4 | 当前 `anti:generic:cyberpunk` 抢先，已知缺陷（纯反例，池 ≥ 2 即可证伪） |
| jspace-01…04 | — | 5 | 11 | 不变量 + 锚点极性，全部通过；jspace-03 的旧“首位 = case:stable:foundation”断言仅在 `--kind case`（池 = 2）下成立，已删除 |

`hit_at_k` 在当前语料上是饱和的（正例 1.0），可证伪信号来自 `first_rank`/`mrr_at_k`（0.7708）、三个反例（`decoy_pass_rate` 0.0）与 `integrity_failures`。数值随语料与排序实现变化，以每次运行的 JSON 输出为准。

不能检测：

- 不是 with/without 因果对比，也不证明任何效果提升；它只说明当前排序在给定案例上是否失败。
- 排序由 `query.py` 的字符/词项重叠 + bm25 决定，不是 embedding 语义检索；查询接近记录原文，命中率高不证明语义检索能力。
- 语料只有 12 条记录，其中 case 记录 `status=proposed`、`anti_pattern` 1 条；池小是语料的性质，不是本基准可以掩盖的。
- 不度量人类视觉质量、渲染产物、上游 VI Guide 正确性。

## 未执行的协议

[visual-guide-ab-benchmark.md](visual-guide-ab-benchmark.md) 与 [benchmark-cases.json](benchmark-cases.json) 是 A/B 评测协议与案例，**没有任何 runner 消费它们，也没有任何实测结果**。要评测“加入本 Skill 是否改善结果”，先按该文件的单一基线与多图要求实现运行与盲评，再报告结果；不得把协议本身当作效果证明。
