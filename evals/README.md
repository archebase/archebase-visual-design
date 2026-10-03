# evals — 本 Skill 的可运行自检

本目录有四个可运行脚本；其余文件是案例数据与评测协议（A/B 有 harness，但尚未填入实测结果）。

```text
check_brand_facts.py           品牌事实一致性（本 Skill ↔ 上游 VI Guide）
run_visual_design_benchmark.py 检索 + 设计空间回归（读 Design IR store）
check_routing.py               索引层路由可达性与 vi-guide 边界（读 route_cases.json）
check_spatial_spec.py          参考图保真与佩戴几何规格校验（读 spatial-spec-cases.json 自检）
spatial-spec-cases.json        spatial-fidelity 规格的正例与反例（被 check_spatial_spec.py --self-test 消费）
route_cases.json               路由用例集（正例 / 边界 / 无关 / 已知难例）
run_ab_benchmark.py            A/B 评测 harness（--plan 出运行清单与盲评表，--score 算指标与 CI）
visual-design-benchmark.json   检索回归的案例数据（被 run_visual_design_benchmark.py 消费）
benchmark-cases.json           A/B 协议案例（被 run_ab_benchmark.py 消费）
visual-guide-ab-benchmark.md   A/B 协议正文与 harness 用法
```

## 运行

四个脚本都只读、确定性、无网络；路径解析基于脚本自身位置，因此从任意工作目录调用都可以（下列命令在 Skill 根目录执行）：

```bash
python3 evals/check_brand_facts.py              # 退出码 0 一致 / 1 有分歧 / 2 上游不可达或身份不可核对
python3 evals/run_visual_design_benchmark.py    # 默认退出码 0（报告模式）；--strict 在状态为 FAIL 时退出 1
python3 evals/check_routing.py                  # 退出码 0 无 FAIL / 1 存在 FAIL / 2 依赖不可解析
python3 evals/check_spatial_spec.py --spec <spec.json>   # 退出码 0 无 FAIL / 1 存在 FAIL / 2 规格不可解析
python3 evals/check_spatial_spec.py --self-test          # 正例放行、反例全部拦下才退出 0
python3 evals/run_ab_benchmark.py --plan --out /tmp/ab   # A/B：出运行清单、提示词与盲评表
```

路径解析顺序（都不含机器绝对路径默认值）：

- 上游 VI Guide：`ARCHEBASE_VI_GUIDE` → Skill 目录/上级目录/上上级目录 → `$HOME` → `$HOME/Books` 下的 `archebase-vi-guide`；
- Design IR store：`ARCHEBASE_DESIGN_IR` → `archebase-design-workspace/ir`（当前布局）→ `archebase-design-ir`（兼容旧布局）→ 按 pin clone `https://github.com/archebase/archebase-design-workspace`（**内部仓库，需访问权限**）；身份（commit）见 `skill-dependencies.json` 的 `design-ir-store`；索引是构建产物，先跑 `ir/build_index.py`。无权限或不可达时本脚本按 `待确认` 退出 2——品牌事实检查与路由检查不依赖 store，可照常运行。

**上游身份必须核对**：本地 clone 只是缓存。候选目录必须完整（`SKILL.md`、`tokens/archebase.tokens.json`、`assets/guide-evidence.json`、`references/visual-grammar.md`、`references/asset-governance.md`），并且 `git rev-parse HEAD` 等于 `skill-dependencies.json` 里 `archebase-vi-guide` 的 pin；解析器会优先选身份与 pin 一致的候选，避免同机上的旧副本被当成权威。身份不一致或不可核对时 `check_brand_facts.py` 按 `待确认` 退出 2（`--allow-unpinned` 可继续做参考比较，结果只能视为待确认）；若上游副本连批准公开名称都读不出来，同样按上游不可用退出 2，而不是判本 Skill 有分歧。

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
- 第三方素材授权不在本目录度量范围；本 Skill 不维护许可台账，也不给出任何清权结论；对外发布前由发布方确认授权。

## check_routing.py

在**加载之前**的索引层检查本 Skill 是否可能被选中，以及与上游 `archebase-vi-guide` 的边界是否可见。Hermes loader 只把描述的前 60 字符（`desc[:57] + '...'`）放进索引，超出部分对路由等于不存在（`~/.hermes/hermes-agent/agent/skill_utils.py` 的 `SKILL_PROMPT_DESC_LIMIT`）。

判定规则：

- `expect=visual-design` 的用例必须命中索引窗口内的 key term，否则该请求在索引层无法被本 Skill 接住 → FAIL。
- `expect=vi-guide` / `neither` 的用例若命中本 Skill 的 key term → WARN（字面层不可区分，需模型按 `SKILL.md` 分工边界裁决）；标 `ambiguity: true` 的已知难例只报 WARN。
- 结构性检查：`boundary_terms` 必须存在于 `SKILL.md` 正文；落在窗口外的 key term 会单独列出。

`--limit N` 模拟更严格的 loader；`--print-window` 只打印窗口并显示上游身份（pin tag/commit 与解析来源）。脚本只做字面判定，不替代模型裁决。反证：`--limit 30` 时正例立即 FAIL（rc=1），说明检查不是永远通过。

## L1 实测（2026-09-27）

字面检查（`check_routing.py`，17 个用例）：FAIL 0，WARN 2（两个 `ambiguity` 已知难例）。

语义探测（判官代理，**不是**线上 router）：只用两个 Skill **截断后的窗口文字**作为可见信息，让判官模型为 7 条正例 / 5 条边界 / 3 条无关 / 2 条难例各选一个 Skill，重复 4 次：

| 指标 | 结果 |
|---|---|
| 准确率 | 0.94（16/17），4 次运行一致 |
| 逐用例稳定 | 17/17 不翻转 |
| 正例（海报/头图/社媒/信息图/报告封面/评审/设计方法） | 7/7 选中本 Skill |
| 边界用例（色值/Logo 变体/发布门禁/Guide 页码/字体权威） | 5/5 落到 `vi-guide` |
| 无关用例 | 3/3 `neither` |
| 唯一错例 | `amb-02`「公众号头图的官方尺寸规范在哪」→ 本 Skill（已声明的已知难例：含“头图”但诉求是官方规格） |

方法与边界：判官代理 ≠ 线上 router（`[UNVERIFIED]`：未对真实 router 执行）。改写描述前的同法探测中，“公众号头图”类请求 3/3 落到 `vi-guide`；改写后同一方法 4/4 落到本 Skill，因此这是可复现的改善，但仍不是线上路由结论。`amb-02` 的兜底：即使加载本 Skill，`SKILL.md` 的渠道路由也会把尺寸规范指向 `references/channel-wechat.md` 与渠道 CSS 仓库。

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

## 当前实测（2026-09-27，11 条记录的语料）

```bash
python3 evals/run_visual_design_benchmark.py
```

| 案例 | 渠道 | k | pool | 期望失败模式 / 结果 |
|---|---|---|---|---|
| retrieval-01…10 | wechat_cover/report/slides/web/poster | 5 | 7–9 | 池 > k，可证伪；首位命中 7 例，`retrieval-02`/`08`/`10` 的期望记录为第 2 |
| decoy-02-image | slides | 5 | 10 | 当前 `rule:accessibility:semantic` 抢先，已知缺陷 |
| decoy-03-logo | web | 5 | 4 | 当前 `anti:generic:cyberpunk` 抢先，已知缺陷（纯反例，池 ≥ 2 即可证伪） |
| jspace-01…04 | — | 5 | 11 | 不变量 + 锚点极性，全部通过 |

`hit_at_k` 在当前语料上是饱和的（正例 1.0），可证伪信号来自 `first_rank`/`mrr_at_k`（0.8182）、两个反例（`decoy_pass_rate` 0.0）与 `integrity_failures`。数值随语料与排序实现变化，以每次运行的 JSON 输出为准。

不能检测：

- 不是 with/without 因果对比，也不证明任何效果提升；它只说明当前排序在给定案例上是否失败。
- 排序由 `query.py` 的字符/词项重叠 + bm25 决定，不是 embedding 语义检索；查询接近记录原文，命中率高不证明语义检索能力。
- 语料只有 11 条记录，其中 case 记录 `status=proposed`、`anti_pattern` 1 条；池小是语料的性质，不是本基准可以掩盖的。
- 不度量人类视觉质量、渲染产物、上游 VI Guide 正确性。

## check_spatial_spec.py

校验 [templates/spatial-fidelity-spec.json](../templates/spatial-fidelity-spec.json) 规格（参考图保真与佩戴几何；方法见 [references/spatial-fidelity.md](../references/spatial-fidelity.md)）。只读、确定性、无网络、不依赖第三方包：`--spec <spec.json>` 逐项输出 PASS/FAIL/WARN/SKIP，任一 FAIL 退出 1；`--self-test` 跑 [spatial-spec-cases.json](spatial-spec-cases.json) 的正例与反例，反例未被拦下即退出 1。

能检测（每条都有对应反例证明可失败）：

- 必填字段齐全；`subject.kind` 合法。
- `device_on_person` 必须声明 `subject.pose`（姿态优先）与 `posture_geometry_check.violates_if`（什么姿态使不变式失效），且至少有一个器件角色参考。
- 参考角色取值合法、id 唯一；每个角色都登记了不可变特征与不得复现项。
- 不变式 id 唯一，且每条都同时有 statement / observation / prompt_clause 和合法状态。
- 不可证伪表述（“更真实/更自然/更高级”等）不能充当判据。
- 为展示器件而要求“确保镜头/相机可见、露出、朝前”的措辞判 FAIL——应改姿态或接受遮挡。
- 规格中出现本机绝对路径判 FAIL（规格必须能跨机器复现）。
- 交付门：存在 `accepted` 候选时，不得仍有 `fail` 状态的不变式或该候选的失败不变式。
- 未批准的品牌名称写法。

`known_limits` 为空只报 WARN：任何真实器件复刻都有无法消除的偏差，应如实登记而不是声称完美。

不能检测（不要据此声称更宽的正确性）：器件是否真的与参考图一致、不变式判据在物理上是否正确、所选姿态是否真的能让全部不变式同时成立。这些只能靠按 `observation` 指定的位置裁切复核与人工评审；本脚本只保证规格可复核、可追溯、不自相矛盾。

退出码：0 = 无 FAIL；1 = 存在 FAIL 或自检不符预期；2 = 规格不可解析。

## A/B 协议与 harness

[visual-guide-ab-benchmark.md](visual-guide-ab-benchmark.md) 与 [benchmark-cases.json](benchmark-cases.json) 是 A/B 评测协议与案例。`run_ab_benchmark.py` 现在能按协议生成运行清单、渲染提示词、随机化盲评表（`--plan`）、校验结果完整性（`--validate`）并统计指标与 bootstrap 置信区间（`--score`），但**尚未有人填入实测结果**，因此本仓库目前没有任何可引用的效果分数。不得把协议或 harness 本身当作效果证明。
