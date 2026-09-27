# 智域基石品牌系统

## 品牌核心

ArcheBase / 智域基石是 Physical AI 的数据基础设施：把复杂物理世界转成高保真、可组织、可验证、可供智能理解和行动的数据。视觉表达应传递基础性、工程秩序、可信度、精确度和从物理到智能的连续关系。

## 正式色彩角色

品牌色板是上游定义的五个 token，其中没有白色 token（上游 `tokens/archebase.tokens.json`；`references/visual-grammar.md:5-8`）。色值只在本文件声明，其他文件引用本文件。

| token | 色值 | 角色与推荐用途 | 限制 |
|---|---|---|---|
| `AB_BLUE_1` | `#0032FF` | 最强品牌识别与主结构：主标题结构、关键强调、核心数据、链接 | 不大面积淹没长篇阅读内容 |
| `AB_BLUE_2` | `#7172FA` | 支撑层级：分隔、边界、次级图形层 | 不默认用于白底小字 |
| `AB_BLUE_3` | `#619AFD` | 次级数据层：结构线、空间层次、次级数据关系 | 不默认用于白底小字 |
| `AB_BLUE_4` | `#46CFFF` | 有意义的强调与数据流：节点、边线、深底高亮 | 不用于白底小字号正文 |
| `AB_CHARCOAL` | `#1E2124` | 技术深色场与中性文字：正文、深色背景、中性色主体 | 深底时保证反白文字对比度 |

（色值与角色：上游 `tokens/archebase.tokens.json`；`references/visual-grammar.md:5-8`。）

### 已确认证据：色彩比例

- Guide p.28 显示四色块比例：`AB_BLUE_1` 50%、`AB_BLUE_2` 25%、`AB_BLUE_3` 10%、`AB_BLUE_4` 5%，标注合计 90%。
- 剩余 10% 在 Guide 中未指派，不得自行分配给某个颜色或组件。
- 该比例是显式视觉几何证据，不是自动的按组件配额。

（上游 `assets/guide-evidence.json` id `color.ratio`；Guide p.28；`references/visual-grammar.md:19`。）

### 已确认证据：中性色阶

- 背景档位：`#1E2124` 的 100% 与 5%，对应深色与浅色中性背景示例（Guide pp.30-31；上游 `assets/guide-evidence.json` id `neutral.background`）。
- 文字档位：`#1E2124` 的 100%、70%、50%（Guide p.32；上游 `assets/guide-evidence.json` id `neutral.text`）。

### 待确认

- `color.ratio` 的语义角色命名与按组件分配。
- 中性色的合成公式、CSS 实现与组件角色映射。

（上游 `tokens/archebase.tokens.json` 的 `unconfirmed`；不要为以上项目臆造数值。）

### 应用默认（非品牌 token）

白/浅色阅读表面是本 Skill 为阅读稳定性设定的应用默认，不代表品牌色板含白色：它不属于上方 token 表，也不得进入任何“精确色值”验收门。上游白色只作为 Logo 形态出现，不构成颜色 token（上游 `assets/guide-evidence.json` id `logo.forms`，Guide pp.1-5）。
批准 Logo 资产内部的渐变 stops、字标黑色与 counterform 白色属于资产几何/渲染细节，不进入品牌 token 精确色值门，也不构成新增品牌色；只要资产文件未被改写并通过上游 Logo 完整性校验，即按该资产规则处理。

不依赖颜色单独编码关键含义。

## 字体

- 中文：`思源黑体`，Guide 显示字重 粗黑 / 黑 / 细黑。
- 拉丁（展示、数字、短标签）：`Poppins` ExtraBold / SemiBold / Regular。
- 待确认：精确生产字体文件与授权，以及 `Source Han Sans SC` 这一命名是否适用。

（上游 `tokens/archebase.tokens.json` 的 `type`；`assets/guide-evidence.json` id `typography.specimens`，Guide pp.6/10/14/26。）
渲染与打样：上游 VI 不随附字体文件；可使用另行取得许可的同设计字体（中文 `Noto Sans CJK SC`，与 `思源黑体` 同设计；拉丁 `Poppins`）。渲染前用 `fc-match '<family>'` 或输出文件的 `/BaseFont` 表确认**实际解析到的 family**，并把实际 family、字重、文件与授权记入 [visual-spec.md](../templates/visual-spec.md)；解析到替代字体时交付状态记 `待确认`，不得声明已按 VI 字体渲染。保留 live text 与可复现的字体配置。

渠道字体回退栈（`Noto Sans CJK SC / PingFang SC / Microsoft YaHei`）是渠道实现细节，归 [channel-wechat.md](channel-wechat.md)，不写进本品牌系统文件。

不随意增加装饰字体；中文长正文以阅读稳定性为先。

## 核心视觉母题

以下六个母题是本 Skill 为稳定执行而做的自定综合，属于本技能的操作方法，不是 VI 原文条款（对上游仓库全量检索无命中）。使用时按“本 Skill 自定的母题（非 VI 原文）”标注。

### Foundation Block
稳定方形、矩形、模块和基准面，表达底层基础设施。避免无支撑漂浮和随机软形。

### Coordinate Field
网格、刻度、边界框和对齐轴用于组织内容、测量与定位；不能只是科技背景纹理。

### Data Spine
主品牌蓝强轴线连接物理现实、数据处理和智能行动；必须有结构或叙事作用。

### Signal Node
青色节点、短线、标注表达信号与状态；稀疏使用，配合标签或形状。

### Controlled Flow
从分散到汇聚、复杂到有序的方向关系；流线应有起点、终点或明确关系。

### Physical Field
通过密度、间距、线宽、透明度、裁切和层次表达真实世界规模，而非廉价阴影或玻璃拟态。

## Logo

不得变形、重绘、重新配色或添加效果。

硬约束（违反即阻断发布）：

- 当前工作中公开名称必须是 `ArcheBase`；小写 `archebase` 仅作技术标识；不得使用未经批准的组合锁定或做域名命名变更（上游 `references/asset-governance.md:126`；`assets/guide-evidence.json` id `naming.examples`，Guide pp.33-36）。
- 使用与已批准资产不匹配的渲染器栅格化的 Logo、以及未批准的 Logo 变体同样阻断（上游 `references/asset-governance.md:123,125`）。

已确认且可执行的解析规则（细节以上游为准）：

- 只解析当前世代 `智域基石 Logo V2`；不得解析到被取代的世代：V1 命名（`白色_*` / `蓝色_*`）、2026-07-29 原始导出、V2 之前草稿（上游 `references/logo-asset-resolver.md:26-34`）。
- 圆形展示面或任何可能被圆形裁切的场景必须使用 `方圆通用` 变体（如 `蓝色纯色_无文字_方圆通用_图形标.svg`）；不得缩放或遮罩裁剪 `方形` 变体（上游 `references/logo-asset-resolver.md:42`）。
- 渐变标必须用 `rsvg-convert` 或浏览器引擎栅格化；禁止 ImageMagick 内置 SVG 渲染器；可直接使用随附 PNG（上游 `references/logo-asset-resolver.md:47-53`）。

待确认：Logo 安全区、最小尺寸、组合锁定参数（上游 `tokens/archebase.tokens.json` 的 `unconfirmed`）。缺少正式参数时使用 VI 原文件中的现成资产。

## 禁止项

- 泛化“AI 蓝紫渐变”。
- 发光大脑、随机电路、二进制雨、机器人手指触屏。
- 无来源仪表盘与装饰性数据图。
- 无语义粒子、光晕和赛博城市。
- 近似但不一致的蓝色和字体。
- 用“极简”掩盖信息缺失或空洞。
